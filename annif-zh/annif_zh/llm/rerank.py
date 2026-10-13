"""大模型重排的核心逻辑：拼提示词、解析返回、合并分数。不依赖 Annif，便于单独测试。

约束：大模型只能从编号为 C1…Cn 的候选里选；返回中不认识的编号一律丢弃，
所以输出永远落在词表之内，不会编造主题词。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

SYSTEM_PROMPT = (
    "你是图书馆的主题标引员。任务是为一篇文献从给定的候选主题词中挑选最能概括其主题的词。"
    "只能使用候选列表里的编号，不得自造新词。"
    "优先选择具体、专指的主题词；“应用”“研究”“方法”“问题”“对策”这类泛泛之词，"
    "除非确实是文献的核心主题，否则不要选。"
)

USER_TEMPLATE = """{examples}文献：
{text}

候选主题词（编号 主题词）：
{candidates}

请选出最多 {select} 个最合适的主题词，按相关度从高到低排列，并给出 0 到 1 之间的置信度。
只输出 JSON，不要输出其他内容，格式如下：
{{"subjects": [{{"id": "C1", "score": 0.9}}, {{"id": "C5", "score": 0.6}}]}}"""

EXAMPLE_TEMPLATE = "示例文献：{text}\n已确认的主题词：{subjects}\n\n"

_THINK = re.compile(r"<think>.*?</think>", re.S)


@dataclass
class Candidate:
    key: str          # 提示词里的编号，如 C1
    subject_id: int   # Annif 内部的主题序号
    label: str
    score: float      # 来源项目给出的分数


@dataclass
class Example:
    text: str
    subjects: list[str] = field(default_factory=list)


def make_candidates(items: list[tuple[int, str, float]], n: int) -> list[Candidate]:
    """items 为 (subject_id, label, score)，按分数降序取前 n 个并编号。"""
    ranked = sorted(items, key=lambda x: x[2], reverse=True)[:n]
    return [Candidate(f"C{i + 1}", sid, label, score) for i, (sid, label, score) in enumerate(ranked)]


def build_messages(text: str, candidates: list[Candidate], select: int,
                   examples: list[Example] | None = None, max_chars: int = 1500) -> list[dict]:
    text = " ".join(text.split())[:max_chars]
    shots = "".join(
        EXAMPLE_TEMPLATE.format(text=" ".join(ex.text.split())[:300], subjects="、".join(ex.subjects))
        for ex in (examples or [])
    )
    user = USER_TEMPLATE.format(
        examples=shots,
        text=text,
        candidates="\n".join(f"{c.key} {c.label}" for c in candidates),
        select=select,
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def _first_json(content: str):
    """从任意文本中取出第一个能解析的 JSON 对象或数组。"""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", content):
        try:
            value, _ = decoder.raw_decode(content[match.start():])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("回复中没有可解析的 JSON")


def parse_response(content: str, valid_keys: set[str]) -> list[tuple[str, float]]:
    """解析大模型回复，返回 [(编号, 置信度)]，按回复顺序，去重，丢弃不认识的编号。

    兼容：<think> 推理块、```json 代码块、{"subjects": [...]} 或直接的数组、
    数组元素为 {"id","score"} 对象或单纯的编号字符串、缺失或非法的分数。
    """
    value = _first_json(_THINK.sub("", content))
    if isinstance(value, dict):
        value = value.get("subjects", value.get("results", []))
    if not isinstance(value, list):
        raise ValueError("JSON 中没有主题列表")

    picks, seen = [], set()
    for rank, item in enumerate(value):
        if isinstance(item, dict):
            key, score = str(item.get("id", "")).strip(), item.get("score")
        else:
            key, score = str(item).strip(), None
        key = key.upper()
        if key not in valid_keys or key in seen:
            continue
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = max(1.0 - 0.1 * rank, 0.1)   # 没给分数时按名次递减
        picks.append((key, min(max(score, 0.0), 1.0)))
        seen.add(key)
    return picks


def merge(candidates: list[Candidate], picks: list[tuple[str, float]],
          blend: float = 0.7, mode: str = "rerank") -> list[tuple[int, float]]:
    """合并分数。来源分数先按候选中的最高分归一化到 0–1。

    被选中：blend × 大模型置信度 + (1 − blend) × 来源分数
    未选中：mode=rerank 时保留，得分 (1 − blend) × 来源分数；mode=filter 时丢弃
    """
    top = max((c.score for c in candidates), default=0.0) or 1.0
    picked = dict(picks)
    merged = []
    for c in candidates:
        source = c.score / top
        if c.key in picked:
            merged.append((c.subject_id, blend * picked[c.key] + (1 - blend) * source))
        elif mode == "rerank":
            merged.append((c.subject_id, (1 - blend) * source))
    return sorted(merged, key=lambda x: x[1], reverse=True)
