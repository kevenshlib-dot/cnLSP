# 用开放数据拼出一个中文 Annif

**能做到，但要换一条路走。** 网上没有任何开放许可、可下载、带 606/690 字段的 CNMARC 数据集。中图法、中分表（汉语主题词表）、CMeSH、STKOS 也都没有开放许可。所以"复刻国图编目习惯"这条路在教学和开放演示阶段走不通。不过，词表和训练数据两头各有合法替代：
- 词表：台湾国家图书馆的《中文主題詞表》CSV 有 17,125 个首选主题词，带中文图书分类法类号，采用台湾政府资料开放授权条款 v1.0，与 CC BY 4.0 兼容。FAO 的 AGROVOC 有 41,855 个中文标签概念（CC BY 4.0）。OCLC FAST、YSO、STW 等国外词表许可宽松，可以借 Wikidata 的 CC0 中文标签加大模型补齐翻译。
- 训练数据：CSL 中文科技文献数据集有 396,209 篇论文，带标题、摘要、作者关键词和 13 门类 / 67 学科两级标签，足够训练 Annif 的 Omikuji、fastText 等后端。Harvard 图书馆 CC0 书目数据（约 1,330 万条，估算值）可以提供中文题名配 LCSH/LCC 的记录，但其中中文记录有多少还没测出来。

技术上还有一道必须先过的关：Annif 没有中文分析器，默认配置会把整段中文当成一个词。所以第一件事是给 Annif 加一个 jieba 分析器。

我推荐的组合是：**"台湾主题词表简体化 + CSL 论文（关键词对齐到主题词）+ 自定义 jieba 分析器 + TF-IDF/MLLM/Omikuji 集成"**作为主演示，**CSL 学科分类**作为五分钟入门，**AGROVOC** 作为现成的专业领域示例。这套组合全部用开放数据，许可清楚，一两周可以搭起来。要做成生产工具，最终还得通过授权拿到大陆的词表和 CNMARC 数据。

## Annif 默认分析器会把整段中文当成一个词

