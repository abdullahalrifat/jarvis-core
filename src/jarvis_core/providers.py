"""Provider-neutral model contracts and normalization helpers.

The core package contains only provider-independent data structures and small
normalization helpers. Provider SDKs, transports, credentials, retries and
endpoint-specific request/response handling remain outside Core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ModelRequest:
    """Provider-independent model invocation request."""

    messages: Sequence[dict[str, Any]]
    tools: Sequence[dict[str, Any]] = ()
    max_output_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelUsage:
    """Normalized usage information returned by a provider."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float | None = None


@dataclass(frozen=True)
class ToolCall:
    """Provider-independent tool call."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    """Provider-independent model response."""

    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    usage: ModelUsage = field(default_factory=ModelUsage)
    provider: str = ""
    model: str = ""
    raw: Any = None


class ModelProvider(Protocol):
    """Minimal interface implemented by every model backend."""

    provider: str
    model: str

    def complete(self, request: ModelRequest) -> ModelResponse: ...

    @property
    def last_usage(self) -> ModelUsage: ...


def normalize_usage(value: Mapping[str, Any] | None) -> ModelUsage:
    """Normalize common provider usage mappings without importing an SDK."""

    value = value or {}
    input_tokens = int(value.get("input_tokens", value.get("prompt_tokens", 0)) or 0)
    output_tokens = int(
        value.get("output_tokens", value.get("completion_tokens", 0)) or 0
    )
    total_tokens = int(value.get("total_tokens", input_tokens + output_tokens) or 0)
    estimated_cost = value.get("estimated_cost")
    if estimated_cost is not None:
        estimated_cost = float(estimated_cost)
    return ModelUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
    )


def normalize_tool_call(
    value: Mapping[str, Any],
    *,
    default_id: str = "tool-call",
) -> ToolCall:
    """Normalize a provider-neutral tool-call mapping."""

    function = value.get("function")
    if isinstance(function, Mapping):
        name = str(function.get("name") or "")
        arguments = function.get("arguments") or {}
    else:
        name = str(value.get("name") or "")
        arguments = value.get("arguments") or {}
    if not isinstance(arguments, Mapping):
        raise TypeError("tool call arguments must be a mapping")
    if not name:
        raise ValueError("tool call name is required")
    return ToolCall(
        id=str(value.get("id") or default_id),
        name=name,
        arguments=dict(arguments),
    )


def normalize_tool_calls(
    values: Sequence[Mapping[str, Any]] | None,
) -> tuple[ToolCall, ...]:
    """Normalize a sequence of provider tool-call mappings."""

    return tuple(
        normalize_tool_call(value, default_id=f"tool-call-{index}")
        for index, value in enumerate(values or (), start=1)
    )


def make_model_response(
    *,
    content: str = "",
    tool_calls: Sequence[ToolCall] = (),
    usage: ModelUsage | Mapping[str, Any] | None = None,
    provider: str = "",
    model: str = "",
    raw: Any = None,
) -> ModelResponse:
    """Build the canonical response while accepting raw usage mappings."""

    normalized_usage = (
        usage if isinstance(usage, ModelUsage) else normalize_usage(usage)
    )
    return ModelResponse(
        content=str(content or ""),
        tool_calls=tuple(tool_calls),
        usage=normalized_usage,
        provider=provider,
        model=model,
        raw=raw,
    )
