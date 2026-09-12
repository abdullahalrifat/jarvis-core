"""Provider-neutral parent/child agent lineage and proof contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Mapping

LINEAGE_SCHEMA_VERSION = 1


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AgentLineage:
    """Immutable identity for one node in a parent/child agent tree."""

    task_id: str
    parent_task_id: str | None = None
    root_task_id: str | None = None
    depth: int = 0
    role: str = "agent"
    schema_version: int = LINEAGE_SCHEMA_VERSION

    def validate(self) -> None:
        if not self.task_id.strip():
            raise ValueError("lineage task_id is required")
        if self.depth < 0:
            raise ValueError("lineage depth cannot be negative")
        if not self.role.strip():
            raise ValueError("lineage role is required")
        if self.parent_task_id == self.task_id:
            raise ValueError("a task cannot be its own parent")
        if self.schema_version != LINEAGE_SCHEMA_VERSION:
            raise ValueError("unsupported lineage schema version")

    @property
    def root(self) -> str:
        return self.root_task_id or self.task_id

    def child(self, task_id: str, role: str) -> "AgentLineage":
        self.validate()
        child = AgentLineage(
            task_id=task_id,
            parent_task_id=self.task_id,
            root_task_id=self.root,
            depth=self.depth + 1,
            role=role,
        )
        child.validate()
        return child

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class LineageProof:
    """Tamper-evident binding of a child result to its parent lineage."""

    lineage: AgentLineage
    result_digest: str
    evidence_digests: tuple[str, ...] = field(default_factory=tuple)
    proof_digest: str = ""

    def __post_init__(self) -> None:
        self.lineage.validate()
        if len(self.result_digest) != 64:
            raise ValueError("result_digest must be a SHA-256 hex digest")
        int(self.result_digest, 16)
        for digest in self.evidence_digests:
            if len(digest) != 64:
                raise ValueError("evidence digests must be SHA-256 hex digests")
            int(digest, 16)
        expected = self.compute_digest()
        if self.proof_digest and self.proof_digest != expected:
            raise ValueError("lineage proof digest does not match its contents")
        object.__setattr__(self, "proof_digest", expected)

    def compute_digest(self) -> str:
        return _digest(
            {
                "lineage": self.lineage.to_dict(),
                "result_digest": self.result_digest,
                "evidence_digests": list(self.evidence_digests),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": LINEAGE_SCHEMA_VERSION,
            "lineage": self.lineage.to_dict(),
            "result_digest": self.result_digest,
            "evidence_digests": list(self.evidence_digests),
            "proof_digest": self.proof_digest,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "LineageProof":
        lineage_value = value.get("lineage")
        if not isinstance(lineage_value, Mapping):
            raise ValueError("lineage proof requires a lineage object")
        lineage = AgentLineage(**dict(lineage_value))
        return cls(
            lineage=lineage,
            result_digest=str(value.get("result_digest") or ""),
            evidence_digests=tuple(
                str(item) for item in value.get("evidence_digests", [])
            ),
            proof_digest=str(value.get("proof_digest") or ""),
        )
