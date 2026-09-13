from jarvis_core.calibration import RouteCalibrator, RouteObservation


def test_calibrator_requires_minimum_samples_and_quality_floor():
    calibrator = RouteCalibrator(min_samples=3, quality_floor=0.8)
    for _ in range(2):
        calibrator.record(RouteObservation("cheap", "code", True, 100, quality=0.95))
    assert calibrator.select(["cheap", "fallback"], "code", fallback="fallback") == "fallback"
    calibrator.record(RouteObservation("cheap", "code", True, 100, quality=0.95))
    assert calibrator.select(["cheap", "fallback"], "code", fallback="fallback") == "cheap"


def test_calibrator_reuses_legacy_observations():
    calibrator = RouteCalibrator(min_samples=1)
    calibrator.record(RouteObservation("legacy", "general", True, 100))
    assert calibrator.score("legacy", "general").quality == 1.0


def test_calibrator_recency_changes_effective_weight():
    now = 1_000_000.0
    calibrator = RouteCalibrator(min_samples=1, half_life_days=30)
    calibrator.record(RouteObservation("route", "code", True, 100, quality=1.0, recorded_at=now))
    score = calibrator.score("route", "code", now=now + 30 * 86400)
    assert score is not None
    assert 0.49 < score.effective_samples < 0.51
