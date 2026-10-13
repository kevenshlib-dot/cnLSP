import pytest

from annif_zh.llm import fake_server
from annif_zh.llm.client import ChatClient, LLMError
from annif_zh.llm.rerank import build_messages, make_candidates, parse_response


@pytest.fixture
def server():
    srv, handler = fake_server.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1", handler
    srv.shutdown()


def _messages():
    cands = make_candidates([(1, "柴油机", 0.5), (2, "排放", 0.4), (3, "护理", 0.3)], 3)
    return cands, build_messages("农用柴油机排放控制探讨", cands, select=5)


def test_complete_against_fake_server(server):
    endpoint, _ = server
    cands, msgs = _messages()
    reply = ChatClient(endpoint, "fake").complete(msgs)
    assert parse_response(reply, {c.key for c in cands}) == [("C1", 0.9), ("C2", 0.8)]


def test_cache_avoids_second_request(server, tmp_path):
    endpoint, handler = server
    client = ChatClient(endpoint, "fake", cache_path=str(tmp_path / "cache.sqlite3"))
    _, msgs = _messages()
    assert client.complete(msgs) == client.complete(msgs)
    assert handler.requests_seen == 1


def test_retry_then_success(server):
    endpoint, handler = server
    handler.fail_next = 1
    _, msgs = _messages()
    assert "subjects" in ChatClient(endpoint, "fake", retries=1).complete(msgs)
    assert handler.requests_seen == 2


def test_gives_up_after_retries(server):
    endpoint, handler = server
    handler.fail_next = 5
    with pytest.raises(LLMError):
        ChatClient(endpoint, "fake", retries=1).complete(_messages()[1])


def test_api_key_comes_from_environment(monkeypatch):
    monkeypatch.setenv("MY_TEST_KEY", "not-a-real-key")
    assert ChatClient("http://x/v1", "m", api_key_env="MY_TEST_KEY").api_key == "not-a-real-key"


def test_empty_reply_is_an_error_and_not_cached(server, tmp_path):
    endpoint, handler = server
    handler.empty_next = 1
    client = ChatClient(endpoint, "fake", retries=0, cache_path=str(tmp_path / "c.sqlite3"))
    _, msgs = _messages()
    with pytest.raises(LLMError, match="空回复"):
        client.complete(msgs)
    assert "subjects" in client.complete(msgs)      # 空回复没有进缓存，第二次重新请求
    assert handler.requests_seen == 2


def test_extra_body_is_sent_and_part_of_cache_key(server):
    endpoint, handler = server
    _, msgs = _messages()
    plain = ChatClient(endpoint, "fake")
    thinking_off = ChatClient(endpoint, "fake", extra_body={"thinking": {"type": "disabled"}})
    thinking_off.complete(msgs)
    assert handler.last_body["thinking"] == {"type": "disabled"}
    assert plain._cache_key(msgs) != thinking_off._cache_key(msgs)
