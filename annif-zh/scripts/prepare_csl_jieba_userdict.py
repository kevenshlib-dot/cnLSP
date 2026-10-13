"""用 jieba + 自定义词典 + 停用词重新切分 CSL，生成可与原 jieba 版直接对比的数据集。

文档 ID、划分、标准答案和词表都取自已有的 jieba 版数据集（annif-csl-jieba-server），
只替换 text。原始文本按 csl_annif.py 的同一规则（NFKC、空白归一、标题 + 摘要、
sha256 指纹）从 CSL TSV 中找回。

自定义词典：词表里每个关键词的中文片段（>=2 字），频率交给 jieba.suggest_freq，
保证它能被整体切出。停用词：configs/zh_stopwords.txt 中不在词表里的词。

用法（在 annif-zh 镜像里运行，jieba 0.42.1）：
  python prepare_csl_jieba_userdict.py <csl.tsv> <baseline_dir> <stopwords.txt> <out_dir> [workers]
"""

import csv
import hashlib
import json
import multiprocessing
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

CJK = r"㐀-䶿一-鿿"
TOKEN_PARTS = re.compile(rf"[{CJK}]+|[A-Za-z0-9]+")
CJK_RUN = re.compile(rf"[{CJK}]{{2,}}")

TOKENIZER = None
STOPWORDS = frozenset()


def clean(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


def init_worker(userdict_path, stopwords):
    global TOKENIZER, STOPWORDS
    import logging

    import jieba

    jieba.setLogLevel(logging.WARNING)
    TOKENIZER = jieba.Tokenizer()
    TOKENIZER.initialize()
    TOKENIZER.load_userdict(userdict_path)
    STOPWORDS = frozenset(stopwords)


def segment(text):
    tokens = []
    for token in TOKENIZER.cut(clean(text), cut_all=False, HMM=True):
        for part in TOKEN_PARTS.findall(token):
            part = part.lower()
            if part not in STOPWORDS:
                tokens.append(part)
    return " ".join(tokens)


def process(item):
    split, doc, raw = item
    doc = dict(doc, text=segment(raw))
    return split, doc


def main(tsv, baseline, stopwords_file, out, workers=8):
    baseline, out = Path(baseline), Path(out)
    out.mkdir(parents=True, exist_ok=False)

    labels = [r["label_zh"] for r in csv.DictReader(open(baseline / "vocab.csv", encoding="utf-8"))]
    entries = sorted({run for label in labels for run in CJK_RUN.findall(clean(label))})
    userdict = out / "userdict.txt"
    # 只写词、不写频率：jieba 会为每个词调用 suggest_freq，保证它能整体切出
    userdict.write_text("\n".join(entries) + "\n", encoding="utf-8")

    label_set = {clean(label).lower() for label in labels}
    raw_stop = [w.strip() for w in open(stopwords_file, encoding="utf-8")
                if w.strip() and not w.startswith("#")]
    stopwords = sorted(w for w in set(raw_stop) if w not in label_set)
    kept_as_labels = sorted(set(raw_stop) & label_set)
    (out / "stopwords.txt").write_text("\n".join(stopwords) + "\n", encoding="utf-8")

    # 指纹 -> 原始文本（标题 + 摘要）
    raw_text = {}
    with open(tsv, encoding="utf-8-sig") as f:
        for line in f:
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 5:
                continue
            text = clean(fields[0] + " " + fields[1])
            raw_text.setdefault(hashlib.sha256(text.encode()).hexdigest(), text)

    def items():
        for split in ("train", "dev", "test"):
            with open(baseline / f"{split}.jsonl", encoding="utf-8") as f:
                for line in f:
                    doc = json.loads(line)
                    yield split, doc, raw_text[doc["document_id"]]

    counts, tokens = Counter(), Counter()
    handles = {s: open(out / f"{s}.jsonl", "w", encoding="utf-8") for s in ("train", "dev", "test")}
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(workers, initializer=init_worker, initargs=(str(userdict), stopwords)) as pool:
        for split, doc in pool.imap(process, items(), chunksize=256):
            handles[split].write(json.dumps(doc, ensure_ascii=False) + "\n")
            counts[split] += 1
            tokens[split] += doc["text"].count(" ") + 1
            if sum(counts.values()) % 50000 == 0:
                print(f"segmented {sum(counts.values()):,}", flush=True)
    for h in handles.values():
        h.close()

    for name in ("vocab.csv", "example.txt"):
        (out / name).write_bytes((baseline / name).read_bytes())
    stats = {
        "baseline": str(baseline),
        "preprocessing": "NFKC + jieba 0.42.1 precise/HMM + vocabulary user dictionary + stopwords",
        "userdict_entries": len(entries),
        "stopwords": len(stopwords),
        "stopwords_kept_because_they_are_labels": kept_as_labels,
        "documents": dict(counts),
        "mean_tokens": {s: round(tokens[s] / counts[s], 2) for s in counts},
        "comparison": "Same document IDs, splits, subjects and vocabulary as the baseline; only text changes.",
    }
    (out / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:5], *(int(a) for a in sys.argv[5:6]))
