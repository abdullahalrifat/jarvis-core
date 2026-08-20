from datetime import datetime, timedelta, timezone

import pytest

from jarvis_core.benchmarks import BenchmarkObservation, BenchmarkRegistry
from jarvis_core.capabilities import ModelProfile
from jarvis_core.policy import (
    AttachmentDescriptor,
    Instruction,
    InstructionLevel,
    MemoryRecord,
    resolve_instructions,
)
from jarvis_core.resilience import (
    CircuitState,
    IdempotencyLedger,
    ProviderHealth,
    ProviderPool,
)
from jarvis_core.review import ChangeTransaction, ReviewHunk, ReviewState
from jarvis_core.verification import (
    ClaimAssessment,
    SourceAssessment,
    SourceKind,
    rank_sources,
)


def profile(name: str, priority: int = 0) -> ModelProfile:
    return ModelProfile(name, "openai", name, "http://localhost/v1", priority=priority)


def test_provider_pool_falls_back_and_tracks_health():
    pool = ProviderPool(["bad", "good"], name=str)
    pool.health["bad"] = ProviderHealth("bad", failure_threshold=1)
    pool.health["good"] = ProviderHealth("good")

    result = pool.call(
        lambda provider: (
            (_ for _ in ()).throw(RuntimeError("down"))
            if provider == "bad"
            else "answer"
        )
    )

    assert result == "answer"
    assert pool.health["bad"].state is CircuitState.OPEN
    assert pool.health["good"].successes == 1


def test_idempotency_ledger_reuses_completed_side_effect():
    calls = []
    ledger = IdempotencyLedger()
    assert ledger.execute("patch:1", lambda: calls.append(1) or "ok") == "ok"
    assert ledger.execute("patch:1", lambda: calls.append(2) or "bad") == "ok"
    assert calls == [1]


def test_claim_verification_detects_contradiction_and_ranks_primary():
    now = datetime.now(timezone.utc)
    primary = SourceAssessment(
        "https://example.gov/report", "Report", SourceKind.GOVERNMENT, now, True
    )
    community = SourceAssessment(
        "https://forum.example/post", "Post", SourceKind.COMMUNITY, now, False
    )
    claim = ClaimAssessment("The value increased", [community, primary])
    assert claim.contradictions
    assert claim.independent_domains == 2
    assert rank_sources(claim.sources)[0] == primary
    assert 0 <= claim.confidence() <= 1


def test_benchmark_registry_calibrates_for_task():
    registry = BenchmarkRegistry()
    registry.record(BenchmarkObservation("fast", "code", 0.7, 1.0, 100))
    registry.record(BenchmarkObservation("slow", "code", 0.95, 1.0, 20_000))
    assert registry.select([profile("fast"), profile("slow")], "code").name == "slow"
    with pytest.raises(ValueError):
        registry.record(BenchmarkObservation("bad", "code", 2, 0, 0))


def test_transaction_approves_applies_and_reverts_selected_hunk():
    keep = ReviewHunk("a.py", "@@ keep", ("pytest",))
    drop = ReviewHunk("b.py", "@@ drop")
    tx = ChangeTransaction("abc", [keep, drop])
    tx.approve({keep.id})
    tx.reject({drop.id})
    assert tx.approved_patch == "@@ keep"
    tx.mark_applied("def")
    assert keep.state is ReviewState.APPLIED
    tx.mark_reverted()
    assert keep.state is ReviewState.REVERTED


def test_hierarchical_instructions_memory_and_attachment_budget(tmp_path):
    nested = tmp_path / "src"
    nested.mkdir()
    instructions = [
        Instruction("user", InstructionLevel.USER, "user"),
        Instruction("workspace", InstructionLevel.WORKSPACE, "root", str(tmp_path)),
        Instruction(
            "other", InstructionLevel.DIRECTORY, "other", str(tmp_path / "other")
        ),
        Instruction("nested", InstructionLevel.DIRECTORY, "src", str(nested)),
    ]
    assert [
        item.content for item in resolve_instructions(instructions, nested / "a.py")
    ] == [
        "user",
        "workspace",
        "nested",
    ]
    expired = MemoryRecord(
        "old", "value", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    assert expired.expired()
    assert AttachmentDescriptor.budget(
        [AttachmentDescriptor("x.pdf", "application/pdf", 100, 25)]
    ) == {"files": 1, "bytes": 100, "estimated_tokens": 25}
