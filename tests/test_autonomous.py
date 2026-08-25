from datetime import datetime, timezone

import pytest

from jarvis_core.autonomous import (
    ExecutionProof,
    ExecutionProofLedger,
    ExecutionState,
    LeaseToken,
    PermissionAction,
    PermissionRule,
    ProofKind,
    can_transition,
    cron_matches,
    next_cron,
    permission_decision,
    VerificationRecord,
    require_transition,
)


def test_execution_state_machine_rejects_invalid_terminal_transition():
    assert can_transition(ExecutionState.QUEUED, ExecutionState.LEASED)
    with pytest.raises(ValueError):
        require_transition(ExecutionState.COMPLETED, ExecutionState.RUNNING)


def test_lease_tokens_are_attempt_scoped_and_expirable():
    token = LeaseToken.issue("task", "worker", 2, 60)
    assert token.attempt == 2
    assert token.lease_id
    assert not token.expired()


def test_proof_ledger_deduplicates_and_reports_verification():
    ledger = ExecutionProofLedger()
    ledger.record(ProofKind.TEST, "pytest", "passed", "10 passed")
    ledger.record(ProofKind.TEST, "pytest", "passed", "10 passed")
    ledger.record(ProofKind.VERIFIER, "independent", "passed")
    assert ledger.successful_tests() == 1
    assert ledger.failed_tests() == 0
    assert ledger.verifier_passed() is True


def test_plan_mode_denies_mutation_even_if_rule_allows():
    decision = permission_decision(
        "write_file",
        [PermissionRule("write_file", PermissionAction.ALLOW)],
        plan_mode=True,
        mutation=True,
    )
    assert decision.action is PermissionAction.DENY


def test_standard_cron_dom_dow_uses_or_semantics():
    # 08:00 on Friday the 2nd: DOW matches although DOM does not.
    friday = datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc)
    assert cron_matches("0 8 1 * 5", friday)
    # 08:00 on the 1st even though it is Thursday: DOM matches.
    first = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    assert cron_matches("0 8 1 * 5", first)


def test_cron_supports_sunday_seven_and_next_run():
    sunday = datetime(2026, 1, 4, 8, 0, tzinfo=timezone.utc)
    assert cron_matches("0 8 * * 7", sunday)
    after = datetime(2026, 1, 4, 7, 59, tzinfo=timezone.utc)
    assert next_cron("0 8 * * 7", after) == sunday


def test_execution_proof_is_fenced_and_digest_is_stable():
    digest = "a" * 64
    proof = ExecutionProof(
        task_id="task-1",
        lease_id="lease-1",
        attempt=2,
        workspace_digest=digest,
        route="coding",
        model="test-model",
        mutation_digest="b" * 64,
        verifications=(VerificationRecord("pytest -q", "passed", 0, "c" * 64),),
        artifact_hashes={"patch.diff": "d" * 64},
    )
    payload = proof.to_dict()
    parsed = ExecutionProof.from_dict(payload, task_id="task-1", lease_id="lease-1")
    assert parsed.digest() == proof.digest()


@pytest.mark.parametrize(
    "mutation",
    [
        {"task_id": "other"},
        {"lease_id": "other"},
        {"schema_version": 999},
        {"verifications": []},
    ],
)
def test_execution_proof_rejects_unfenced_or_unverified_payload(mutation):
    digest = "a" * 64
    payload = {
        "schema_version": 1,
        "task_id": "task-1",
        "lease_id": "lease-1",
        "attempt": 1,
        "workspace_digest": digest,
        "route": "coding",
        "model": "test-model",
        "mutation_digest": "b" * 64,
        "verifications": [
            {
                "command": "pytest -q",
                "status": "passed",
                "exit_code": 0,
                "output_digest": "c" * 64,
            }
        ],
        "artifact_hashes": {},
    }
    payload.update(mutation)
    with pytest.raises(ValueError):
        ExecutionProof.from_dict(payload, task_id="task-1", lease_id="lease-1")
