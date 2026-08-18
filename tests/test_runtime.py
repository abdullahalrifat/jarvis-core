from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from jarvis_core import (
    AgentResult,
    ArtifactResolver,
    BudgetExceeded,
    Evidence,
    EvidenceStatus,
    FileArtifactStore,
    PromptTemplate,
    SelectiveOrchestrator,
    TaskProfile,
    TokenBudget,
    TokenLedger,
    Usage,
    VerificationStatus,
    VerificationVerdict,
    compact_messages,
    default_prompt_registry,
)


def test_atomic_reservations_prevent_parallel_overspend():
    ledger = TokenLedger(
        TokenBudget(
            max_run_input=10, max_run_output=10, max_turn_input=10, max_turn_output=10
        )
    )

    def attempt():
        try:
            return ledger.reserve("worker", 6, 1)
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        reservations = list(pool.map(lambda _: attempt(), range(2)))
    assert sum(item is not None for item in reservations) == 1


def test_reservation_commit_refund_and_provider_usage():
    ledger = TokenLedger()
    held = ledger.reserve("agent", 10, 10)
    ledger.commit(held, Usage("agent", input_tokens=8, output_tokens=3))
    refunded = ledger.reserve("agent", 1, 1)
    ledger.refund(refunded)
    normalized = ledger.usage_from_provider(
        "agent", "model", {"prompt_tokens": 7, "completion_tokens": 2}
    )
    assert normalized and normalized.input_tokens == 7 and normalized.output_tokens == 2
    assert ledger.totals().output_tokens == 3


def test_call_refunds_failed_invocation():
    ledger = TokenLedger()
    with pytest.raises(RuntimeError):
        ledger.call(
            agent="a",
            model="m",
            prompt="x",
            max_output_tokens=2,
            invoke=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
    assert ledger.totals(include_reserved=True).input_tokens == 0


def test_compaction_keeps_tool_exchange_together():
    messages = [
        {"role": "system", "content": "rules"},
        {"role": "user", "content": "old request" * 1_000},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "call-1"}]},
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "name": "read_file",
            "content": "result" * 1_000,
        },
        {"role": "user", "content": "recent"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "call-2"}]},
        {"role": "tool", "tool_call_id": "call-2", "name": "test", "content": "passed"},
    ]
    compacted, saved = compact_messages(messages, keep_recent=2)
    assistant_index = next(
        i for i, item in enumerate(compacted) if item.get("tool_calls")
    )
    assert compacted[assistant_index + 1]["tool_call_id"] == "call-2"
    assert saved > 0


def test_artifact_resolver_reads_bounded_chunks(tmp_path: Path):
    store = FileArtifactStore(tmp_path)
    artifact = store.put("abcdefghij")
    result = ArtifactResolver(store, max_bytes=5).read(artifact.uri, offset=2, limit=4)
    assert result["content"] == "cdef" and result["next_offset"] == 6
    with pytest.raises(ValueError):
        ArtifactResolver(store, max_bytes=5).read(artifact.uri, limit=6)


def test_evidence_and_verdict_validation():
    evidence = Evidence(
        "test passed",
        "tests/test_x.py",
        3,
        4,
        confidence=0.9,
        status=EvidenceStatus.VERIFIED,
    )
    verdict = VerificationVerdict(
        VerificationStatus.PASSED, checks=("pytest",), evidence=(evidence,)
    )
    assert (
        verdict.passed and verdict.to_dict()["evidence"][0]["path"] == "tests/test_x.py"
    )
    with pytest.raises(ValueError):
        VerificationVerdict(VerificationStatus.FAILED)


def test_versioned_prompt_registry():
    registry = default_prompt_registry()
    assert registry.get("verifier").id == "verifier@v1"
    with pytest.raises(ValueError):
        registry.register(PromptTemplate("verifier", "v1", "duplicate", {}))


class VerdictBackend:
    model = "test"

    def __init__(self):
        self.verifications = 0

    def run(self, *, role, task, context, max_output_tokens):
        if role == "verifier":
            self.verifications += 1
            if self.verifications == 1:
                verdict = VerificationVerdict(
                    VerificationStatus.FAILED,
                    failed_checks=("tests",),
                    retry_instruction="fix tests",
                )
            else:
                verdict = VerificationVerdict(
                    VerificationStatus.PASSED, checks=("tests",)
                )
            return AgentResult(role, "verification", verdict=verdict)
        return AgentResult(role, task, evidence=[Evidence("inspected")])


def test_orchestrator_retries_from_structured_verdict():
    results = SelectiveOrchestrator(
        VerdictBackend(), TokenLedger(), require_structured_verdict=True
    ).run("fix tests", profile=TaskProfile.CODE)
    assert [item.role for item in results] == [
        "explorer",
        "implementer",
        "verifier",
        "implementer",
        "verifier",
    ]
