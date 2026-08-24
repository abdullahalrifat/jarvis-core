from pathlib import Path

from jarvis_core import (
    RemoteRunSpec,
    RouteCalibrator,
    RouteObservation,
    ScheduleSpec,
    TaskStatus,
    TeamBoard,
    TeamTask,
    Telemetry,
)


def test_team_board_dependency_progression():
    first = TeamTask("inspect")
    second = TeamTask("implement", dependencies=(first.id,))
    board = TeamBoard([first, second])
    assert board.get(first.id).status == TaskStatus.READY
    assert board.get(second.id).status == TaskStatus.PENDING
    board.claim(first.id, "worker-1")
    board.complete(first.id)
    assert board.get(second.id).status == TaskStatus.READY


def test_team_board_blocks_dependents_after_failure():
    first = TeamTask("inspect")
    second = TeamTask("implement", dependencies=(first.id,))
    board = TeamBoard([first, second])
    board.claim(first.id, "worker-1")
    board.fail(first.id, "boom")
    assert board.get(second.id).status == TaskStatus.BLOCKED


def test_calibrator_prefers_measured_reliability(tmp_path: Path):
    path = tmp_path / "calibration.json"
    calibrator = RouteCalibrator(path, min_samples=1)
    calibrator.extend(
        [
            RouteObservation("fast", "code", True, 100, input_tokens=1000),
            RouteObservation(
                "fast",
                "code",
                False,
                100,
                incorrect_completion=True,
            ),
            RouteObservation("safe", "code", True, 500, input_tokens=3000),
            RouteObservation("safe", "code", True, 500, input_tokens=3000),
        ]
    )
    assert calibrator.select(["fast", "safe"], "code") == "safe"
    assert (
        RouteCalibrator(path, min_samples=1).select(["fast", "safe"], "code") == "safe"
    )


def test_schedule_requires_exactly_one_timing_mode():
    run = RemoteRunSpec("task", "/repo")
    assert ScheduleSpec("daily", run, interval_seconds=60).interval_seconds == 60
    try:
        ScheduleSpec("bad", run)
    except ValueError:
        pass
    else:
        raise AssertionError("schedule without timing must fail")


def test_telemetry_jsonl_fallback(tmp_path: Path):
    target = tmp_path / "spans.jsonl"
    telemetry = Telemetry(jsonl_path=target)
    with telemetry.span("test", example=True):
        pass
    assert target.exists()
    assert telemetry.records[0].duration_ms is not None
