from __future__ import annotations

import hashlib

import pytest

from jarvis_core import AgentLineage, LineageProof


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_child_lineage_binds_parent_and_root() -> None:
    root = AgentLineage(task_id="root", role="orchestrator")
    child = root.child("child", "coder")
    assert child.parent_task_id == "root"
    assert child.root_task_id == "root"
    assert child.depth == 1


def test_lineage_proof_is_tamper_evident() -> None:
    lineage = AgentLineage(
        task_id="child",
        parent_task_id="root",
        root_task_id="root",
        depth=1,
    )
    proof = LineageProof(lineage, digest("result"), (digest("evidence"),))
    restored = LineageProof.from_dict(proof.to_dict())
    assert restored.proof_digest == proof.proof_digest
    with pytest.raises(ValueError):
        LineageProof(
            lineage,
            digest("different"),
            proof.evidence_digests,
            proof.proof_digest,
        )
