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

## llm_rerank 后端：大模型在候选中重排

它的接入方式参照 Annif 自带的 Omikuji 后端：

- 大模型本身在 Annif 外面运行，可以是 Ollama、vLLM 或云端 API，通过 OpenAI 兼容接口调用。
- Annif 里只放一个很薄的适配层 [annif_zh/backend/llm_rerank.py](annif_zh/backend/llm_rerank.py)，按需导入。

### 工作流程

1. 从 `sources` 指定的项目取前 `candidates` 个候选。
2. 把候选编号成 C1…Cn，连同原文交给大模型，要求它只按编号挑选，并给出置信度。不认识的编号一律丢弃，所以结果不会超出词表。
3. 最终分数 = `blend` × 大模型置信度 + (1 − `blend`) × 来源分数。`mode=filter` 时丢弃大模型没选中的候选。
4. 网络、超时或回复格式出错时，原样返回来源项目的排序，并记一条警告。
5. 回复缓存在项目数据目录的 `llm-cache.sqlite3` 里，重复评测时不重复调用大模型。

### 配置示例

完整示例见 [configs/csl-llm-rerank.cfg](configs/csl-llm-rerank.cfg)。

```ini
[csl-llm]
backend=llm_rerank
sources=csl-ensemble
candidates=30
select=8
endpoint=http://host.docker.internal:11434/v1
model=qwen3:8b
api_key_env=LLM_API_KEY
```

### 参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `candidates` | 30 | 交给大模型的候选数 |
| `select` | 8 | 让大模型最多选几个 |
| `blend` | 0.7 | 最终分数中大模型置信度占的权重 |
| `mode` | rerank | `rerank` 把未选中的候选降分保留；`filter` 直接丢弃 |
| `endpoint` / `model` | Ollama / qwen3:8b | 任意 OpenAI 兼容接口 |
| `api_key_env` | LLM_API_KEY | 存放 API 密钥的环境变量名。密钥不要写进配置 |
| `temperature` / `max_tokens` / `timeout` | 0 / 1024 / 120 | |
| `thinking` | 空 | 推理模型的思考开关，可设为 `disabled` 或 `enabled`；为空时不发送。DeepSeek V4 必须设为 `disabled` |
| `max_chars` | 1500 | 原文最多发送多少字 |
| `concurrency` | 4 | 同时发出的请求数 |
| `examples` | 3 | 提示词里放几条已确认的示例 |
| `cache` | 1 | 是否缓存大模型回复 |
| `allow_learn` | 0 | 是否允许 `learn` 写入示例 |

### 人工校准

设置 `allow_learn=1` 后，可以把编目员确认过的记录交给这个项目：用命令 `annif learn csl-llm 确认记录.tsv`，或调用 REST 接口 `POST /v1/projects/csl-llm/learn`。

这些记录会追加到 `examples.jsonl`，其中最近的 `examples` 条作为少样本示例放进提示词。

### 离线测试

[annif_zh/llm/fake_server.py](annif_zh/llm/fake_server.py) 是一个假的大模型服务，提供同样的接口。它的规则是挑出原文中字面出现的候选，回复外面包一层 `<think>` 推理块，用来检验解析是否稳健。

在 CSL 测试集前 1,000 篇上，用它重排加权集成的结果：

| 指标 | 只用加权集成 | 加上假大模型重排 |
|---|---|---|
| F1@5 | 0.352 | 0.371 |
| nDCG@10 | 0.526 | 0.543 |

可见重排这一步本身就有效。这个"字面出现优先"的简单规则也是一条基线，真实大模型至少要超过它。

### DeepSeek 实测

200 篇的试验结果见 [大模型重排试验_200篇.md](大模型重排试验_200篇.md)。

| 方案 | F1@5 | 相对 Annif |
|---|---|---|
| Annif | 0.339 | — |
| 字面出现规则 | 0.363 | +0.024 |
| DeepSeek flash（关闭思考） | 0.371 | +0.033，95% 置信区间 [+0.010, +0.056] |

编目员盲评表由 `scripts/make_blind_review.py` 生成，填完后用 `scripts/score_blind_review.py` 统计。

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
