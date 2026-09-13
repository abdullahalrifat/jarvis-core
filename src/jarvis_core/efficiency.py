"""Provider-neutral token and context efficiency primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .context import compact_messages
from .quality import TaskAnalysis
from .reliability import (
    ContextItem,
    CompiledContext,
    compile_context,
    escalation_policy,
)
from .tokens import Usage, estimate_tokens


@dataclass(frozen=True)
class ModelPricing:
    """USD per million tokens for one provider/model route."""

    input_per_million: float = 0.0
    output_per_million: float = 0.0
    cached_input_per_million: float = 0.0
    cache_write_per_million: float = 0.0

    def cost(
        self,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_input_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> float:
        uncached = max(0, input_tokens - cached_input_tokens)
        return (
            uncached * self.input_per_million
            + max(0, cached_input_tokens) * self.cached_input_per_million
            + max(0, cache_write_tokens) * self.cache_write_per_million
            + max(0, output_tokens) * self.output_per_million
        ) / 1_000_000


@dataclass(frozen=True)
class RouteBudget:
    """Hard USD guard for a metered route."""

    monthly_usd: float = 50.0
    used_usd: float = 0.0

    def permits(self, estimated_usd: float) -> bool:
        return self.used_usd + max(0.0, estimated_usd) <= self.monthly_usd

    def after(self, actual_usd: float) -> "RouteBudget":
        return RouteBudget(self.monthly_usd, self.used_usd + max(0.0, actual_usd))


@dataclass(frozen=True)
class ContextBudget:
    """Bounded context categories so one noisy source cannot consume the window."""

    total_tokens: int = 24_000
    stable_tokens: int = 6_000
    state_tokens: int = 4_000
    evidence_tokens: int = 8_000
    history_tokens: int = 4_000

    def __post_init__(self) -> None:
        values = (
            self.total_tokens,
            self.stable_tokens,
            self.state_tokens,
            self.evidence_tokens,
            self.history_tokens,
        )
        if min(values) < 0 or sum(values[1:]) > self.total_tokens:
            raise ValueError("invalid context token budgets")


@dataclass
class AgentState:
    """Small state ledger used to avoid repeating exploration and failures."""

    inspected_files: set[str] = field(default_factory=set)
    executed_commands: set[str] = field(default_factory=set)
    failed_fingerprints: set[str] = field(default_factory=set)
    decisions: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)

    def remember_file(self, path: str) -> bool:
        value = path.strip()
        if not value or value in self.inspected_files:
            return False
        self.inspected_files.add(value)
        return True

    def remember_command(self, command: str) -> bool:
        value = command.strip()
        if not value or value in self.executed_commands:
            return False
        self.executed_commands.add(value)
        return True

    def remember_failure(self, fingerprint: str) -> bool:
        value = fingerprint.strip()
        if not value or value in self.failed_fingerprints:
            return False
        self.failed_fingerprints.add(value)
        return True

    def as_context(self) -> str:
        return (
            "Already inspected files: "
            + ", ".join(sorted(self.inspected_files))
            + "\nAlready executed commands: "
            + ", ".join(sorted(self.executed_commands))
            + "\nKnown failure fingerprints: "
            + ", ".join(sorted(self.failed_fingerprints))
            + "\nDecisions: "
            + " | ".join(self.decisions[-8:])
            + "\nObservations: "
            + " | ".join(self.observations[-8:])
        )


@dataclass(frozen=True)
class CompiledAgentContext:
    """Compiled context plus the number of historical tokens removed."""

    compiled: CompiledContext
    messages: tuple[dict[str, Any], ...]
    compacted_tokens_saved: int = 0

    @property
    def token_count(self) -> int:
        return self.compiled.total_tokens


def build_context(
    items: Iterable[ContextItem],
    *,
    budget: ContextBudget | None = None,
    messages: list[dict[str, Any]] | None = None,
    keep_recent: int = 4,
) -> CompiledAgentContext:
    """Deduplicate/rank context and compact old messages before model invocation."""
    budget = budget or ContextBudget()
    compiled = compile_context(items, budget.total_tokens)
    compacted = list(messages or [])
    saved = 0
    if compacted:
        compacted, saved = compact_messages(
            compacted,
            keep_recent=keep_recent,
            max_summary_chars=max(1024, budget.state_tokens * 4),
        )
    return CompiledAgentContext(compiled, tuple(compacted), saved)


def estimate_request_tokens(
    *,
    task: str,
    context: CompiledAgentContext,
    tools: Iterable[Mapping[str, Any]] = (),
) -> int:
    """Estimate the complete request, including context and tool schemas."""
    return (
        estimate_tokens(task)
        + estimate_tokens(context.compiled.render())
        + estimate_tokens(list(tools))
    )


def estimate_usage_cost(usage: Usage, pricing: ModelPricing) -> float:
    return pricing.cost(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cached_input_tokens=usage.cached_input_tokens,
    )


def choose_route(
    analysis: TaskAnalysis,
    *,
    uncertainty: float = 0.0,
    tool_failures: int = 0,
    conflicting_evidence: bool = False,
    retrieval_confidence: float = 1.0,
) -> str:
    """Return cheap/strong/expert without coupling Core to a model vendor."""
    return escalation_policy(
        complexity=analysis.complexity,
        uncertainty=uncertainty,
        risk=analysis.risk,
        tool_failures=tool_failures,
        conflicting_evidence=conflicting_evidence,
        retrieval_confidence=retrieval_confidence,
    ).tier
