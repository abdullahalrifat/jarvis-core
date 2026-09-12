"""Provider-neutral model contracts shared by Jarvis applications.

The core package deliberately contains no provider SDK dependencies. Concrete
providers (Anthropic, Ollama, OpenAI-compatible gateways, etc.) live in the
application/infrastructure layers and implement these contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


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
