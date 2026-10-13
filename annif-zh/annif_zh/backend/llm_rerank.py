"""llm_rerank：用大模型在来源项目的候选主题词中挑选、重排。

配置示例（projects.cfg）：

    [csl-llm]
    name=CSL keywords + LLM rerank
    language=zh
    backend=llm_rerank
    vocab=csl-keywords
    sources=csl-ensemble
    limit=10
    candidates=30
    select=8
    endpoint=http://localhost:11434/v1
    model=qwen3:8b

工作流程：
  1. 从 sources 指定的项目取推荐（多个来源时按权重平均），取前 candidates 个作为候选。
  2. 把原文和候选（编号 + 主题词）交给大模型，要求只按编号挑选，并给出置信度。
  3. 按 blend 合并大模型置信度和来源分数，返回前 limit 个。
  4. 大模型出错或回复无法解析时，原样返回来源排序，并记一条警告。

人工校准：开启 allow_learn=1 后，Annif 的 learn 接口（命令行 `annif learn`，或 REST
/projects/<id>/learn）收到的、经编目员确认的记录会存进项目数据目录的 examples.jsonl，
最近的 examples 条作为少样本示例加入提示词。
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

import annif.util
from annif.backend import backend
from annif.backend.ensemble import BaseEnsembleBackend
from annif.exception import NotSupportedException
from annif.suggestion import SubjectSuggestion, SuggestionBatch

from annif_zh.llm.client import ChatClient
from annif_zh.llm.rerank import Example, build_messages, make_candidates, merge, parse_response

if TYPE_CHECKING:
    from datetime import datetime

    from annif.corpus.document import Document, DocumentCorpus


class LLMRerankBackend(BaseEnsembleBackend, backend.AnnifLearningBackend):
    name = "llm_rerank"

    EXAMPLES_FILE = "examples.jsonl"
    CACHE_FILE = "llm-cache.sqlite3"

    DEFAULT_PARAMETERS = {
        "candidates": 30,        # 交给大模型的候选数
        "select": 8,             # 要求大模型最多选几个
        "blend": 0.7,            # 最终分数中大模型置信度的权重
        "mode": "rerank",        # rerank：未选中的候选降分保留；filter：未选中的丢弃
        "endpoint": "http://localhost:11434/v1",
        "model": "qwen3:8b",
        "api_key_env": "LLM_API_KEY",   # 存放 API 密钥的环境变量名，不在配置里写密钥
        "temperature": 0.0,
        "max_tokens": 1024,
        "thinking": "",          # 推理模型的思考开关：空=不发送；disabled / enabled（DeepSeek V4 等）
        "timeout": 120,
        "max_chars": 1500,       # 原文最多送多少字
        "concurrency": 4,        # 同时发出的请求数
        "examples": 3,           # 提示词里放几条已确认的示例
        "cache": True,
        "allow_learn": False,
    }

    # 与 ensemble 一致：是否已训练、修改时间都取自来源项目
    @property
    def is_trained(self) -> bool:
        return all(self._get_sources_attribute("is_trained"))

    @property
    def modification_time(self) -> datetime | None:
        return max(filter(None, self._get_sources_attribute("modification_time")), default=None)

    def _train(self, corpus: DocumentCorpus, params: dict[str, Any], jobs: int = 0):
        raise NotSupportedException(
            "llm_rerank 无需训练；请训练它的来源项目。人工确认的记录可用 learn 加入示例。")

    def _label(self, subject_id: int) -> str:
        labels = self.project.subjects[subject_id].labels or {}
        return labels.get(self.project.language) or next(iter(labels.values()), "")

    # ---- 人工校准：learn 存示例 ----

    def _examples_path(self) -> str:
        return os.path.join(self.datadir, self.EXAMPLES_FILE)

    def _learn(self, corpus: DocumentCorpus, params: dict[str, Any]) -> None:
        if not annif.util.boolean(params["allow_learn"]):
            raise NotSupportedException("learn 未开启，请在项目配置中设置 allow_learn=1")
        os.makedirs(self.datadir, exist_ok=True)
        with open(self._examples_path(), "a", encoding="utf-8") as f:
            for doc in corpus.documents:
                labels = [self._label(sid) for sid in doc.subject_set]
                if doc.text.strip() and labels:
                    f.write(json.dumps({"text": doc.text, "subjects": labels}, ensure_ascii=False) + "\n")

    def _load_examples(self, n: int) -> list[Example]:
        if n <= 0 or not os.path.exists(self._examples_path()):
            return []
        with open(self._examples_path(), encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        return [Example(r["text"], r["subjects"]) for r in rows[-n:]]

    # ---- 推荐 ----

    def _client(self, params: dict[str, Any]) -> ChatClient:
        cache = None
        if annif.util.boolean(params["cache"]):
            os.makedirs(self.datadir, exist_ok=True)
            cache = os.path.join(self.datadir, self.CACHE_FILE)
        return ChatClient(
            endpoint=params["endpoint"], model=params["model"], api_key_env=params["api_key_env"],
            temperature=float(params["temperature"]), max_tokens=int(params["max_tokens"]),
            timeout=float(params["timeout"]), cache_path=cache,
            extra_body={"thinking": {"type": params["thinking"]}} if params["thinking"] else None,
        )

    def _rerank_one(self, doc: Document, source_result, params, client, examples
                    ) -> tuple[list[SubjectSuggestion], bool]:
        """返回 (推荐, 是否由大模型重排)；回退时第二项为 False。"""
        items = [(s.subject_id, self._label(s.subject_id), s.score) for s in source_result]
        candidates = make_candidates(items, int(params["candidates"]))
        if not candidates:
            return [], True
        fallback = [SubjectSuggestion(subject_id=c.subject_id, score=c.score) for c in candidates]
        try:
            messages = build_messages(doc.text, candidates, int(params["select"]),
                                      examples, int(params["max_chars"]))
            picks = parse_response(client.complete(messages), {c.key for c in candidates})
        except Exception as err:  # 网络、超时、回复格式错误等，一律回退
            self.debug(f"大模型重排失败，返回来源排序：{err}")
            return fallback, False
        if not picks:
            self.debug("大模型没有选出任何候选，返回来源排序")
            return fallback, False
        merged = merge(candidates, picks, float(params["blend"]), params["mode"])
        return [SubjectSuggestion(subject_id=sid, score=score) for sid, score in merged], True

    def _suggest_batch(self, documents: list[Document], params: dict[str, Any]) -> SuggestionBatch:
        sources = annif.util.parse_sources(params["sources"])
        by_source = self._suggest_with_sources(documents, sources)
        base = self._merge_source_batches(by_source, sources, {"limit": params["candidates"]})

        client = self._client(params)
        examples = self._load_examples(int(params["examples"]))
        with ThreadPoolExecutor(max_workers=max(1, int(params["concurrency"]))) as pool:
            outcomes = list(pool.map(
                lambda i: self._rerank_one(documents[i], base[i], params, client, examples),
                range(len(documents)),
            ))
        failed = sum(1 for _, ok in outcomes if not ok)
        if failed:
            self.warning(f"本批 {len(documents)} 篇中 {failed} 篇大模型重排失败，已回退为来源排序"
                         "（用 --verbosity DEBUG 查看原因）")
        return SuggestionBatch.from_sequence([r for r, _ in outcomes], self.project.subjects,
                                             limit=int(params["limit"]))
