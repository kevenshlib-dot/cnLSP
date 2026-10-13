"""端到端：在临时目录里搭一个极小的 Annif 环境（jieba 分析器 + TF-IDF 来源 + llm_rerank），
用假大模型服务跑 suggest / learn / 出错回退。"""

import json

import pytest
from click.testing import CliRunner

import annif.cli
from annif_zh.llm import fake_server

VOCAB = {
    "u:diesel": "柴油机", "u:emission": "排放", "u:nursing": "护理", "u:surgery": "手术",
    "u:grid": "网格", "u:info": "信息资源", "u:apply": "应用", "u:control": "控制",
}
CORPUS = [
    ("农用柴油机排放控制技术探讨", ["u:diesel", "u:emission", "u:control"]),
    ("船用柴油机排放标准与应用", ["u:diesel", "u:emission", "u:apply"]),
    ("开胸手术患者的护理干预", ["u:nursing", "u:surgery"]),
    ("手术室护理质量管理", ["u:nursing", "u:surgery"]),
    ("网格技术在信息资源管理中的应用", ["u:grid", "u:info", "u:apply"]),
    ("信息资源共享与网格计算", ["u:grid", "u:info"]),
]


def _cfg(endpoint, extra=""):
    return f"""
[src]
name=source
language=zh
backend=tfidf
analyzer=jieba
vocab=v
limit=100

[llm]
name=llm rerank
language=zh
backend=llm_rerank
vocab=v
sources=src
limit=5
candidates=8
select=3
endpoint={endpoint}
model=fake
{extra}
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    srv, handler = fake_server.start()
    endpoint = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    monkeypatch.chdir(tmp_path)
    (tmp_path / "vocab.tsv").write_text("".join(f"<{u}>\t{l}\n" for u, l in VOCAB.items()), encoding="utf-8")
    (tmp_path / "train.tsv").write_text(
        "".join(f"{t}\t{' '.join(f'<{u}>' for u in us)}\n" for t, us in CORPUS), encoding="utf-8")
    runner = CliRunner()

    def run(*args, cfg=None, input=None):
        (tmp_path / "projects.cfg").write_text(cfg or _cfg(endpoint), encoding="utf-8")
        result = runner.invoke(annif.cli.cli, [*args, "--projects", "projects.cfg"], input=input)
        assert result.exit_code == 0, result.output + repr(result.exception)
        return result.output

    run("load-vocab", "v", "vocab.tsv", "--language", "zh")
    run("train", "src", "train.tsv")
    yield run, endpoint, handler
    srv.shutdown()


def _labels(output):
    return [line.split("\t")[1] for line in output.strip().splitlines() if "\t" in line]


def test_suggest_reranks_with_llm(env):
    run, _, handler = env
    out = run("suggest", "llm", input="农用柴油机的排放控制与应用")
    labels = _labels(out)
    # 假大模型选出原文中字面出现的候选，它们应排在最前
    assert set(labels[:4]) == {"柴油机", "排放", "控制", "应用"}
    assert handler.requests_seen == 1


def test_falls_back_to_source_when_llm_down(env):
    run, endpoint, _ = env
    down = _cfg("http://127.0.0.1:9/v1", "timeout=2")
    src = _labels(run("suggest", "src", input="开胸手术护理"))
    llm = _labels(run("suggest", "llm", input="开胸手术护理", cfg=down))
    assert llm == src[:5]


def test_learn_stores_examples_and_uses_them(env, tmp_path):
    run, endpoint, _ = env
    cfg = _cfg(endpoint, "allow_learn=1\nexamples=2")
    (tmp_path / "learn.tsv").write_text("编目员确认：护理干预研究\t<u:nursing>\n", encoding="utf-8")
    run("learn", "llm", "learn.tsv", cfg=cfg)
    rows = [json.loads(l) for l in (tmp_path / "data/projects/llm/examples.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows == [{"text": "编目员确认：护理干预研究", "subjects": ["护理"]}]
    assert _labels(run("suggest", "llm", input="手术护理", cfg=cfg))


def test_learn_disabled_by_default(env, tmp_path):
    run, endpoint, _ = env
    (tmp_path / "learn.tsv").write_text("护理\t<u:nursing>\n", encoding="utf-8")
    (tmp_path / "projects.cfg").write_text(_cfg(endpoint), encoding="utf-8")
    result = CliRunner().invoke(annif.cli.cli, ["learn", "llm", "learn.tsv", "--projects", "projects.cfg"])
    assert result.exit_code != 0


def test_empty_replies_fall_back(env):
    run, endpoint, handler = env
    handler.empty_next = 99
    src = _labels(run("suggest", "src", input="开胸手术护理"))
    assert _labels(run("suggest", "llm", input="开胸手术护理")) == src[:5]


def test_thinking_param_is_sent(env):
    run, endpoint, handler = env
    run("suggest", "llm", input="网格与信息资源", cfg=_cfg(endpoint, "thinking=disabled"))
    assert handler.last_body["thinking"] == {"type": "disabled"}
