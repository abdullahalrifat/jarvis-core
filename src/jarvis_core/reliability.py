"""Deterministic v0.7 efficiency/reliability contracts.

These primitives deliberately avoid trusting model self-assessment. They are shared by
CLI and Server runtimes for context compilation, escalation, verification, retry,
impact analysis, failure memory, evidence confidence, patch minimization, and routing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class FailureClass(str, Enum):
    SYNTAX = "syntax"
    TEST = "test"
    TOOL_PROTOCOL = "tool_protocol"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    PERMISSION = "permission"
    RETRIEVAL = "retrieval"
    WRONG_SYMBOL = "wrong_symbol"
    API_COMPAT = "api_compat"
    REPEATED = "repeated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FailureSignature:
    kind: FailureClass
    fingerprint: str
    detail: str = ""
    tool: str | None = None
    model: str | None = None
    attempts: int = 1

    @classmethod
    def from_error(
        cls,
        text: str,
        *,
        tool: str | None = None,
        model: str | None = None,
        attempts: int = 1,
    ) -> "FailureSignature":
        lowered = text.casefold()
        if "syntaxerror" in lowered or "parse error" in lowered:
            kind = FailureClass.SYNTAX
        elif "assert" in lowered or "test failed" in lowered or "pytest" in lowered:
            kind = FailureClass.TEST
        elif "429" in lowered or "rate limit" in lowered:
            kind = FailureClass.RATE_LIMIT
        elif "tool" in lowered and ("schema" in lowered or "protocol" in lowered):
            kind = FailureClass.TOOL_PROTOCOL
        elif "permission" in lowered or "denied" in lowered:
            kind = FailureClass.PERMISSION
        elif "timeout" in lowered or "connection" in lowered or "network" in lowered:
            kind = FailureClass.NETWORK
        elif "symbol" in lowered and ("missing" in lowered or "wrong" in lowered):
            kind = FailureClass.WRONG_SYMBOL
        elif "compat" in lowered or "breaking" in lowered:
            kind = FailureClass.API_COMPAT
        else:
            kind = FailureClass.UNKNOWN
        normalized = " ".join(lowered.split())[:1000]
        fingerprint = hashlib.sha256(
            f"{kind.value}|{tool or ''}|{model or ''}|{normalized}".encode()
        ).hexdigest()[:24]
        return cls(kind, fingerprint, text[:4000], tool, model, max(1, attempts))


@dataclass(frozen=True)
class RetryDecision:
    action: str
    retry: bool
    escalate: bool = False
    backoff_seconds: float = 0.0
    reason: str = ""


def retry_policy(signature: FailureSignature) -> RetryDecision:
    if signature.attempts >= 3:
        return RetryDecision("escalate", False, True, reason="repeated failure budget exhausted")
    if signature.kind is FailureClass.RATE_LIMIT:
        return RetryDecision("fallback_or_backoff", True, backoff_seconds=2 ** signature.attempts)
    if signature.kind is FailureClass.TOOL_PROTOCOL:
        return RetryDecision("repair_message", True)
    if signature.kind in {FailureClass.SYNTAX, FailureClass.TEST, FailureClass.WRONG_SYMBOL}:
        return RetryDecision("inspect_and_repair", True)
    if signature.kind in {FailureClass.PERMISSION, FailureClass.API_COMPAT}:
        return RetryDecision("escalate", False, True)
    if signature.kind is FailureClass.NETWORK:
        return RetryDecision("fallback_provider", True, backoff_seconds=1.0)
    return RetryDecision("retry_once", signature.attempts < 2, signature.attempts >= 2)


@dataclass(frozen=True)
class PatchTarget:
    path: str
    symbols: tuple[str, ...] = ()
    expected_change: str = ""
    tests: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatchPlan:
    goal: str
    targets: tuple[PatchTarget, ...]
    rollback: str = "git restore changed files"
    risk: str = "normal"

    def permits(self, path: str, symbol: str | None = None) -> bool:
        for target in self.targets:
            if target.path != path:
                continue
            return not symbol or not target.symbols or symbol in target.symbols
        return False


@dataclass(frozen=True)
class ContextItem:
    kind: str
    key: str
    content: str
    relevance: float = 0.0
    tokens: int = 0
    digest: str = ""

    @classmethod
    def build(cls, kind: str, key: str, content: str, relevance: float = 0.0) -> "ContextItem":
        compact = content.strip()
        return cls(
            kind=kind,
            key=key,
            content=compact,
            relevance=max(0.0, min(1.0, relevance)),
            tokens=max(1, len(compact) // 4),
            digest=hashlib.sha256(compact.encode()).hexdigest(),
        )


@dataclass(frozen=True)
class CompiledContext:
    items: tuple[ContextItem, ...]
    token_budget: int
    total_tokens: int
    omitted: int

    def render(self) -> str:
        blocks = [f"[{item.kind}:{item.key} sha256={item.digest[:12]}]\n{item.content}" for item in self.items]
        return "\n\n".join(blocks)


def compile_context(items: Iterable[ContextItem], token_budget: int) -> CompiledContext:
    budget = max(256, token_budget)
    deduped: dict[str, ContextItem] = {}
    for item in items:
        current = deduped.get(item.digest)
        if current is None or item.relevance > current.relevance:
            deduped[item.digest] = item
    ranked = sorted(deduped.values(), key=lambda item: (item.relevance, -item.tokens), reverse=True)
    selected: list[ContextItem] = []
    used = 0
    for item in ranked:
        if used + item.tokens > budget:
            continue
        selected.append(item)
        used += item.tokens
    return CompiledContext(tuple(selected), budget, used, len(ranked) - len(selected))


@dataclass(frozen=True)
class SpeculationPolicy:
    enabled: bool
    candidates: int
    cancel_after_progress: float = 0.55
    reason: str = ""


def speculation_policy(*, complexity: float, uncertainty: float, risk: float, token_pressure: float) -> SpeculationPolicy:
    score = 0.45 * complexity + 0.35 * uncertainty + 0.20 * risk
    if token_pressure >= 0.85 or score < 0.48:
        return SpeculationPolicy(False, 1, reason="single path is more efficient")
    return SpeculationPolicy(True, 3 if score >= 0.78 and token_pressure < 0.55 else 2, reason="uncertainty justifies bounded parallel candidates")


@dataclass(frozen=True)
class EscalationDecision:
    tier: str
    require_independent_verifier: bool
    require_remote: bool
    reason: str


def escalation_policy(
    *,
    complexity: float,
    uncertainty: float,
    risk: float,
    tool_failures: int = 0,
    conflicting_evidence: bool = False,
    retrieval_confidence: float = 1.0,
) -> EscalationDecision:
    score = 0.35 * complexity + 0.30 * uncertainty + 0.25 * risk
    score += min(tool_failures, 3) * 0.08
    score += 0.15 if conflicting_evidence else 0.0
    score += max(0.0, 0.6 - retrieval_confidence) * 0.35
    if score < 0.42:
        return EscalationDecision("cheap", False, False, "low measured task difficulty")
    if score < 0.72:
        return EscalationDecision("strong", risk >= 0.55, False, "strong single agent with selective verification")
    return EscalationDecision("expert", True, risk >= 0.75 or tool_failures >= 2, "complex/risky task requires independent escalation")


@dataclass(frozen=True)
class EvidenceConfidence:
    score: float
    tests: float
    requirements: float
    verifier: float
    diagnostics: float
    assumptions: float


def evidence_confidence(
    *,
    tests_passed: int,
    tests_failed: int,
    requirements_verified: int,
    requirements_total: int,
    verifier_passed: bool | None,
    unresolved_diagnostics: int,
    unverified_assumptions: int,
) -> EvidenceConfidence:
    tests = tests_passed / max(1, tests_passed + tests_failed)
    requirements = requirements_verified / max(1, requirements_total)
    verifier = 1.0 if verifier_passed is True else 0.5 if verifier_passed is None else 0.0
    diagnostics = 1.0 / (1.0 + max(0, unresolved_diagnostics))
    assumptions = 1.0 / (1.0 + max(0, unverified_assumptions))
    score = 0.30 * tests + 0.30 * requirements + 0.20 * verifier + 0.12 * diagnostics + 0.08 * assumptions
    return EvidenceConfidence(score, tests, requirements, verifier, diagnostics, assumptions)


@dataclass(frozen=True)
class ImpactNode:
    key: str
    kind: str
    related: tuple[str, ...] = ()


class ImpactGraph:
    def __init__(self, nodes: Iterable[ImpactNode] = ()) -> None:
        self.nodes = {node.key: node for node in nodes}

    def impacted(self, changed: Iterable[str], max_depth: int = 3) -> tuple[str, ...]:
        reverse: dict[str, set[str]] = {}
        for node in self.nodes.values():
            for dep in node.related:
                reverse.setdefault(dep, set()).add(node.key)
        seen = set(changed)
        frontier = set(changed)
        for _ in range(max(0, max_depth)):
            nxt = {item for key in frontier for item in reverse.get(key, ())} - seen
            seen |= nxt
            frontier = nxt
            if not frontier:
                break
        return tuple(sorted(seen))

    def tests_for(self, changed: Iterable[str]) -> tuple[str, ...]:
        impacted = self.impacted(changed)
        return tuple(sorted(key for key in impacted if self.nodes.get(key) and self.nodes[key].kind == "test"))


@dataclass(frozen=True)
class FailureMemoryRecord:
    signature: FailureSignature
    task_category: str
    successful_recovery: str | None = None
    count: int = 1


class FailureMemory:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.records: dict[str, FailureMemoryRecord] = {}
        if self.path.is_file():
            self.load()

    def remember(self, record: FailureMemoryRecord) -> None:
        previous = self.records.get(record.signature.fingerprint)
        if previous:
            record = FailureMemoryRecord(
                record.signature,
                record.task_category,
                record.successful_recovery or previous.successful_recovery,
                previous.count + 1,
            )
        self.records[record.signature.fingerprint] = record
        self.save()

    def relevant(self, category: str, limit: int = 10) -> list[FailureMemoryRecord]:
        rows = [item for item in self.records.values() if item.task_category in {category, "*"}]
        return sorted(rows, key=lambda item: item.count, reverse=True)[:limit]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for record in self.records.values():
            row = asdict(record)
            row["signature"]["kind"] = record.signature.kind.value
            payload.append(row)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        for row in payload:
            sig = row["signature"]
            signature = FailureSignature(FailureClass(sig["kind"]), sig["fingerprint"], sig.get("detail", ""), sig.get("tool"), sig.get("model"), sig.get("attempts", 1))
            record = FailureMemoryRecord(signature, row["task_category"], row.get("successful_recovery"), row.get("count", 1))
            self.records[signature.fingerprint] = record


@dataclass(frozen=True)
class ToolArtifact:
    digest: str
    summary: str
    content: str


def compress_tool_result(content: str, *, max_chars: int = 6000) -> ToolArtifact:
    digest = hashlib.sha256(content.encode()).hexdigest()
    lines = content.splitlines()
    if len(content) <= max_chars:
        summary = content
    else:
        head = "\n".join(lines[:40])
        tail = "\n".join(lines[-40:])
        summary = f"{head}\n\n...[{len(content) - len(head) - len(tail)} chars omitted; sha256={digest}]...\n\n{tail}"
        summary = summary[:max_chars]
    return ToolArtifact(digest, summary, content)


def minimize_patch_paths(changed_paths: Sequence[str], required_paths: Iterable[str]) -> tuple[str, ...]:
    required = set(required_paths)
    return tuple(path for path in changed_paths if path in required)


@dataclass(frozen=True)
class VerifierEnvelope:
    task: str
    diff: str
    evidence: tuple[Mapping[str, Any], ...]
    tests: str

    def to_prompt(self) -> str:
        # Intentionally excludes implementer chain-of-thought, plans, and narrative.
        return json.dumps({"task": self.task, "diff": self.diff, "evidence": list(self.evidence), "tests": self.tests}, ensure_ascii=False)
