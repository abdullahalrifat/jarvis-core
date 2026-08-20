from jarvis_core import (
    CapabilityRegistry,
    EvalCase,
    FailureKind,
    ModelCapabilities,
    ModelProfile,
    TraceRecorder,
    citation_context,
    classify_failure,
    normalize_search_results,
    score_output,
)


def test_capability_registry_routes_by_requirements():
    registry = CapabilityRegistry(
        [
            ModelProfile(
                "chat",
                "openai",
                "small",
                "https://models.test/v1",
                ModelCapabilities(tool_calling=False),
                priority=10,
            ),
            ModelProfile(
                "coder",
                "openai",
                "coder",
                "https://models.test/v1",
                ModelCapabilities(tool_calling=True, structured_output=True),
                priority=5,
            ),
        ]
    )
    assert registry.select(required=("tool_calling",)).name == "coder"


def test_failure_recovery_is_deterministic():
    decision = classify_failure("HTTP 429 rate limit")
    assert decision.kind is FailureKind.RATE_LIMIT
    assert decision.action == "backoff"
    assert decision.retryable


def test_trace_redacts_secrets_and_round_trips(tmp_path):
    recorder = TraceRecorder()
    recorder.record("model_call", api_key="secret", model="coder")
    path = tmp_path / "trace.jsonl"
    recorder.write_jsonl(path)
    loaded = TraceRecorder.read_jsonl(path)
    assert loaded.events[0].payload["api_key"] == "[REDACTED]"
    assert loaded.events[0].payload["model"] == "coder"


def test_search_results_are_bounded_and_citable():
    results = normalize_search_results(
        [
            {"title": "One", "url": "https://example.com/1", "content": "fact"},
            {"title": "Duplicate", "url": "https://example.com/1"},
            {"title": "Invalid", "url": "file:///secret"},
        ]
    )
    assert len(results) == 1
    assert "https://example.com/1" in citation_context(results)


def test_eval_scoring_reports_missing_and_forbidden_content():
    result = score_output(
        EvalCase(
            name="answer",
            task="answer",
            expected_contains=("source",),
            forbidden_contains=("guess",),
        ),
        "a guess",
    )
    assert not result.passed
    assert result.score == 0.0
    assert len(result.failures) == 2
