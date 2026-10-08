"""Protocol and capability contracts shared across Jarvis services.

This module is transport-neutral: it defines compatibility semantics without
depending on HTTP, FastAPI, Ollama, or any particular deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

AGENT_PROTOCOL_VERSION = 1
INFERENCE_PROTOCOL_VERSION = 1
EVENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProtocolRange:
    """A protocol version range accepted by a component."""

    minimum: int
    maximum: int

    def supports(self, version: int) -> bool:
        return self.minimum <= version <= self.maximum


@dataclass(frozen=True)
class CapabilityDescriptor:
    """A model/service capability advertised by a component."""

    name: str
    version: int = 1
    features: frozenset[str] = frozenset()

    def supports(self, required: Iterable[str]) -> bool:
        return set(required).issubset(self.features)


def compatible(
    local: ProtocolRange,
    remote: ProtocolRange,
    *,
    version: int | None = None,
) -> bool:
    """Return whether two protocol ranges have at least one compatible version."""

    if version is not None:
        return local.supports(version) and remote.supports(version)
    return max(local.minimum, remote.minimum) <= min(local.maximum, remote.maximum)


def require_features(
    capabilities: Mapping[str, object],
    required: Iterable[str],
) -> None:
    """Raise ValueError when advertised capabilities do not cover requirements."""

    raw_features = capabilities.get("features", ())
    advertised = (
        {str(item) for item in raw_features}
        if isinstance(raw_features, (list, tuple, set, frozenset))
        else set()
    )
    missing = sorted(set(required) - advertised)
    if missing:
        raise ValueError("Missing required capabilities: " + ", ".join(missing))
