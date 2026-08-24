"""Shared v0.8 autonomous-engineering runtime contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
import secrets
from typing import Any, Iterable


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
    ExecutionState.RETRYING: frozenset(
        {ExecutionState.QUEUED, ExecutionState.FAILED}
    ),
    ExecutionState.COMPLETED: frozenset(),
    ExecutionState.CANCELLED: frozenset(),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.TIMED_OUT: frozenset(
        {ExecutionState.RETRYING, ExecutionState.FAILED}
    ),
}


def can_transition(current: str | ExecutionState, target: str | ExecutionState) -> bool:
    return ExecutionState(target) in _ALLOWED_TRANSITIONS[ExecutionState(current)]


def require_transition(current: str | ExecutionState, target: str | ExecutionState) -> None:
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
    candidate = (
        after.astimezone(timezone.utc).replace(second=0, microsecond=0)
        + timedelta(minutes=1)
    )
    for _ in range(limit_minutes):
        if cron_matches(expression, candidate):
            return candidate
        candidate += timedelta(minutes=1)
    raise ValueError("cron has no occurrence within search horizon")
