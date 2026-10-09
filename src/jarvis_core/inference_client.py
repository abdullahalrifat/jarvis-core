"""Shared client for the Jarvis OpenAI-compatible inference gateway.

This module owns endpoint configuration, authentication, HTTP error handling,
model discovery, completion/streaming and embedding protocol behavior. It uses
only the Python standard library so both the Jarvis CLI and AI Stack can share
the same implementation without coupling Core to either application.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 120.0
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_ERROR_BYTES = 16 * 1024


class InferenceClientError(RuntimeError):
    """A transport or protocol error returned by the inference gateway."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.retryable = retryable


@dataclass(frozen=True)
class InferenceConfig:
    """Connection settings shared by every inference consumer."""

    base_url: str
    api_key: str = ""
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    user_agent: str = "jarvis-agent-core"

    def __post_init__(self) -> None:
        normalized = self.base_url.strip().rstrip("/")
        if not normalized:
            raise ValueError("Inference base_url is required")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("Inference base_url must use http:// or https://")
        if self.timeout <= 0:
            raise ValueError("Inference timeout must be positive")
        object.__setattr__(self, "base_url", normalized)

    @classmethod
    def from_env(
        cls,
        *,
        base_url_env: str = "INFERENCE_BASE_URL",
        api_key_env: str = "INFERENCE_API_KEY",
        timeout_env: str = "INFERENCE_TIMEOUT_SECONDS",
        user_agent: str = "jarvis-agent-core",
    ) -> "InferenceConfig":
        """Load the canonical gateway configuration from environment variables."""
        base_url = os.getenv(base_url_env, "").strip()
        if not base_url:
            base_url = os.getenv("JARVIS_BASE_URL", "").strip()
        api_key = os.getenv(api_key_env, "").strip()
        if not api_key:
            api_key = os.getenv("JARVIS_API_KEY", "").strip()
        timeout_value = os.getenv(timeout_env, str(DEFAULT_TIMEOUT_SECONDS))
        try:
            timeout = float(timeout_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{timeout_env} must be a positive number") from exc
        return cls(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            user_agent=user_agent,
        )

    def headers(self, *, accept: str = "application/json") -> dict[str, str]:
        """Return standard gateway headers without mutating shared state."""
        headers = {
            "Accept": accept,
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def endpoint(self, path: str) -> str:
        """Build an endpoint URL relative to the configured API base URL."""
        return f"{self.base_url}/{path.lstrip('/')}"


class InferenceClient:
    """Dependency-free client for the versioned Jarvis inference API.

    The configured base URL should include the API prefix, usually
    http://inference-host:8080/v1. The client intentionally does not retry
    requests: retrying an inference timeout can duplicate expensive model work.
    """

    def __init__(self, config: InferenceConfig, *, opener=urlopen) -> None:
        self.config = config
        self._opener = opener

    @classmethod
    def from_env(cls, **config_kwargs: Any) -> "InferenceClient":
        """Create a client from the shared environment-variable contract."""
        return cls(InferenceConfig.from_env(**config_kwargs))

    def list_models(self) -> list[dict[str, Any]]:
        """Return the gateway's OpenAI-compatible model catalog."""
        payload = self._request("GET", "models")
        data = payload.get("data")
        if not isinstance(data, list):
            raise InferenceClientError("Inference /models response has no data list")
        return [item for item in data if isinstance(item, dict)]

    def capabilities(self) -> dict[str, Any]:
        """Return the gateway's capability and protocol declaration."""
        payload = self._request("GET", "capabilities")
        if not isinstance(payload, dict):
            raise InferenceClientError("Inference capabilities response is not an object")
        return payload

    def complete(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]] | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Create one non-streaming chat completion."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [dict(message) for message in messages],
            "stream": False,
        }
        if tools is not None:
            payload["tools"] = [dict(tool) for tool in tools]
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(options)
        return self._request("POST", "chat/completions", payload, timeout=timeout)

    def stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]] | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        **options: Any,
    ) -> Iterator[dict[str, Any]]:
        """Yield decoded OpenAI-compatible server-sent events."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [dict(message) for message in messages],
            "stream": True,
        }
        if tools is not None:
            payload["tools"] = [dict(tool) for tool in tools]
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(options)
        request = Request(
            self.config.endpoint("chat/completions"),
            data=json.dumps(payload).encode("utf-8"),
            headers=self.config.headers(accept="text/event-stream"),
            method="POST",
        )
        try:
            with self._opener(request, timeout=timeout or self.config.timeout) as response:
                total_bytes = 0
                for line in response:
                    total_bytes += len(line)
                    if total_bytes > MAX_RESPONSE_BYTES:
                        raise InferenceClientError(
                            "Inference stream exceeded the response size limit"
                        )
                    if not line.startswith(b"data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    if data == b"[DONE]":
                        return
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError as exc:
                        raise InferenceClientError(
                            "Inference endpoint returned invalid SSE JSON"
                        ) from exc
                    if isinstance(event, dict):
                        yield event
        except HTTPError as exc:
            detail = exc.read(MAX_ERROR_BYTES).decode(errors="replace")
            raise self._http_error(exc, detail) from exc
        except (URLError, OSError, TimeoutError) as exc:
            raise InferenceClientError(
                f"Could not reach inference endpoint: {exc}", retryable=True
            ) from exc

    def embeddings(
        self,
        *,
        model: str,
        inputs: str | Sequence[str],
        timeout: float | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Create embeddings through the same gateway and authentication contract."""
        payload: dict[str, Any] = {"model": model, "input": inputs}
        payload.update(options)
        return self._request("POST", "embeddings", payload, timeout=timeout)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.config.endpoint(path),
            data=body,
            headers=self.config.headers(),
            method=method,
        )
        try:
            with self._opener(request, timeout=timeout or self.config.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                request_id = response.headers.get("X-Request-ID")
        except HTTPError as exc:
            detail = exc.read(MAX_ERROR_BYTES).decode(errors="replace")
            raise self._http_error(exc, detail) from exc
        except (URLError, OSError, TimeoutError) as exc:
            raise InferenceClientError(
                f"Could not reach inference endpoint: {exc}", retryable=True
            ) from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise InferenceClientError("Inference response exceeded the response size limit")
        try:
            result = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InferenceClientError("Inference endpoint returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise InferenceClientError("Inference endpoint returned a non-object response")
        if request_id and "request_id" not in result:
            result["request_id"] = request_id
        return result

    @staticmethod
    def _http_error(exc: HTTPError, detail: str) -> InferenceClientError:
        retryable = exc.code in {408, 429, 500, 502, 503, 504}
        request_id = exc.headers.get("X-Request-ID") if exc.headers else None
        return InferenceClientError(
            f"Inference endpoint returned HTTP {exc.code}: {detail}",
            status_code=exc.code,
            request_id=request_id,
            retryable=retryable,
        )
