"""Transactional change-review contracts shared by CLI and Server."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib


class ReviewState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    REVERTED = "reverted"


@dataclass
class ReviewHunk:
    path: str
    patch: str
    evidence: tuple[str, ...] = ()
    state: ReviewState = ReviewState.PENDING

    @property
    def id(self) -> str:
        return hashlib.sha256(f"{self.path}\0{self.patch}".encode()).hexdigest()[:16]


@dataclass
class ChangeTransaction:
    base_revision: str
    hunks: list[ReviewHunk]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    applied_revision: str | None = None
    reverted_at: str | None = None

    def approve(self, ids: set[str]) -> None:
        for hunk in self.hunks:
            if hunk.id in ids and hunk.state is ReviewState.PENDING:
                hunk.state = ReviewState.APPROVED

    def reject(self, ids: set[str]) -> None:
        for hunk in self.hunks:
            if hunk.id in ids and hunk.state is ReviewState.PENDING:
                hunk.state = ReviewState.REJECTED

    @property
    def approved_patch(self) -> str:
        return "\n".join(
            hunk.patch for hunk in self.hunks if hunk.state is ReviewState.APPROVED
        )

    def mark_applied(self, revision: str) -> None:
        if not self.approved_patch:
            raise ValueError("transaction has no approved hunks")
        self.applied_revision = revision
        for hunk in self.hunks:
            if hunk.state is ReviewState.APPROVED:
                hunk.state = ReviewState.APPLIED

    def mark_reverted(self) -> None:
        if self.applied_revision is None:
            raise ValueError("transaction was not applied")
        self.reverted_at = datetime.now(timezone.utc).isoformat()
        for hunk in self.hunks:
            if hunk.state is ReviewState.APPLIED:
                hunk.state = ReviewState.REVERTED
