"""把已分词的 CSL 语料还原成原始文本（标题 + 摘要），供 jieba 分析器直接训练。

文档 ID、划分、标准答案保持不变。用法：
  python make_raw_corpus.py <csl.tsv> <segmented_dir> <out_dir>
"""

import hashlib
import json
import sys
import unicodedata
from pathlib import Path


def clean(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


def main(tsv, segmented, out):
    segmented, out = Path(segmented), Path(out)
    out.mkdir(parents=True, exist_ok=False)
    raw = {}
    with open(tsv, encoding="utf-8-sig") as f:
        for line in f:
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) == 5:
                text = clean(fields[0] + " " + fields[1])
                raw.setdefault(hashlib.sha256(text.encode()).hexdigest(), text)
    for split in ("train", "dev", "test"):
        with open(segmented / f"{split}.jsonl", encoding="utf-8") as src, \
                open(out / f"{split}.jsonl", "w", encoding="utf-8") as dst:
            for line in src:
                doc = json.loads(line)
                doc["text"] = raw[doc["document_id"]]
                dst.write(json.dumps(doc, ensure_ascii=False) + "\n")
    (out / "vocab.csv").write_bytes((segmented / "vocab.csv").read_bytes())
    print(f"wrote {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
