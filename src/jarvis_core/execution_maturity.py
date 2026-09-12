"""Shared contracts for observable execution, background work and steering."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import hashlib
import json

from .evidence import Evidence, EvidenceLedger


class ProcessStatus(str, Enum):
    RUNNING = "running"
    EXITED = "exited"
    TERMINATED = "terminated"
    FAILED = "failed"


@dataclass(frozen=True)
class ProcessHandle:
    id: str
    command: tuple[str, ...]
    status: ProcessStatus = ProcessStatus.RUNNING
    pid: int | None = None
    exit_code: int | None = None


class SteeringAction(str, Enum):
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    REDIRECT = "redirect"
    REWIND = "rewind"


@dataclass(frozen=True)
class SteeringCommand:
    action: SteeringAction
    instruction: str | None = None
    checkpoint_id: str | None = None


@dataclass(frozen=True)
class Checkpoint:
    id: str
    run_id: str
    label: str
    workspace_revision: str | None = None
    conversation_revision: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def execution_evidence(
    ledger: EvidenceLedger,
    *,
    claim: str,
    kind: str,
    reference: str,
    output: str | None = None,
    path: str | None = None,
    verified: bool = True,
) -> Evidence:
    """Record a deterministic observation and return its evidence identity.

    Consumers call this at the boundary where an actual command/test/tool
    observation becomes trustworthy evidence; model prose never enters here.
    """
    digest = None
    if output is not None:
        digest = hashlib.sha256(output.encode("utf-8", errors="replace")).hexdigest()
    evidence = Evidence(
        claim=claim,
        path=path or reference,
        digest=digest,
        confidence=1.0 if verified else 0.0,
    )
    ledger.add(evidence)
    return evidence


def checkpoint_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()
