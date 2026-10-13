# annif-zh

Annif 的中文扩展：jieba 分析器、词表转 jieba 词典工具，以及 CSL 中文主题标引实验。

- 方案与 PRD：[中文 Annif 自动标引工具方案与 PRD](https://claude.ai/code/artifact/7f89703c-a2e9-4628-a647-1fe19704de36)
- 实验结果：
  - [CSL分词与集成对比.md](CSL分词与集成对比.md)
  - [CSL关键词基线结果.md](CSL关键词基线结果.md)
  - [CSL对齐率实测.md](CSL对齐率实测.md)
- 算法路线比较：[算法路线比较与建议.md](算法路线比较与建议.md)

## 镜像

```bash
docker build -f docker/Dockerfile -t annif-zh:1.4.2 .
```

基于 Annif 1.4.2，原生支持 arm64。内含：

- 后端：Omikuji、fastText、nn_ensemble（TensorFlow）
- 中文处理：jieba 0.42.1，以及本目录的 `annif_zh` 包

构建时会执行 `python -m annif_zh.register`，把 jieba 分析器登记进 Annif。

## jieba 分析器

在项目配置里这样写：

```ini
analyzer=jieba
analyzer=jieba(userdict=vocab/userdict.txt,stopwords=vocab/stopwords.txt)
analyzer=jieba(userdict=vocab/userdict.txt,hmm=0,token_min_length=2)
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `userdict` | 无 | jieba 自定义词典，一行一词。唯一的位置参数也被当作这一项 |
| `stopwords` | 无 | 停用词表，一行一词，`#` 开头为注释 |
| `hmm` | 1 | 是否启用 jieba 的 HMM 新词发现 |
| `token_min_length` | 1 | 最短词长。中文主题词以双字词为主，所以不沿用 Annif 默认的 3 |

分词流程：

1. NFKC 规范化。
2. jieba 精确模式切分。
3. 每个词再拆成连续的汉字段或字母数字段。
4. 转小写，去掉停用词。数字串保留。

分句按"。！？；"和换行进行。

几点说明：

- 配置里的路径相对于 Annif 工作目录，不能含逗号。
- 分析器可以被 pickle（Omikuji 会序列化它）。jieba 分词器不进入序列化结果，加载后按需重建。

## 从词表生成词典和停用词表

```bash
python -m annif_zh.userdict VOCAB OUT_DIR --stopwords configs/zh_stopwords.txt
```

- **VOCAB**：可以是 Annif 的 CSV 词表（`uri,label_zh`），也可以是 SKOS 文件。
- **userdict.txt**：从首选词、入口词、隐藏词中取出所有至少两个字的汉字段。
- **stopwords.txt**：会去掉本身就是标签的词，否则这些标签永远预测不出来。

## 测试

```bash
docker run --rm -v "$PWD/tests:/tests:ro" annif-zh:1.4.2 \
    sh -c 'pip install -q pytest && cd /tmp && python -m pytest -q /tests -p no:cacheprovider'
```

在 CSL 测试集前 3,000 篇上，分析器的分词结果和离线脚本 `scripts/prepare_csl_jieba_userdict.py` 逐词一致。

用原始中文加这个分析器端到端训练，加权集成的 F1@5 为 0.344（测试集前 5,000 篇）。离线分词版是 0.346，差异来自两次调出的集成权重不同。

## 目录

| 路径 | 内容 | 能否进仓库 |
|---|---|---|
| `annif_zh/` | 分析器、词典工具、登记脚本 | 是 |
| `configs/` | Annif 项目配置、自编停用词表 | 是 |
| `scripts/` | 数据准备、实验、评测脚本 | 是 |
| `docker/` | 镜像定义 | 是 |
| `tests/` | 单元测试 | 是 |
| `data/teaching/` | CSL 及其派生数据，仅限教学 | 否，已 gitignore |
| `data/licensed/` | 授权词表与本馆数据，仅限内网 | 否，已 gitignore |
| `models/` | 训练好的模型和日志 | 否，已 gitignore |
