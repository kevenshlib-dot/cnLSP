"""OpenAI 兼容的 chat/completions 客户端，带可选的 SQLite 缓存。

适用于本地 Ollama（http://localhost:11434/v1）、vLLM、LM Studio，以及提供 OpenAI
兼容接口的云端服务。API 密钥只从环境变量读取，不写进配置文件。
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time

import requests


class LLMError(RuntimeError):
    pass


class ChatClient:
    def __init__(self, endpoint: str, model: str, api_key_env: str | None = None,
                 temperature: float = 0.0, max_tokens: int = 512, timeout: float = 120,
                 retries: int = 1, cache_path: str | None = None) -> None:
        self.url = endpoint.rstrip("/") + "/chat/completions"
        self.model = model
        self.api_key = os.environ.get(api_key_env) if api_key_env else None
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        self.cache_path = cache_path

    def _cache_key(self, messages: list[dict]) -> str:
        payload = json.dumps([self.model, self.temperature, messages], ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _cache(self) -> sqlite3.Connection:
        # 每次调用新开连接：后端可能在多进程、多线程里运行
        conn = sqlite3.connect(self.cache_path, timeout=30)
        conn.execute("CREATE TABLE IF NOT EXISTS replies (key TEXT PRIMARY KEY, content TEXT)")
        return conn

    def complete(self, messages: list[dict]) -> str:
        key = self._cache_key(messages)
        if self.cache_path:
            with self._cache() as conn:
                row = conn.execute("SELECT content FROM replies WHERE key = ?", (key,)).fetchone()
            if row:
                return row[0]

        content = self._post(messages)

        if self.cache_path:
            with self._cache() as conn:
                conn.execute("INSERT OR REPLACE INTO replies VALUES (?, ?)", (key, content))
        return content

    def _post(self, messages: list[dict]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {"model": self.model, "messages": messages,
                "temperature": self.temperature, "max_tokens": self.max_tokens}
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                resp = requests.post(self.url, json=body, headers=headers, timeout=self.timeout)
                if resp.status_code >= 500 or resp.status_code == 429:
                    raise LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"] or ""
            except (requests.RequestException, LLMError, KeyError, IndexError, ValueError) as err:
                last_error = err
                if attempt < self.retries:
                    time.sleep(1.0 * (attempt + 1))
        raise LLMError(f"LLM 调用失败：{last_error}")
