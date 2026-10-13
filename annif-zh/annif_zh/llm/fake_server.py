"""假的大模型服务，实现 OpenAI 兼容的 /v1/chat/completions，用于测试和离线演示。

规则：从提示词里读出原文和候选，挑出在原文中字面出现的候选（最多 select 个），
置信度从 0.9 起递减；一个都没有时选前 3 个。回复外面包一层 <think>…</think>，
模拟 Qwen3 等推理模型的输出，检验解析是否稳健。

    python -m annif_zh.llm.fake_server --port 8765
"""

from __future__ import annotations

import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CANDIDATE = re.compile(r"^(C\d+) (.+)$", re.M)
SELECT = re.compile(r"最多 (\d+) 个")


def fake_reply(prompt: str) -> str:
    # 示例里也有“示例文献：”，所以取候选列表之前最后一个“文献：”后面的内容
    text = prompt.split("候选主题词", 1)[0].rsplit("文献：", 1)[-1]
    candidates = CANDIDATE.findall(prompt)
    m = SELECT.search(prompt)
    select = int(m.group(1)) if m else 5
    chosen = [key for key, label in candidates if label in text][:select] or [k for k, _ in candidates[:3]]
    subjects = [{"id": key, "score": round(0.9 - 0.1 * i, 2)} for i, key in enumerate(chosen)]
    return "<think>先看原文，再对照候选。</think>\n" + json.dumps({"subjects": subjects}, ensure_ascii=False)


class Handler(BaseHTTPRequestHandler):
    requests_seen = 0
    fail_next = 0          # 测试用：接下来几次请求返回 500
    empty_next = 0         # 测试用：接下来几次请求返回空正文（模拟推理模型耗尽 max_tokens）

    def do_POST(self):  # noqa: N802
        if not self.path.endswith("/chat/completions"):
            self.send_error(404)
            return
        cls = type(self)
        cls.requests_seen += 1
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if cls.fail_next > 0:
            cls.fail_next -= 1
            self.send_error(500, "simulated failure")
            return
        prompt = body["messages"][-1]["content"]
        cls.last_body = body
        if cls.empty_next > 0:
            cls.empty_next -= 1
            content, finish = "", "length"
        else:
            content, finish = fake_reply(prompt), "stop"
        reply = {"choices": [{"message": {"role": "assistant", "content": content},
                              "finish_reason": finish}], "model": body.get("model")}
        data = json.dumps(reply, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def start(port: int = 0) -> tuple[ThreadingHTTPServer, type[Handler]]:
    """在后台线程启动服务，返回 (server, handler 类)。port=0 表示自动选空闲端口。"""
    handler = type("FakeHandler", (Handler,), {"requests_seen": 0, "fail_next": 0,
                                               "empty_next": 0, "last_body": None})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"fake LLM listening on http://{args.host}:{args.port}/v1")
    server.serve_forever()


if __name__ == "__main__":
    main()
