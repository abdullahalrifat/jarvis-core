"""Shared v0.8 autonomous-engineering runtime contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
import secrets
from typing import Any, Iterable, Mapping


class ExecutionState(str, Enum):
    QUEUED = "queued"
    LEASED = "leased"
    PREPARING = "preparing_workspace"
    RUNNING = "running"
    VERIFYING = "verifying"
    UPLOADING = "uploading_result"
    COMPLETED = "completed"
    LEASE_LOST = "lease_lost"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


_ALLOWED_TRANSITIONS: dict[ExecutionState, frozenset[ExecutionState]] = {
    ExecutionState.QUEUED: frozenset({ExecutionState.LEASED, ExecutionState.CANCELLED}),
    ExecutionState.LEASED: frozenset(
        {
            ExecutionState.PREPARING,
            ExecutionState.LEASE_LOST,
            ExecutionState.CANCEL_REQUESTED,
        }
    ),
    ExecutionState.PREPARING: frozenset(
        {
            ExecutionState.RUNNING,
            ExecutionState.FAILED,
            ExecutionState.LEASE_LOST,
            ExecutionState.CANCEL_REQUESTED,
        }
    ),
    ExecutionState.RUNNING: frozenset(
        {
            ExecutionState.VERIFYING,
            ExecutionState.FAILED,
            ExecutionState.LEASE_LOST,
            ExecutionState.CANCEL_REQUESTED,
            ExecutionState.TIMED_OUT,
        }
    ),
    ExecutionState.VERIFYING: frozenset(
        {
            ExecutionState.UPLOADING,
            ExecutionState.FAILED,
            ExecutionState.LEASE_LOST,
            ExecutionState.CANCEL_REQUESTED,
        }
    ),
    ExecutionState.UPLOADING: frozenset(
        {ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.LEASE_LOST}
    ),
    ExecutionState.CANCEL_REQUESTED: frozenset(
        {ExecutionState.CANCELLED, ExecutionState.FAILED}
    ),
    ExecutionState.LEASE_LOST: frozenset(
        {ExecutionState.RETRYING, ExecutionState.FAILED}
    ),
    ExecutionState.RETRYING: frozenset({ExecutionState.QUEUED, ExecutionState.FAILED}),
    ExecutionState.COMPLETED: frozenset(),
    ExecutionState.CANCELLED: frozenset(),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.TIMED_OUT: frozenset(
        {ExecutionState.RETRYING, ExecutionState.FAILED}
    ),
}


def can_transition(current: str | ExecutionState, target: str | ExecutionState) -> bool:
    return ExecutionState(target) in _ALLOWED_TRANSITIONS[ExecutionState(current)]


def require_transition(
    current: str | ExecutionState, target: str | ExecutionState
) -> None:
    if not can_transition(current, target):
        raise ValueError(f"invalid execution transition: {current} -> {target}")


@dataclass(frozen=True)
class LeaseToken:
    task_id: str
    worker_id: str
    lease_id: str
    attempt: int
    expires_at: datetime

    @classmethod
    def issue(
        cls, task_id: str, worker_id: str, attempt: int, lease_seconds: int
    ) -> "LeaseToken":
        return cls(
            task_id=task_id,
            worker_id=worker_id,
            lease_id=secrets.token_urlsafe(24),
            attempt=max(1, attempt),
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=max(1, lease_seconds)),
        )

    def expired(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(timezone.utc)) >= self.expires_at


class ProofKind(str, Enum):
    FILE_READ = "file_read"
    PATCH_APPLIED = "patch_applied"
    COMMAND = "command"
    TEST = "test"
    DIAGNOSTIC = "diagnostic"
    VERIFIER = "verifier"
    SOURCE = "source"
    APPROVAL = "approval"
    ROUTE = "route"


@dataclass(frozen=True)
class ProofRecord:
    kind: ProofKind
    subject: str
    status: str
    detail: str = ""
    digest: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        kind: ProofKind,
        subject: str,
        status: str,
        detail: str = "",
        **metadata: Any,
    ) -> "ProofRecord":
        payload = json.dumps(metadata, sort_keys=True, default=str)
        digest = hashlib.sha256(
            f"{kind.value}|{subject}|{status}|{detail}|{payload}".encode()
        ).hexdigest()
        return cls(kind, subject, status, detail[:8000], digest, dict(metadata))


@dataclass
class ExecutionProofLedger:
    records: list[ProofRecord] = field(default_factory=list)

    def add(self, record: ProofRecord) -> ProofRecord:
        if not any(existing.digest == record.digest for existing in self.records):
            self.records.append(record)
        return record

    def record(
        self,
        kind: ProofKind,
        subject: str,
        status: str,
        detail: str = "",
        **metadata: Any,
    ) -> ProofRecord:
        return self.add(ProofRecord.build(kind, subject, status, detail, **metadata))

    def successful_tests(self) -> int:
        return sum(
            1
            for item in self.records
            if item.kind is ProofKind.TEST and item.status == "passed"
        )

    def failed_tests(self) -> int:
        return sum(
            1
            for item in self.records
            if item.kind is ProofKind.TEST and item.status == "failed"
        )

    def verifier_passed(self) -> bool | None:
        rows = [item for item in self.records if item.kind is ProofKind.VERIFIER]
        if not rows:
            return None
        return all(item.status == "passed" for item in rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [
                {**asdict(item), "kind": item.kind.value} for item in self.records
            ]
        }


PROOF_SCHEMA_VERSION = 1
_HEX_DIGEST_LENGTH = 64


def _require_digest(value: str, field_name: str) -> None:
    if len(value) != _HEX_DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc


@dataclass(frozen=True)
class VerificationRecord:
    """One reproducible verification command and its bound output digest."""

    command: str
    status: str
    exit_code: int
    output_digest: str

    def validate(self) -> None:
        if not self.command.strip():
            raise ValueError("verification command is required")
        if self.status not in {"passed", "failed", "blocked"}:
            raise ValueError("verification status must be passed, failed, or blocked")
        if self.status == "passed" and self.exit_code != 0:
            raise ValueError("a passed verification must have exit_code 0")
        _require_digest(self.output_digest, "verification output_digest")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "VerificationRecord":
        record = cls(
            command=str(value.get("command") or ""),
            status=str(value.get("status") or ""),
            exit_code=int(value.get("exit_code", -1)),
            output_digest=str(value.get("output_digest") or ""),
        )
        record.validate()
        return record


@dataclass(frozen=True)
class ExecutionProof:
    """Versioned proof envelope fenced to one cloud execution attempt."""

    task_id: str
    lease_id: str
    attempt: int
    workspace_digest: str
    route: str
    model: str
    mutation_digest: str
    verifications: tuple[VerificationRecord, ...]
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    schema_version: int = PROOF_SCHEMA_VERSION

    def validate(
        self,
        *,
        task_id: str | None = None,
        lease_id: str | None = None,
        require_verified: bool = True,
    ) -> None:
        if self.schema_version != PROOF_SCHEMA_VERSION:
            raise ValueError(f"unsupported proof schema_version: {self.schema_version}")
        for name, value in (
            ("task_id", self.task_id),
            ("lease_id", self.lease_id),
            ("route", self.route),
            ("model", self.model),
        ):
            if not value.strip():
                raise ValueError(f"proof {name} is required")
        if task_id is not None and self.task_id != task_id:
            raise ValueError("proof task_id does not match the completed task")
        if lease_id is not None and self.lease_id != lease_id:
            raise ValueError("proof lease_id does not match the active lease")
        if self.attempt < 1:
            raise ValueError("proof attempt must be positive")
        _require_digest(self.workspace_digest, "workspace_digest")
        _require_digest(self.mutation_digest, "mutation_digest")
        for record in self.verifications:
            record.validate()
        for name, digest in self.artifact_hashes.items():
            if not name.strip():
                raise ValueError("artifact hash names cannot be empty")
            _require_digest(digest, f"artifact {name}")
        if require_verified and (
            not self.verifications
            or any(item.status != "passed" for item in self.verifications)
        ):
            raise ValueError("successful completion requires passing verifications")

    def to_dict(self) -> dict[str, Any]:
        self.validate(require_verified=False)
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "lease_id": self.lease_id,
            "attempt": self.attempt,
            "workspace_digest": self.workspace_digest,
            "route": self.route,
            "model": self.model,
            "mutation_digest": self.mutation_digest,
            "verifications": [asdict(item) for item in self.verifications],
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
        }

    @classmethod
    def from_dict(
        cls,
        value: Mapping[str, Any],
        *,
        task_id: str | None = None,
        lease_id: str | None = None,
        require_verified: bool = True,
    ) -> "ExecutionProof":
        if not isinstance(value, Mapping):
            raise ValueError("execution proof must be an object")
        raw_verifications = value.get("verifications")
        if not isinstance(raw_verifications, list):
            raise ValueError("proof verifications must be a list")
        raw_artifacts = value.get("artifact_hashes", {})
        if not isinstance(raw_artifacts, Mapping):
            raise ValueError("proof artifact_hashes must be an object")
        proof = cls(
            schema_version=int(value.get("schema_version", 0)),
            task_id=str(value.get("task_id") or ""),
            lease_id=str(value.get("lease_id") or ""),
            attempt=int(value.get("attempt", 0)),
            workspace_digest=str(value.get("workspace_digest") or ""),
            route=str(value.get("route") or ""),
            model=str(value.get("model") or ""),
            mutation_digest=str(value.get("mutation_digest") or ""),
            verifications=tuple(
                VerificationRecord.from_dict(item)
                for item in raw_verifications
                if isinstance(item, Mapping)
            ),
            artifact_hashes={str(k): str(v) for k, v in raw_artifacts.items()},
        )
        if len(proof.verifications) != len(raw_verifications):
            raise ValueError("every verification entry must be an object")
        proof.validate(
            task_id=task_id, lease_id=lease_id, require_verified=require_verified
        )
        return proof

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class PermissionAction(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass(frozen=True)
class PermissionRule:
    capability: str
    action: PermissionAction
    risk: str = "normal"


@dataclass(frozen=True)
class PermissionDecision:
    capability: str
    action: PermissionAction
    reason: str


def permission_decision(
    capability: str,
    rules: Iterable[PermissionRule],
    *,
    plan_mode: bool = False,
    mutation: bool = False,
) -> PermissionDecision:
    if plan_mode and mutation:
        return PermissionDecision(
            capability, PermissionAction.DENY, "plan mode is technically read-only"
        )
    for rule in rules:
        if rule.capability == capability or rule.capability == "*":
            return PermissionDecision(
                capability,
                rule.action,
                f"matched {rule.capability} ({rule.risk})",
            )
    if mutation:
        return PermissionDecision(
            capability,
            PermissionAction.ASK,
            "mutation requires explicit approval by default",
        )
    return PermissionDecision(
        capability,
        PermissionAction.ALLOW,
        "read-only capability allowed by default",
    )


def _field_values(
    expression: str,
    minimum: int,
    maximum: int,
    *,
    sunday_7: bool = False,
) -> set[int]:
    raw_maximum = 7 if sunday_7 else maximum
    values: set[int] = set()
    for raw in expression.split(","):
        part = raw.strip()
        if not part:
            raise ValueError("empty cron field item")
        step = 1
        base = part
        if "/" in part:
            base, step_raw = part.split("/", 1)
            step = int(step_raw)
            if step <= 0:
                raise ValueError("cron step must be positive")
        if base == "*":
            start, end = minimum, raw_maximum
        elif "-" in base:
            start, end = (int(item) for item in base.split("-", 1))
        else:
            start = end = int(base)
        if start > end or start < minimum or end > raw_maximum:
            raise ValueError("cron value/range outside field bounds")
        values.update(range(start, end + 1, step))
    if sunday_7:
        values = {0 if item == 7 else item for item in values}
    return values


def cron_matches(expression: str, value: datetime) -> bool:
    fields = expression.split()
    if len(fields) != 5:
        raise ValueError("cron must have 5 fields: minute hour day month weekday")
    minute, hour, dom, month, dow = fields
    dt = value.astimezone(timezone.utc)
    weekday = (dt.weekday() + 1) % 7
    if dt.minute not in _field_values(minute, 0, 59):
        return False
    if dt.hour not in _field_values(hour, 0, 23):
        return False
    if dt.month not in _field_values(month, 1, 12):
        return False
    dom_match = dt.day in _field_values(dom, 1, 31)
    dow_match = weekday in _field_values(dow, 0, 6, sunday_7=True)
    dom_wild = dom == "*"
    dow_wild = dow == "*"
    if dom_wild and dow_wild:
        return True
    if dom_wild:
        return dow_match
    if dow_wild:
        return dom_match
    return dom_match or dow_match


def next_cron(
    expression: str,
    after: datetime,
    *,
    limit_minutes: int = 60 * 24 * 366 * 2,
) -> datetime:
    candidate = after.astimezone(timezone.utc).replace(
        second=0, microsecond=0
    ) + timedelta(minutes=1)
    for _ in range(limit_minutes):
        if cron_matches(expression, candidate):
            return candidate
        candidate += timedelta(minutes=1)
    raise ValueError("cron has no occurrence within search horizon")