Annif（NatLibFi/Annif，Apache-2.0）的最新版本是 v1.4.2，2026-08-14 发布，支持 Python 3.10–3.13（[NatLibFi/Annif](https://github.com/NatLibFi/Annif)）。它没有中文分析器。本次对话中实测了三个问题：
- 默认的 NLTK 分词器把一整段中文当作一个 token 返回。
- 遇到"。"不会断句。
- 默认 `token_min_length=3` 会丢掉绝大多数双字词，而双字词恰恰是中文主题词的主体。台湾主题词表的标目平均只有 3.7 个字（见下文实测）。

也就是说，不改分析器，TF-IDF、fastText、Omikuji 这些关联型后端拿到的都是整句"巨词"，MLLM 这类词汇匹配型后端则几乎匹配不到任何标签。

可行的修法有三种：
- `spacy(zh_core_web_sm, token_min_length=1)`：本次未测试。
- 先用 jieba 把语料和词表预先分词、空格连接，再配 `simple(token_min_length=1)`：不改源码，但每份输入都要预处理。
- 在克隆的 Annif 里新增一个约 30 行的 jieba 分析器：**推荐这一种**。它让命令行、REST API 和 Web 界面都能直接处理原始中文，也方便以后换成 pkuseg 或 HanLP。

这是整个项目里唯一需要动 Annif 源码的地方，其余工作都是数据准备。

## 大陆体系闭源：没有开放 CNMARC，中图法和中分表都没有开放许可

研究者检索了 GitHub、HuggingFace、Kaggle、数据门户和近年论文，**没有找到任何开放许可的 CNMARC 606/690 数据集**。离得最近的是一篇 DCMI-2026 论文：作者用了 **32,837 条 CNMARC 记录**加上中图法第五版的 53,326 个类号–类名对，构建了 36,786 条训练实例。但论文没有说明数据来源馆，也没有给数据链接或许可，CC BY 4.0 只适用于论文本身（[DCMI 论文](https://dcpapers.dublincore.org/article/952629699)）。北京大学 2023 年的一项研究也提到缺少带中图法标签的图书，只能借 LCC→CLC 映射来补训练数据（[北大学报](https://xbna.pku.edu.cn/CN/Y2023/V59/I1/11)）。

通过 Z39.50 或联合编目中心自己采集，许可同样不允许对外共享。CALIS 协议规定数据"不得用于任何商业行为或转交第三方使用"，大学成员馆可以无限下载，但只能用来建本馆书目库（[CALIS 协议](https://lawinsider.com/zh/contracts/amXDAsuA25k)；[协议 PDF](https://calis.sdu.edu.cn/lhbm/3.pdf)）。国家图书馆联合编目中心的下载价格和许可条款，研究者没有找到公开的官方页面。

小规模抓几十到几百条做格式教学，风险不高；批量采集再公开发布就踩线了。这是推断，不是法律意见。

词表这边情况相同：
- **中图法、中分表**：clc.nlc.cn 提供需要账号登录的 Web 版和征订服务，没有任何开放许可声明（[clc.nlc.cn](http://clc.nlc.cn/)）。
- **CMeSH**：是机构订阅资源（[PolyU 图书馆](https://www.lib.polyu.edu.hk/node/25167)）。
- **GB/T 13745 等推荐性国标**：按国家版权局权司〔1999〕50号等答复，属于著作权保护范围，能免费在线阅读不等于可以再分发（[elawcn 汇编](https://www.elawcn.com/rule/2022/1219/1208.html)）。
- **GitHub 上的中图法抓取版**：如 acdzh/Chinese-Library-Classification、tinycourses/library_classification，都没有许可证，内容来自受版权保护的原表（[acdzh](https://github.com/acdzh/Chinese-Library-Classification)；[tinycourses](https://github.com/tinycourses/library_classification)），最多只能用于不公开的课堂实验。

研究者也**没找到任何中文分类法或主题词表的 SKOS 转换版**，所以任何一套中文词表进 Annif 都需要自己转换。

## 现成带中文标签的开放词表只有五个，通用领域的只有台湾 1.7 万条主题词

下表汇总了研究者 2026-10-13 对各发布方官方端点的实时查询结果。

| 词表 | 许可（能否用于生产） | 概念总数 | 有中文标签的概念 | 字形 | 适合场景 |
|---|---|---|---|---|---|
| 台湾《中文主題詞表》（中文主題編目規範） | 政府资料开放授权 v1.0，与 CC BY 4.0 兼容（可） | 17,125 首选词 + 2,200 入口词 | 全部 | 繁体 | 通用图书主题标引 |
| AGROVOC | CC BY 4.0（可） | 41,999 | 41,855 | 简体 | 农业、食品、环境 |
| GEMET 4.2.3 | CC BY 4.0（可） | 约 5,573 | 约 5,208（zh-CN，带定义） | 简体 | 环境领域小型练习 |
| Getty AAT | ODC-By 1.0（可，本次未复核） | 57,572 | 27,472 | 繁体 | 艺术、博物馆 |
| Wikidata | CC0（可） | 数百万 | 例如 LCSH 关联条目中约 4.1 万个 | 简繁混杂 | 标签来源，层级弱 |

来源：[AGROVOC SPARQL](https://agrovoc.fao.org/sparql)、[FAO 许可页](https://www.fao.org/agrovoc/index.php/maintenance)、[GEMET 导出页](https://www.eionet.europa.eu/gemet/en/exports/rdf/latest)、[data.gov.tw 27190](https://data.gov.tw/en/datasets/27190)、[Getty SPARQL](https://vocab.getty.edu/sparql)、[Wikidata Query Service](https://query.wikidata.org/sparql)。

另外三个常被提到的词表**完全没有中文**：UNESCO Thesaurus（4,500 个概念）、EuroVoc（7,515 个），以及 MeSH（[UNESCO SPARQL](https://vocabularies.unesco.org/sparql)；[EU Publications Office SPARQL](https://publications.europa.eu/webapi/rdf/sparql)）。

**台湾主题词表是唯一开放、图书馆级、覆盖通用领域的中文主题词表**。研究者下载并解析了 CSV，结果如下：
- 文件 1,472,821 字节，UTF-8 带 BOM，**19,325 行**，主题词全部唯一。
- **95.2% 的行带中文图书分类法类号**（第八版和/或 2007 版）。
- 有"用 / 不用"等同关系，以及 1,596 对"參見"相关关系。
- 标目平均 3.7 个字，几乎没有复分串，非常适合 Annif 这种扁平概念模型。

它有三个硬伤：
- **没有上下位（BT/NT）字段**，层级无法重建。
- **没有逐条 URI**，网址列每行都是同一个 catsmart.ncl.edu.tw。
- 类号按大类分布偏向 3（自然科学）、4（应用科学）、5（社会科学），史地和文学偏薄。

另外，数据集元数据标注的覆盖期是 2000–2016，最后修改日期却是 2026-09-23，无法判断 2016 年之后有没有新增标目（[NCL CSV](https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137)；[data.gov.tw API](https://data.gov.tw/api/v2/rest/dataset/27190)）。

给大陆用户用，需要用 OpenCC 把繁体转成简体。但字形转换解决不了用词差异，比如"部落格"对"博客"，需要人工补一批简体别名。

AGROVOC 是"开箱即用"程度最高的选择：中文标签覆盖 99.7%，有 42,446 条上下位关系，每月更新，Annif 生态里本来就在用。缺点是领域局限在农业。

技术细节上有一个坑：AGROVOC 的语言标签是 `zh`，GEMET 是 `zh-CN`。`annif load-vocab --language` 只接受一个语言代码，加载前要统一改写。

## 翻译国外词表可行，FAST、YSO、STW 起点最好，LCSH 的预组配是陷阱

如果想要更接近图书馆主题标引、规模也更大的词表，翻译国外词表是可行的。关键是选一个许可宽松、结构扁平、已有部分中文标签的起点。研究者用 QLever 的 Wikidata 镜像统计了各词表经 Wikidata 关联得到的中文标签数：

| 词表 | 许可 | 规模 | Wikidata 已有中文标签 | 评价 |
|---|---|---|---|---|
| OCLC FAST | ODC-By（可用于生产，需署名） | 全量 NT 压缩包 266 MB，主题分面 46 MB | 非人名条目 20,801 | 分面、后组配，最适合 Annif；可由 LCSH 机械转换 |
| LCSH | 通常视为美国政府作品（公有领域，未取得明确声明） | 2018 年 342,947 条 | 40,793（其中 zh-hans 仅 20,261） | 预组配复分串会让标签空间爆炸 |
| YSO | CC BY 4.0 | 33,237 | 20,516 | Annif 的"主场"词表，但没有中文书用它标引 |
| STW 经济学叙词表 | CC BY 4.0 | 6,000+ 叙词 | 4,064 | 小而干净的单领域演示 |
| MeSH | NLM 条款（署名，保持更新） | — | 19,491 | 医学；CMeSH 另有版权 |
| DDC | OCLC 专有 | — | — | 生产受阻 |
| UDC Summary | 许可说法冲突（BY-NC 4.0 / BY-SA 3.0 / BY-NC-ND） | 约 2,600 类 | — | 商用风险 |

来源：[OCLC FAST 下载页](https://www.oclc.org/research/areas/data-science/fast/download.html)、[id.loc.gov 下载页](https://id.loc.gov/download/)、[ALA LRTS](https://journals.ala.org/lrts/article/download/5430/6667)、[Finto YSO 统计](https://api.finto.fi/rest/v1/yso/vocabularyStatistics)、[ZBW STW](https://zbw.eu/stw/version/latest/about)、[NLM MeSH 条款](https://www.nlm.nih.gov/databases/download/terms_and_conditions_mesh.html)、[OCLC DDC 条款](https://oclc.org/research/activities/browser/terms.html)、[UDC Summary 导出页](https://udcsummary.info/exports.htm)、[UDCC FAQ](https://udcc.org/index.php/faq/7)、[QLever Wikidata](https://qlever.dev/api/wikidata)。

这些数字有一个容易误读的地方：LCSH 的 4 万多个中文标签只覆盖约 **12%** 的 LCSH。而且偏向人物、物种这类适合写成维基条目的实体，"China—History—1949-1976"这样的复分串几乎不可能有对应条目。研究者抽样还发现几类问题：
- 简繁混在同一个 `zh` 标签下。
- 一个 Wikidata 条目对应多个 LCSH 号。
- 标签带维基标题腔，如"在美國的伊斯蘭教"。

所以 Wikidata 只能当种子，主体翻译要靠大模型。FAST 在 2024-10-10 之后是否还在更新，OCLC 页面没有说明。

翻译流程已有可借鉴的先例：
- WOKIE（CHR 2025）是一套开源流水线，用机器翻译加大模型修订来翻译 SKOS 叙词表。它在 28 个机器翻译服务中只有 8 个可用；评估方法是删掉一种语言再重新生成，与原标签比对；但测试没有覆盖中文（[arXiv 2507.19537](https://arxiv.org/abs/2507.19537)）。
- 芬兰国家图书馆的 Skosmos/Annif 团队在 NKOS 2025 上报告，他们已用大模型翻译词表、生成合成数据（[NKOS 2025 幻灯片](https://nkos.dublincore.org/2025NKOSworkshop/NKOS%20Skosmos%20and%20Annif.pdf)）。

可行的做法分四层：
1. 先按 zh-cn > zh-hans > zh > zh-hant 的优先级取 Wikidata 标签，用 OpenCC 统一成简体。
2. 剩下的交给大模型。提示里给出英文首选词、入口词、上下位词、范围注释，按兄弟概念成批翻译，以保持术语一致。
3. 复分词（如"—History"）单独翻成对照表，再机械拼接。
4. 质检：回译抽样、检查中文首选词是否重复（"Cells (Biology)"和"Prison cells"这类多义冲突）、按领域分层抽 200–500 个概念人工核对，并给每条标签记录来源（wikidata / llm / human）。

术语在线（termonline）没有找到开放许可，只适合人工比对，不要批量抓取。

美国中心的标目（如"Indians of North America"）以及中国特有主题（朝代、少数民族），在 LCSH 和 FAST 里本来就表达得不好，演示文档里应写明这是已知局限。

## CSL 39.6 万篇论文是训练主力，书目记录要么是英文标签，要么规模小

**CSL（ydli-ai/CSL）是最适合中文 Annif 演示的单一数据集**（[ydli-ai/CSL](https://github.com/ydli-ai/CSL)）：
- 396,209 篇 2010–2020 年的中文论文，有标题、摘要、作者关键词、13 门类 / 67 学科。
- 仓库内有 10k 基准集，谷歌网盘上有 40k 子集和全量。
- 两级学科可以直接组成一个小型封闭词表，作者关键词则是一个开放的大标签集。
- 40k 子集已超过 Annif 维基对 fastText 和 Omikuji 建议的"一万篇以上"（[Annif wiki: Backends](https://github.com/NatLibFi/Annif/wiki/Backends)）。

它的弱点在许可：仓库标注 Apache-2.0，但没有单独的数据许可，摘要来自国家科技资源共享服务中心，期刊和出版方从未授予这项权利。论文本身是 CC BY-NC-SA 4.0（[arXiv 2209.05034](https://arxiv.org/abs/2209.05034)）。稳妥的定位是"教学和研究使用、注明出处、不重新托管"。另外，13/67 对应哪套官方学科目录还没核实。门类数与教育部 2022 年前的学科目录一致，但这只是推断。

其他中文文本集只适合当分类练习：
- **TNEWS**：今日头条新闻标题，15 类，53,360 条训练。
- **IFLYTEK**：应用描述，119 类，12,133 条训练。
- **THUCNews**：新浪新闻，14 类，约 74 万篇。

三者都是单标签、类别少，许可要么是"No known license"，要么是"Other"（[CLUE](https://github.com/CLUEbenchmark/CLUE)；[TFDS 目录](https://tensorflow.google.cn/datasets/community_catalog/huggingface/clue?hl=en)；[HyperAI](https://hyper.ai/cn/datasets/9277)）。CAKE 医学摘要关键词集（10 万篇训练）可以补医学方向（[JDIS 2021](https://reference-global.com/article/10.2478/jdis-2021-0013)）。百度百科的 robots.txt 屏蔽了大部分爬虫，也没有开放许可，应当避开（[凤凰科技](https://tech.ifeng.com/c/8cFdsd8yDPe)）。

真正的图书书目记录分两条线。

**英文标签线。** Harvard Library Bibliographic Dataset 是 **CC0** 的 MARCXML。研究者从 API 实测到 67 个唯一文件、约 7.2 GB 压缩数据、每个文件 20 万条，据此估算全量约 1,330 万条；快照日期是 2022-02-15（[Dataverse API](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/I8L0ZZ)；[Harvard 开放元数据](https://library.harvard.edu/open-metadata)）。但**中文记录数、LCSH 覆盖率都没测出来**：每个数据文件都挡在 Dataverse 的 guestbook 后面，要填姓名、邮箱、机构、职位（[guestbook 514](https://dataverse.harvard.edu/api/guestbooks/514)）。这一步需要你本人去填。填完之后，草稿区里现成的统计脚本 `harvard_chi_stats.py` 可以直接跑出中文记录数、650 字段第二指示符为 0（即 LCSH）的比例、880 中文题名的比例和高频标目。建议抽两个相隔较远的文件，比如 _010 和 _060。

这条线拿到的标签是英文 LCSH 串，文本多半只有题名，有时带丛编和目次，摘要很少。用于演示，需要配合上一节翻译出来的 FAST 中文词表。LC 的 MDSConnect Books All 同样丰富，但 LC 声明其记录在美国境外受版权保护（[LC CDS](https://loc.gov/cds/mdsftp.html)）。

**中文标签线。** 这条线在台湾，规模小但许可最干净：
- 国发会图书室中文图书清单（研究者本地核实约 21,276 行，索书号含中文图书分类法号，无主题词列）（[data.gov.tw 28528](https://data.gov.tw/en/datasets/28528)）。
- 智慧局馆藏目录，带分类号（[data.gov.tw 123143](https://data.gov.tw/dataset/123143)）。
- 国图 ISBN 中心每月的《新書書目》PDF，每条带主题词和分类号，是"中文题名 → 中文主题词"最好的来源。但它托管在 isbn.ncl.edu.tw，政府开放授权是否适用未经确认（[PDF 示例](https://isbn.ncl.edu.tw/FCKEDITOR_UploadFiles/1596771809.pdf)）。

豆瓣标签是大众分类法，而且没有开放数据，不建议使用。

## 合成数据能加 2–4 个点 nDCG，但不能替代人工标注的测试集

用大模型生成训练数据的最好证据，来自 Annif 团队自己的两次评测。

**SemEval-2025。** 团队用 Llama-3.1-8B 在单张 A100 上以约 8 条/秒的速度生成数据。做法是：给模型一条原始记录和它的金标准标签，再随机加一个词表术语，让它写一条覆盖全部主题的新记录。原始与合成按 1:3 混合，Omikuji Bonsai 的 nDCG@10 提高约 0.02，后续批次收益很小。团队在全主题任务上排名第一（[arXiv 2504.19675](https://arxiv.org/html/2504.19675v1)）。

**GermEval-2025。** 团队改用 3–12B 的小模型，每种语言生成四套与训练集同规模的合成集。Bonsai 德语 nDCG@20 从 0.5122 升到 0.5513，英语用 Qwen3-4B 生成的数据从 0.5595 升到 0.5896。再用 24B 模型对前 100 个候选重排序，又多出 0.025–0.036（[arXiv 2508.15877](https://arxiv.org/html/2508.15877v1)）。

由此可以得出三条规则：
- 合成数据只喂给 Omikuji、fastText 这类关联型后端。团队没有把它用于 MLLM，XTransformer 也没从中获益。
- 合成数据增强的是现有标注，不是凭空造标注。
- 测试集必须全部是人工标注。

完全让大模型给文档打标签风险很大。一项研究发现，用大模型标注替代金标准训练分类器，会带来系统性的、非随机的误差。在一个数据集上，Krippendorff's α 从金标准的 84.30 降到 52.72（3B 标注模型）和 43.75（7B 标注模型），换更大的模型也没解决（[arXiv 2504.15432](https://arxiv.org/html/2504.15432v1)）。

所以"全合成语料"只适合演示流水线怎么跑，在教材里要明确标注为合成数据，指标不能当真。Qwen3 这类中文能力强的 4–8B 模型在 GermEval 中表现良好，可以直接拿来生成中文标题和摘要。研究者没有找到任何专门针对中文主题标引的合成数据研究，这是一块空白。

## 结论

这项调研真正改变的判断是：**中文 Annif 的瓶颈不在算法，而在"词表与训练数据能否对得上"**。开放世界里的中文词表和中文训练数据来自两个互不相干的体系：台湾主题词表没有配套的开放书目，CSL 论文没有图书馆主题词，Harvard 记录的标签是英文 LCSH。因此，项目的核心工程是"对齐"：
- 把 CSL 作者关键词匹配到主题词表的首选词和入口词。台湾标目短小、不复分，和作者关键词形态接近，这条路看起来最顺。但匹配率还没测，是第一项要验证的数字。
- 或者把 LCSH 经 FAST 转成中文。

第二个判断是：**演示和生产对许可的要求完全不同**。CSL 适合课堂，但不适合再发布；台湾主题词表、AGROVOC、FAST 和 Wikidata 可以公开发布衍生词表。真正贴合大陆编目习惯的中图法、中分表加 CNMARC，只能靠授权获得。所以克隆版 Annif 应当把词表和数据做成可替换的配置，等将来拿到授权数据时，直接换掉即可。

## 推荐演示路线与需要你做的决定

**推荐组合：词表用"台湾《中文主題詞表》简体化版"作主词表，"CSL 67 学科"作入门词表，AGROVOC 作领域示例；训练数据用 CSL 40k 子集（文本为标题加摘要）；后端用 TF-IDF 作基线，MLLM 做词汇匹配，Omikuji Bonsai 或 fastText 做关联学习，最后集成。** 具体步骤如下：

| 步骤 | 内容 | 产出 / 验收 | 预计工作量 |
|---|---|---|---|
| 0. 环境与分析器 | Fork Annif v1.4.2（Python 3.12），在 `annif/analyzer/` 下新增约 30 行的 jieba 分析器（`token_min_length=1`，按"。！？"断句）；安装 OpenCC | `annif analyze` 能输出正确的中文词序列 | 半天 |
| 1. 入门词表 | 把 CSL 的 13 门类和 67 学科自建为 SKOS（门类作为 broader） | 可加载的小词表 | 1 小时 |
| 2. 主词表 | 把台湾主题词表 CSV 转成 SKOS/TSV：自建 URI；主题词经 OpenCC tw2sp 转为简体首选词，保留繁体作 `zh-Hant` 别名；"不用"转为 altLabel，"參見"转为 related，类号转为 notation（规范分隔符，去掉方括号）；人工补一批大陆用词别名 | 约 17,125 个概念的 SKOS，注明出处和许可 | 1–2 天（约 100 行 RDFLib 代码） |
| 3. 训练语料 | CSL 40k：文本为标题加摘要；标签 A 为学科；标签 B 为作者关键词与主词表首选词及别名精确匹配后的 URI；只保留至少命中一个主题词的记录；留出 2–5k 条人工标签记录作测试集 | `train.tsv` / `test.tsv`，并记录关键词匹配率 | 1 天 |
| 4. 训练与评估 | 先跑 TF-IDF 基线；在主词表上训练 MLLM（100–10k 篇即可）；训练 Omikuji Bonsai 和 fastText（10k 以上）；最后做集成；用 `annif eval --limit 5` 输出 P/R/F1@5 和 nDCG | 指标表，以及每个主题的结果文件（用来展示长尾弱点） | 1–2 天 |
| 5. 领域示例 | 加载 AGROVOC（语言统一为 `zh`），用 CSL 中的农学论文训练一个"开箱即用"的项目 | 第二个演示项目 | 半天 |
| 6. 可选增强 | 用 Qwen3-4B/8B 按 Annif 的一次示例配额外术语的方法生成合成记录（1:1 到 1:3，只加入训练集）；或用大模型重排序 | 对比有无合成数据的指标 | 1–2 天，需要 GPU 或 API |
| 7. 演示 | 通过 Annif Web 界面和 REST API 现场粘贴中文摘要，展示推荐的主题词和类号 | 课堂演示脚本 | 半天 |

如果第 3 步测出的关键词匹配率太低（比如不到一半的记录能命中主题词），退路有两条：改为把关键词匹配到 Wikidata QID（CC0），或者改用翻译后的 FAST 中文词表配 Harvard 中文题名。

**需要你做的决定或动作：**

| # | 事项 | 为什么需要你 |
|---|---|---|
| 1 | 是否接受"繁体台湾主题词表转简体"作为演示主词表，还是希望走"翻译 FAST/LCSH"路线（规模更大，但要投入大模型翻译和人工审校） | 决定词表的风格和工作量 |
| 2 | 定位：只做内部教学，还是要公开发布演示和衍生数据 | 公开发布就不能带 CSL 原文和中图法抓取版，只能用开放许可数据 |
| 3 | 是否亲自填写 Harvard Dataverse 的 guestbook（姓名、邮箱、机构、职位），以便测量中文记录规模 | 这需要提交你的个人信息，我不能代填；填完后脚本可以直接运行 |
| 4 | 大模型资源：本地 GPU、Apple Silicon，还是托管 API（以及预算） | 影响第 6 步和词表翻译能否进行、速度多快 |
| 5 | 是否联系外部机构：向台湾国家图书馆询问《新書書目》PDF 和 catsmart 的授权；向 DCMI-2026 论文作者询问 CNMARC 数据；向合作馆申请内部使用的 CNMARC 导出（606/690/330） | 这些是走向生产的数据来源，需要以你或你所在机构的名义联系 |
| 6 | 是否允许在不公开的课堂实验中使用 GitHub 上无许可的中图法抓取版 | 涉及版权风险，需要你来判断 |
| 7 | 走向生产时，是否向国家图书馆申请中图法、中分表的授权 | 只有这样才能贴合大陆编目实践 |
