from pathlib import Path

import pytest

from jarvis_core.agents import (
    AgentResult,
    SelectiveOrchestrator,
    TaskProfile,
    classify_task,
)
from jarvis_core.artifacts import FileArtifactStore, MemoryArtifactStore
from jarvis_core.context import summarize_tool_result
from jarvis_core.tokens import BudgetExceeded, TokenBudget, TokenLedger


def test_file_and_memory_artifact_stores(tmp_path: Path):
    disk = FileArtifactStore(tmp_path)
    artifact = disk.put("hello")
    assert disk.get(artifact.uri) == b"hello"
    with pytest.raises(ValueError):
        disk.get("artifact://sha256/not-a-digest")
    memory = MemoryArtifactStore()
    item = memory.put(b"bytes")
    assert memory.get(item.uri) == b"bytes"


def test_structured_tool_summaries():
    assert (
        summarize_tool_result("run_tests", {"status": "passed", "passed": 3})["status"]
        == "passed"
    )
    search = summarize_tool_result("search_code", {"matches": list(range(20))})
    assert search["omitted_matches"] == 8
    assert summarize_tool_result("list_files", list(range(30)))["omitted_items"] == 10
    read = summarize_tool_result("read_file", {"content": "x" * 100}, max_chars=20)
    assert "omitted" in read["content"]


class RetryBackend:
    model = "test"

    def __init__(self):
        self.verifications = 0

    def run(self, *, role, task, context, max_output_tokens):
        if role == "verifier":
            self.verifications += 1
            return AgentResult(
                role=role,
                summary="check",
                verified=self.verifications > 1,
                retryable=True,
            )
        return AgentResult(role=role, summary=task)


def test_high_risk_flow_retries_failed_verification():
    backend = RetryBackend()
    results = SelectiveOrchestrator(backend, TokenLedger()).run(
        "migrate authentication", profile=TaskProfile.HIGH_RISK
    )
    assert [result.role for result in results] == [
        "explorer",
        "risk",
        "implementer",
        "verifier",
        "implementer",
        "verifier",
    ]
    assert classify_task("security review") is TaskProfile.HIGH_RISK
    assert classify_task("architecture") is TaskProfile.COMPLEX
    assert classify_task("fix it") is TaskProfile.CODE
    assert classify_task("hello") is TaskProfile.SIMPLE


def test_turn_and_agent_budgets_are_enforced():
    ledger = TokenLedger(
        TokenBudget(
            max_run_input=100,
            max_run_output=100,
            max_turn_input=2,
            max_turn_output=2,
            max_agent_input=2,
            max_agent_output=2,
        )
    )
    with pytest.raises(BudgetExceeded):
        ledger.reserve("agent", 3, 1)
    with pytest.raises(BudgetExceeded):
        ledger.reserve("agent", 1, 3)
