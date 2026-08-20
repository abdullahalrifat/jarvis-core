"""Deterministic quality gates and adaptive multi-model routing contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class Scope(str, Enum):
    SINGLE_FILE = "single_file"
    MULTI_FILE = "multi_file"
    MULTI_MODULE = "multi_module"
    REPOSITORY = "repository"


@dataclass(frozen=True)
class TaskAnalysis:
    complexity: float
    risk: float
    scope: Scope = Scope.SINGLE_FILE
    requires_write: bool = False
    requires_web: bool = False
    verification: tuple[str, ...] = ()
    suggested_roles: tuple[str, ...] = ("implementer",)

    def __post_init__(self) -> None:
        if not 0 <= self.complexity <= 1 or not 0 <= self.risk <= 1:
            raise ValueError("complexity and risk must be between zero and one")

    @property
    def needs_multi_agent(self) -> bool:
        return self.complexity >= 0.55 or self.risk >= 0.45 or self.scope in {
            Scope.MULTI_MODULE,
            Scope.REPOSITORY,
        }

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "TaskAnalysis":
        roles = tuple(str(item) for item in value.get("suggested_roles", ()))
        if not roles:
            roles = ("implementer",)
        return cls(
            complexity=float(value.get("complexity", 0.5)),
            risk=float(value.get("risk", 0.5)),
            scope=Scope(str(value.get("scope", Scope.SINGLE_FILE.value))),
            requires_write=bool(value.get("requires_write", False)),
            requires_web=bool(value.get("requires_web", False)),
            verification=tuple(str(item) for item in value.get("verification", ())),
            suggested_roles=roles,
        )


@dataclass(frozen=True)
class RouteCandidate:
    profile: str
    model: str
    provider: str
    quality: float
    tool_success: float
    structured_success: float
    latency: float
    cost: float
    roles: tuple[str, ...] = ()

    def score(self) -> float:
        return (
            0.40 * self.quality
            + 0.25 * self.tool_success
            + 0.15 * self.structured_success
            - 0.10 * self.latency
            - 0.10 * self.cost
        )


@dataclass(frozen=True)
class RoleRoute:
    role: str
    profile: str
    model: str
    provider: str
    score: float


def route_roles(
    roles: Iterable[str], candidates: Iterable[RouteCandidate], *, diverse: bool = True
) -> tuple[RoleRoute, ...]:
    available = tuple(candidates)
    if not available:
        raise LookupError("no route candidates")
    selected: list[RoleRoute] = []
    used_models: set[str] = set()
    for role in roles:
        eligible = [item for item in available if not item.roles or role in item.roles]
        if not eligible:
            eligible = list(available)
        ranked = sorted(eligible, key=lambda item: item.score(), reverse=True)
        choice = next(
            (item for item in ranked if not diverse or item.model not in used_models),
            ranked[0],
        )
        used_models.add(choice.model)
        selected.append(
            RoleRoute(
                role=role,
                profile=choice.profile,
                model=choice.model,
                provider=choice.provider,
                score=choice.score(),
            )
        )
    return tuple(selected)


class ProofKind(str, Enum):
    FILE = "file"
    MUTATION = "mutation"
    COMMAND = "command"
    TEST = "test"
    SOURCE = "source"


@dataclass(frozen=True)
class ClaimProof:
    claim: str
    kind: ProofKind
    reference: str
    verified: bool = True
    digest: str | None = None


@dataclass(frozen=True)
class CompletionRequirement:
    claim: str
    accepted_kinds: tuple[ProofKind, ...]


@dataclass(frozen=True)
class CompletionAudit:
    passed: bool
    missing: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()


class EvidenceGate:
    """Reject completion claims that lack independently recorded proof."""

    def audit(
        self,
        requirements: Iterable[CompletionRequirement],
        proofs: Iterable[ClaimProof],
    ) -> CompletionAudit:
        proof_list = tuple(proofs)
        missing: list[str] = []
        rejected: list[str] = []
        for requirement in requirements:
            matches = [item for item in proof_list if item.claim == requirement.claim]
            if not matches:
                missing.append(requirement.claim)
                continue
            if not any(
                item.verified
                and bool(item.reference.strip())
                and item.kind in requirement.accepted_kinds
                for item in matches
            ):
                rejected.append(requirement.claim)
        return CompletionAudit(
            not missing and not rejected, tuple(missing), tuple(rejected)
        )


@dataclass(frozen=True)
class AdaptivePlan:
    parallel_exploration: bool
    implementation_owners: int
    independent_verifier: bool
    roles: tuple[str, ...]


def adaptive_plan(analysis: TaskAnalysis) -> AdaptivePlan:
    if not analysis.needs_multi_agent:
        return AdaptivePlan(False, 1, False, ("implementer",))
    roles = list(analysis.suggested_roles)
    for required in ("explorer", "implementer", "verifier"):
        if required not in roles:
            roles.append(required)
    if analysis.risk >= 0.45 and "risk" not in roles:
        roles.append("risk")
    return AdaptivePlan(True, 1, True, tuple(roles))


def stable_cache_key(namespace: str, value: Any, *, version: str = "1") -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{namespace}:{version}:{payload}".encode()).hexdigest()


@dataclass
class QualityMetrics:
    task_success: list[float] = field(default_factory=list)
    latency_ms: list[float] = field(default_factory=list)
    input_tokens: list[int] = field(default_factory=list)
    output_tokens: list[int] = field(default_factory=list)
    tool_failures: list[int] = field(default_factory=list)

    def record(
        self,
        *,
        success: bool,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        tool_failures: int = 0,
    ) -> None:
        self.task_success.append(1.0 if success else 0.0)
        self.latency_ms.append(max(0.0, latency_ms))
        self.input_tokens.append(max(0, input_tokens))
        self.output_tokens.append(max(0, output_tokens))
        self.tool_failures.append(max(0, tool_failures))

    def summary(self) -> dict[str, float]:
        count = len(self.task_success)
        if not count:
            return {
                "runs": 0.0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_tokens": 0.0,
                "avg_tool_failures": 0.0,
            }
        return {
            "runs": float(count),
            "success_rate": sum(self.task_success) / count,
            "avg_latency_ms": sum(self.latency_ms) / count,
            "avg_tokens": (sum(self.input_tokens) + sum(self.output_tokens)) / count,
            "avg_tool_failures": sum(self.tool_failures) / count,
        }
