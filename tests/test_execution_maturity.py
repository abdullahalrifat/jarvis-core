from jarvis_core import (
    Checkpoint,
    EvidenceLedger,
    ProcessHandle,
    ProcessStatus,
    SteeringAction,
    SteeringCommand,
    checkpoint_digest,
    execution_evidence,
)


def test_background_and_steering_contracts():
    handle = ProcessHandle("p1", ("pytest",), pid=42)
    assert handle.status is ProcessStatus.RUNNING
    assert SteeringCommand(SteeringAction.CANCEL).action is SteeringAction.CANCEL
    checkpoint = Checkpoint("c1", "r1", "before-tests")
    assert checkpoint.run_id == "r1"
    assert checkpoint_digest({"a": 1}) == checkpoint_digest({"a": 1})


def test_execution_observation_becomes_evidence():
    ledger = EvidenceLedger()
    item = execution_evidence(
        ledger,
        claim="tests pass",
        kind="test",
        reference="pytest://run/1",
        output="3 passed",
    )
    assert ledger.items == [item]
    assert item.digest and len(item.digest) == 64
