"""Provider-neutral capability and approval primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class Capability(str, Enum):
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    EXECUTE_COMMAND = "execute_command"
    NETWORK = "network"
    GIT_WRITE = "git_write"
    GIT_PUSH = "git_push"
    CREATE_PR = "create_pr"
    SECRETS = "secrets"


class ApprovalDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass(frozen=True)
class CapabilityPolicy:
    allowed: FrozenSet[Capability] = frozenset()
    approval_required: FrozenSet[Capability] = frozenset()

    def decide(self, capability: Capability) -> ApprovalDecision:
        if capability in self.approval_required:
            return ApprovalDecision.ASK
        if capability in self.allowed:
            return ApprovalDecision.ALLOW
        return ApprovalDecision.DENY


@dataclass(frozen=True)
class ApprovalRequest:
    capability: Capability
    reason: str
    scope: str = "task"


@dataclass(frozen=True)
class ApprovalResponse:
    request: ApprovalRequest
    decision: ApprovalDecision
    actor: str = "user"
