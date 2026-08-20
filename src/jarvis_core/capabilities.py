"""Model capability profiles and deterministic task routing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ModelCapabilities:
    tool_calling: bool = False
    structured_output: bool = False
    vision: bool = False
    context_tokens: int = 0
    max_output_tokens: int = 0
    first_token_ms: float | None = None
    tokens_per_second: float | None = None
    tool_success_rate: float | None = None

    def supports(self, required: Iterable[str]) -> bool:
        for name in required:
            if name == "long_context" and self.context_tokens < 32_000:
                return False
            if name != "long_context" and not bool(getattr(self, name, False)):
                return False
        return True


@dataclass(frozen=True)
class ModelProfile:
    name: str
    provider: str
    model: str
    base_url: str
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    priority: int = 0
    enabled: bool = True
    api_key_env: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "capabilities": asdict(self.capabilities)}


class CapabilityRegistry:
    def __init__(self, profiles: Iterable[ModelProfile] = ()) -> None:
        self._profiles = {profile.name: profile for profile in profiles}

    def add(self, profile: ModelProfile) -> None:
        self._profiles[profile.name] = profile

    def list(self) -> list[ModelProfile]:
        return sorted(self._profiles.values(), key=lambda item: item.name)

    def select(
        self,
        *,
        required: Iterable[str] = (),
        preferred: str | None = None,
    ) -> ModelProfile:
        if preferred and preferred != "auto":
            profile = self._profiles.get(preferred)
            if profile is None or not profile.enabled:
                raise LookupError(f"model profile is unavailable: {preferred}")
            if not profile.capabilities.supports(required):
                raise LookupError(
                    f"model profile lacks required capabilities: {preferred}"
                )
            return profile
        candidates = [
            profile
            for profile in self._profiles.values()
            if profile.enabled and profile.capabilities.supports(required)
        ]
        if not candidates:
            raise LookupError("no enabled model satisfies the required capabilities")
        return max(
            candidates,
            key=lambda item: (
                item.priority,
                item.capabilities.tool_success_rate or 0.0,
                item.capabilities.tokens_per_second or 0.0,
                -(item.capabilities.first_token_ms or float("inf")),
                item.name,
            ),
        )
