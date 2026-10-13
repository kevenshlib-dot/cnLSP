"""从 Annif 词表生成 jieba 自定义词典，并按词表过滤停用词。

用法：
    python -m annif_zh.userdict VOCAB OUT_DIR [--stopwords zh_stopwords.txt] [--lang zh]

VOCAB 可以是 Annif 的 CSV 词表（uri,label_zh,...），也可以是 SKOS 文件（.ttl/.rdf/.nt），
也可以是 `annif load-vocab` 生成的 data/vocabs/<id>/subjects.ttl。

输出：
    OUT_DIR/userdict.txt   每个标签（首选词和入口词）里至少 2 个字的汉字段，一行一个。
                           不写词频，jieba 会自动推算，保证这些词能被整体切出
    OUT_DIR/stopwords.txt  停用词表去掉本身就是标签的词（否则模型永远预测不到这些标签）
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path

from .analyzer import load_wordlist

CJK_RUN = re.compile(r"[㐀-䶿一-鿿]{2,}")


def _clean(label: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", label).split())


def read_labels(vocab: Path, lang: str = "zh") -> list[str]:
    if vocab.suffix == ".csv":
        with vocab.open(encoding="utf-8", newline="") as f:
            rows = csv.DictReader(f)
            columns = [c for c in rows.fieldnames or [] if c == f"label_{lang}"]
            if not columns:
                raise ValueError(f"{vocab} 没有 label_{lang} 列")
            return [row[columns[0]] for row in rows if row[columns[0]]]

    import rdflib
    from rdflib.namespace import SKOS

    graph = rdflib.Graph()
    graph.parse(vocab)
    labels = []
    for prop in (SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel):
        for _, _, label in graph.triples((None, prop, None)):
            if getattr(label, "language", None) in (None, lang) or str(label.language).startswith(lang):
                labels.append(str(label))
    return labels


def build(vocab: Path, out_dir: Path, stopwords: Path | None = None, lang: str = "zh") -> dict:
    labels = [_clean(label) for label in read_labels(vocab, lang)]
    entries = sorted({run for label in labels for run in CJK_RUN.findall(label)})
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "userdict.txt").write_text("\n".join(entries) + "\n", encoding="utf-8")

    result = {"labels": len(labels), "userdict_entries": len(entries)}
    if stopwords:
        label_set = {label.lower() for label in labels}
        raw = load_wordlist(str(stopwords))
        kept = sorted(raw & label_set)
        final = sorted(raw - label_set)
        (out_dir / "stopwords.txt").write_text("\n".join(final) + "\n", encoding="utf-8")
        result.update(stopwords=len(final), stopwords_kept_as_labels=kept)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vocab", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--stopwords", type=Path)
    parser.add_argument("--lang", default="zh")
    args = parser.parse_args()
    result = build(args.vocab, args.out_dir, args.stopwords, args.lang)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
