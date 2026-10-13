"""测量 CSL 论文关键词与台湾国家图书馆《中文主題詞表》(data.gov.tw 27190) 的对齐率。

用法: python -I csl_ncl_alignment.py <csh.csv> <csl_camera_readly.tsv> <输出目录>

匹配层级:
  exact   关键词规范化后与主题词(首选词或"不用"入口词)完全一致
  suffix  关键词以某个主题词结尾(取最长的,且主题词至少 2 字),如 农用柴油机 -> 柴油机
  text    主题词作为子串出现在标题中(近似 MLLM 词汇匹配的上限)
"""

import collections
import csv
import json
import sys
import unicodedata

import ahocorasick
from opencc import OpenCC

TW2SP = OpenCC("tw2sp")
T2S = OpenCC("t2s")
SEP = "；"


def norm(s):
    return unicodedata.normalize("NFKC", s).strip().lower().replace(" ", "")


def split_multi(s):
    return [p for p in unicodedata.normalize("NFKC", s).replace(";", SEP).split(SEP) if p.strip()]


def load_ncl(path):
    """返回 (headings, lookup)。headings: id -> 简体首选词; lookup: 规范化标签 -> id。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    headings, nonpref = {}, []
    for r in rows:
        term = r["主題詞"].strip()
        if r["用"].strip():
            nonpref.append((term, r["用"].strip()))
        else:
            headings[term] = TW2SP.convert(term)
    lookup = {}

    def add(label, hid):
        for v in {label, TW2SP.convert(label), T2S.convert(label)}:
            lookup.setdefault(norm(v), hid)

    for term in headings:
        add(term, term)
    for term, target in nonpref:
        # "用" 可能指向多个首选词,取第一个存在的
        for t in split_multi(target):
            if t.strip() in headings:
                add(term, t.strip())
                break
    return headings, lookup


def main(ncl_path, csl_path, out_dir):
    headings, lookup = load_ncl(ncl_path)
    # 后缀匹配: 仅用 >=2 字的标签
    suffix_labels = sorted((k for k in lookup if len(k) >= 2), key=len, reverse=True)
    automaton = ahocorasick.Automaton()
    for k in suffix_labels:
        automaton.add_word(k, k)
    automaton.make_automaton()

    def suffix_match(kw):
        best = None
        for end, label in automaton.iter(kw):
            if end == len(kw) - 1 and (best is None or len(label) > len(best)):
                best = label
        return lookup[best] if best else None

    docs = 0
    kw_inst = kw_exact = kw_loose = 0
    distinct_kw = collections.Counter()
    distinct_hit = set()
    unmatched = collections.Counter()
    doc_exact = collections.Counter()  # 每篇文档 exact 命中的不同主题词数分布
    doc_loose = collections.Counter()
    doc_title = 0
    heading_docs_exact = collections.Counter()
    heading_docs_loose = collections.Counter()
    by_cat = collections.defaultdict(lambda: [0, 0, 0])  # 文档数, >=1 exact, >=1 loose

    with open(csl_path, encoding="utf-8", newline="") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            title, _abstract, kws, _disc, cat = parts
            docs += 1
            ex, lo = set(), set()
            for kw in (k for k in kws.split("_") if k.strip()):
                k = norm(T2S.convert(kw))
                kw_inst += 1
                distinct_kw[k] += 1
                hid = lookup.get(k)
                if hid:
                    kw_exact += 1
                    kw_loose += 1
                    ex.add(hid)
                    lo.add(hid)
                    distinct_hit.add(k)
                    continue
                hid = suffix_match(k)
                if hid:
                    kw_loose += 1
                    lo.add(hid)
                else:
                    unmatched[k] += 1
            t = norm(title)
            if any(len(label) >= 2 for _, label in automaton.iter(t)):
                doc_title += 1
            doc_exact[min(len(ex), 5)] += 1
            doc_loose[min(len(lo), 5)] += 1
            heading_docs_exact.update(ex)
            heading_docs_loose.update(lo)
            c = by_cat[cat]
            c[0] += 1
            c[1] += bool(ex)
            c[2] += bool(lo)

    def at_least(dist, n):
        return sum(v for k, v in dist.items() if k >= n)

    def usable(counter, n):
        return sum(1 for v in counter.values() if v >= n)

    pct = lambda a, b: round(100 * a / b, 1) if b else 0.0
    result = {
        "ncl_preferred_headings": len(headings),
        "ncl_lookup_labels": len(lookup),
        "csl_docs": docs,
        "keyword_instances": kw_inst,
        "keyword_instances_exact_pct": pct(kw_exact, kw_inst),
        "keyword_instances_exact_or_suffix_pct": pct(kw_loose, kw_inst),
        "distinct_keywords": len(distinct_kw),
        "distinct_keywords_exact_pct": pct(len(distinct_hit), len(distinct_kw)),
        "docs_exact_ge": {n: pct(at_least(doc_exact, n), docs) for n in (1, 2, 3)},
        "docs_loose_ge": {n: pct(at_least(doc_loose, n), docs) for n in (1, 2, 3)},
        "docs_title_contains_heading_pct": pct(doc_title, docs),
        "headings_used_exact": len(heading_docs_exact),
        "headings_used_loose": len(heading_docs_loose),
        "headings_with_ge10_docs_exact": usable(heading_docs_exact, 10),
        "headings_with_ge50_docs_exact": usable(heading_docs_exact, 50),
        "headings_with_ge10_docs_loose": usable(heading_docs_loose, 10),
        "headings_with_ge50_docs_loose": usable(heading_docs_loose, 50),
        "by_category": {
            k: {"docs": v[0], "exact_ge1_pct": pct(v[1], v[0]), "loose_ge1_pct": pct(v[2], v[0])}
            for k, v in sorted(by_cat.items(), key=lambda x: -x[1][0])
        },
        "top_headings_exact": [
            (headings[h], n) for h, n in heading_docs_exact.most_common(30)
        ],
        "top_unmatched_keywords": unmatched.most_common(60),
    }
    with open(f"{out_dir}/csl_ncl_alignment.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in result.items() if not k.startswith("top_")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
