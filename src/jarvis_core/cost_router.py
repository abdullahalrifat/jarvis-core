"""Deterministic cost-aware routing for local-first agent execution.

This module contains no provider SDKs. It decides which tier should handle a
turn; the application maps tiers to concrete model profiles. The policy is
intentionally conservative: deterministic tools remain outside the model path,
local inference is the default, and repeated failures trigger escalation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class RouteTier(IntEnum):
    LOCAL = 0
    CHEAP = 1
    FRONTIER = 2


@dataclass(frozen=True)
class RouteModel:
    name: str
    tier: RouteTier
    input_per_million: float = 0.0
    cached_input_per_million: float = 0.0
    output_per_million: float = 0.0
    enabled: bool = True
    priority: int = 0

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, cached_tokens: int = 0
    ) -> float:
        uncached = max(0, input_tokens - cached_tokens)
        return (
            uncached * self.input_per_million
            + max(0, cached_tokens) * self.cached_input_per_million
            + max(0, output_tokens) * self.output_per_million
        ) / 1_000_000


@dataclass(frozen=True)
class RoutingSignals:
    """Evidence used by the router; all values are normalized to 0..1."""

    complexity: float = 0.0
    risk: float = 0.0
    uncertainty: float = 0.0
    retrieval_confidence: float = 1.0
    tool_failures: int = 0
    attempts: int = 0
    deterministic_only: bool = False
    external_evidence_required: bool = False
    security_sensitive: bool = False

    def score(self) -> float:
        value = (
            0.35 * _clamp(self.complexity)
            + 0.25 * _clamp(self.uncertainty)
            + 0.20 * _clamp(self.risk)
            + 0.10 * (1.0 - _clamp(self.retrieval_confidence))
            + 0.10 * min(max(self.tool_failures, 0), 3) / 3
        )
        return min(1.0, value)


@dataclass(frozen=True)
class RoutingDecision:
    tier: RouteTier
    reason: str
    max_attempts: int
    require_verification: bool


@dataclass(frozen=True)
class FailureBudget:
    """Maximum attempts before a tier must hand work to the next tier."""

    local: int = 2
    cheap: int = 2
    frontier: int = 3

    def limit(self, tier: RouteTier) -> int:
        return {
            RouteTier.LOCAL: self.local,
            RouteTier.CHEAP: self.cheap,
            RouteTier.FRONTIER: self.frontier,
        }[tier]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def choose_tier(signals: RoutingSignals) -> RoutingDecision:
    """Choose the minimum-cost tier that has enough evidence to proceed."""
    if signals.deterministic_only:
        return RoutingDecision(
            RouteTier.LOCAL, "deterministic work should bypass the LLM", 0, False
        )

    score = signals.score()
    if signals.security_sensitive or (
        signals.attempts >= 2 and signals.tool_failures >= 2
    ):
        return RoutingDecision(
            RouteTier.FRONTIER, "high-risk or repeated execution failure", 3, True
        )
    if (
        score >= 0.50
        or signals.external_evidence_required
        or signals.attempts >= 2
        or signals.tool_failures >= 2
    ):
        return RoutingDecision(
            RouteTier.CHEAP,
            "moderate/high difficulty or local failure budget reached",
            2,
            signals.risk >= 0.55,
        )
    return RoutingDecision(
        RouteTier.LOCAL, "local-first policy", 2, signals.risk >= 0.65
    )


def next_tier(
    current: RouteTier, *, success: bool, budget: FailureBudget, attempts: int
) -> RouteTier | None:
    """Return the next tier only after failure budget is exhausted."""
    if success or attempts < budget.limit(current):
        return current
    if current is RouteTier.LOCAL:
        return RouteTier.CHEAP
    if current is RouteTier.CHEAP:
        return RouteTier.FRONTIER
    return None


def select_model(
    models: tuple[RouteModel, ...],
    tier: RouteTier,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0,
    max_cost_usd: float | None = None,
) -> RouteModel:
    """Select an enabled model in a tier, preferring low cost then priority."""
    candidates = [m for m in models if m.enabled and m.tier == tier]
    if max_cost_usd is not None:
        candidates = [
            m
            for m in candidates
            if m.estimate_cost(input_tokens, output_tokens, cached_tokens)
            <= max_cost_usd
        ]
    if not candidates:
        raise LookupError(f"no enabled model available for tier: {tier.name.lower()}")
    return min(
        candidates,
        key=lambda m: (
            m.estimate_cost(input_tokens, output_tokens, cached_tokens),
            -m.priority,
            m.name,
        ),
    )
