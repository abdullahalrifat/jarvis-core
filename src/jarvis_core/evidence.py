"""Structured evidence and verification contracts shared by all consumers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class EvidenceStatus(str, Enum):
    OBSERVED = "observed"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Evidence:
    claim: str
    path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    digest: str | None = None
    confidence: float = 1.0
    status: EvidenceStatus = EvidenceStatus.OBSERVED

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.start_line is not None and self.start_line < 1:
            raise ValueError("start_line must be positive")
        if self.end_line is not None and self.start_line is None:
            raise ValueError("end_line requires start_line")
        if (
            self.end_line is not None
            and self.start_line is not None
            and self.end_line < self.start_line
        ):
            raise ValueError("end_line must not precede start_line")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class VerificationVerdict:
    status: VerificationStatus
    checks: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    failed_checks: tuple[str, ...] = ()
    retry_instruction: str | None = None

    def __post_init__(self) -> None:
        if self.status is VerificationStatus.PASSED and self.failed_checks:
            raise ValueError("passed verdict cannot contain failed checks")
        if self.status is not VerificationStatus.PASSED and not (
            self.failed_checks or self.retry_instruction
        ):
            raise ValueError("failed or blocked verdict requires an explanation")

    @property
    def passed(self) -> bool:
        return self.status is VerificationStatus.PASSED

    @property
    def retryable(self) -> bool:
        return self.status is VerificationStatus.FAILED and bool(self.retry_instruction)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checks": list(self.checks),
            "evidence": [item.to_dict() for item in self.evidence],
            "failed_checks": list(self.failed_checks),
            "retry_instruction": self.retry_instruction,
        }


@dataclass
class EvidenceLedger:
    items: list[Evidence] = field(default_factory=list)

    def add(self, evidence: Evidence) -> None:
        key = (evidence.claim, evidence.path, evidence.start_line, evidence.end_line)
        for index, current in enumerate(self.items):
            current_key = (
                current.claim,
                current.path,
                current.start_line,
                current.end_line,
            )
            if current_key == key:
                if evidence.confidence >= current.confidence:
                    self.items[index] = evidence
                return
        self.items.append(evidence)

    def extend(self, evidence: list[Evidence] | tuple[Evidence, ...]) -> None:
        for item in evidence:
            self.add(item)

    def to_dict(self) -> list[dict[str, object]]:
        return [item.to_dict() for item in self.items]
