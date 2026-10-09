import io
import json
from urllib.error import HTTPError

import pytest

from jarvis_core import InferenceClient, InferenceClientError, InferenceConfig


class FakeResponse:
    def __init__(self, body: bytes, *, headers=None, lines=None):
        self.body = body
        self.headers = headers or {}
        self.lines = lines or []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, limit=-1):
        return self.body[:limit]

    def __iter__(self):
        return iter(self.lines)


def test_config_normalizes_url_and_builds_auth_headers():
    config = InferenceConfig(
        base_url=" http://inference:8080/v1/ ",
        api_key="secret",
        timeout=15,
    )

    assert config.base_url == "http://inference:8080/v1"
    assert config.endpoint("/models") == "http://inference:8080/v1/models"
    assert config.headers()["Authorization"] == "Bearer secret"
    assert config.headers()["User-Agent"] == "jarvis-agent-core"


def test_config_rejects_invalid_url_and_timeout():
    with pytest.raises(ValueError, match="base_url"):
        InferenceConfig(base_url="")
    with pytest.raises(ValueError, match="http://"):
        InferenceConfig(base_url="inference:8080/v1")
    with pytest.raises(ValueError, match="positive"):
        InferenceConfig(base_url="http://inference/v1", timeout=0)


def test_config_loads_canonical_env_and_legacy_fallback(monkeypatch):
    monkeypatch.setenv("INFERENCE_BASE_URL", "http://inference:8080/v1")
    monkeypatch.setenv("INFERENCE_API_KEY", "primary")
    monkeypatch.setenv("INFERENCE_TIMEOUT_SECONDS", "42")
    config = InferenceConfig.from_env()

    assert config.base_url == "http://inference:8080/v1"
    assert config.api_key == "primary"
    assert config.timeout == 42

    monkeypatch.delenv("INFERENCE_BASE_URL")
    monkeypatch.delenv("INFERENCE_API_KEY")
    monkeypatch.setenv("JARVIS_BASE_URL", "http://legacy/v1")
    monkeypatch.setenv("JARVIS_API_KEY", "legacy")
    config = InferenceConfig.from_env()
    assert config.base_url == "http://legacy/v1"
    assert config.api_key == "legacy"


def test_list_models_uses_shared_endpoint_and_auth():
    captured = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse(
            b'{"object":"list","data":[{"id":"qwen3:1.7b"}]}',
            headers={"X-Request-ID": "req-123"},
        )

    client = InferenceClient(
        InferenceConfig("http://inference:8080/v1", "secret", 9),
        opener=opener,
    )
    assert client.list_models() == [{"id": "qwen3:1.7b"}]
    assert captured == {
        "url": "http://inference:8080/v1/models",
        "auth": "Bearer secret",
        "timeout": 9,
    }


def test_complete_serializes_openai_compatible_payload():
    captured = {}

    def opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(b'{"choices":[{"message":{"content":"ok"}}]}')

    client = InferenceClient(
        InferenceConfig("http://inference/v1", "key"), opener=opener
    )
    result = client.complete(
        model="qwen3:1.7b",
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"type": "function", "function": {"name": "search"}}],
        max_tokens=256,
        temperature=0,
    )

    request = captured["request"]
    assert request.full_url == "http://inference/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer key"
    assert captured["timeout"] == 120
    assert json.loads(request.data) == {
        "model": "qwen3:1.7b",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
        "tools": [{"type": "function", "function": {"name": "search"}}],
        "max_tokens": 256,
        "temperature": 0,
    }
    assert result["choices"][0]["message"]["content"] == "ok"


def test_stream_decodes_sse_and_stops_at_done():
    captured = {}

    def opener(request, timeout):
        captured["accept"] = request.get_header("Accept")
        return FakeResponse(
            b"",
            lines=[
                b": heartbeat\n",
                b'data: {"choices":[{"delta":{"content":"hello"}}]}\n',
                b"data: [DONE]\n",
                b'data: {"choices":[{"delta":{"content":"ignored"}}]}\n',
            ],
        )

    client = InferenceClient(InferenceConfig("http://inference/v1"), opener=opener)
    events = list(
        client.stream(model="qwen3:1.7b", messages=[{"role": "user", "content": "hi"}])
    )
    assert captured["accept"] == "text/event-stream"
    assert len(events) == 1
    assert events[0]["choices"][0]["delta"]["content"] == "hello"


def test_http_errors_expose_status_request_id_and_retryability():
    def opener(_request, timeout):
        raise HTTPError(
            "http://inference/v1/models",
            503,
            "unavailable",
            {"X-Request-ID": "req-503"},
            io.BytesIO(b'{"detail":"busy"}'),
        )

    client = InferenceClient(InferenceConfig("http://inference/v1"), opener=opener)
    with pytest.raises(InferenceClientError) as caught:
        client.list_models()

    assert caught.value.status_code == 503
    assert caught.value.request_id == "req-503"
    assert caught.value.retryable is True


def test_timeout_is_not_replayed_by_shared_inference_client():
    calls = []

    def opener(_request, timeout):
        calls.append(timeout)
        raise TimeoutError("read timed out after server may have accepted request")

    client = InferenceClient(
        InferenceConfig("http://inference/v1", timeout=3), opener=opener
    )
    with pytest.raises(InferenceClientError):
        client.complete(
            model="qwen3:1.7b", messages=[{"role": "user", "content": "hello"}]
        )
    assert calls == [3]


@pytest.mark.parametrize(
    ("status", "retryable"),
    [(408, False), (504, False), (429, True)],
)
def test_ambiguous_http_timeouts_are_not_retryable(status, retryable):
    def opener(_request, timeout):
        raise HTTPError(
            "http://inference/v1/models",
            status,
            "gateway response",
            {"X-Request-ID": f"req-{status}"},
            io.BytesIO(b'{"detail":"gateway response"}'),
        )

    client = InferenceClient(InferenceConfig("http://inference/v1"), opener=opener)
    with pytest.raises(InferenceClientError) as caught:
        client.list_models()
    assert caught.value.status_code == status
    assert caught.value.retryable is retryable


def test_closing_stream_releases_http_response_for_cancellation():
    class ClosableResponse(FakeResponse):
        def __init__(self):
            super().__init__(
                b"",
                lines=[
                    b'data: {"choices":[{"delta":{"content":"first"}}]}',
                    b'data: {"choices":[{"delta":{"content":"second"}}]}',
                ],
            )
            self.closed = False

        def __exit__(self, *_args):
            self.closed = True

    response = ClosableResponse()
    client = InferenceClient(
        InferenceConfig("http://inference/v1"),
        opener=lambda _request, timeout: response,
    )
    stream = client.stream(
        model="qwen3:1.7b", messages=[{"role": "user", "content": "hello"}]
    )
    next(stream)
    stream.close()
    assert response.closed
