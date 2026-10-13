import pytest

from annif_zh.llm.rerank import Example, build_messages, make_candidates, merge, parse_response

CANDS = make_candidates([(10, "柴油机", 0.6), (11, "排放", 0.4), (12, "应用", 0.2), (13, "控制", 0.3)], 3)
KEYS = {c.key for c in CANDS}


def test_make_candidates_sorted_and_cut():
    assert [(c.key, c.label) for c in CANDS] == [("C1", "柴油机"), ("C2", "排放"), ("C3", "控制")]


def test_build_messages_contains_candidates_examples_and_truncates():
    msgs = build_messages("甲" * 3000, CANDS, select=2, examples=[Example("示例原文", ["排放"])], max_chars=100)
    user = msgs[-1]["content"]
    assert msgs[0]["role"] == "system"
    assert "C1 柴油机" in user and "C3 控制" in user and "最多 2 个" in user
    assert "示例文献：示例原文" in user and "已确认的主题词：排放" in user
    assert "甲" * 100 in user and "甲" * 101 not in user


@pytest.mark.parametrize("reply", [
    '{"subjects": [{"id": "C2", "score": 0.9}, {"id": "C1", "score": 0.5}]}',
    '<think>想一想 {"subjects": []}</think>```json\n{"subjects": [{"id": "c2", "score": 0.9}, {"id": "C1", "score": 0.5}]}\n```',
    '好的：[{"id": "C2", "score": "0.9"}, {"id": "C1", "score": 0.5}]',
])
def test_parse_response_formats(reply):
    assert parse_response(reply, KEYS) == [("C2", 0.9), ("C1", 0.5)]


def test_parse_response_drops_unknown_duplicates_and_fills_scores():
    reply = '{"subjects": ["C9", "C1", {"id": "C1", "score": 1}, {"id": "C3"}, {"id": "C2", "score": 7}]}'
    assert parse_response(reply, KEYS) == [("C1", 0.9), ("C3", 0.7), ("C2", 1.0)]


def test_parse_response_without_json_raises():
    with pytest.raises(ValueError):
        parse_response("我觉得是柴油机", KEYS)


def test_merge_rerank_keeps_unpicked_below_picked():
    merged = merge(CANDS, [("C2", 0.9)], blend=0.7, mode="rerank")
    assert [sid for sid, _ in merged] == [11, 10, 13]
    assert merged[0][1] == pytest.approx(0.7 * 0.9 + 0.3 * (0.4 / 0.6))
    assert merged[1][1] == pytest.approx(0.3 * 1.0)


def test_merge_filter_drops_unpicked():
    # C3: 0.7×0.9 + 0.3×0.5 = 0.78；C1: 0.7×0.3 + 0.3×1.0 = 0.51；C2 未选中被丢弃
    assert [sid for sid, _ in merge(CANDS, [("C3", 0.9), ("C1", 0.3)], mode="filter")] == [13, 10]
