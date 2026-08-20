import pytest

from jarvis_core import (
    ClaimProof,
    CompletionRequirement,
    EvidenceGate,
    ProofKind,
    QualityMetrics,
    RouteCandidate,
    Scope,
    TaskAnalysis,
    adaptive_plan,
    route_roles,
    stable_cache_key,
)


def test_task_analysis_drives_adaptive_parallel_plan():
    plan = adaptive_plan(TaskAnalysis(0.8, 0.6, Scope.MULTI_MODULE, True))
    assert plan.parallel_exploration
    assert plan.implementation_owners == 1
    assert plan.independent_verifier
    assert {"explorer", "implementer", "verifier", "risk"} <= set(plan.roles)


def test_simple_task_avoids_multi_agent_token_cost():
    plan = adaptive_plan(TaskAnalysis(0.1, 0.1))
    assert plan.roles == ("implementer",)
    assert not plan.parallel_exploration


def test_role_router_prefers_quality_and_model_diversity():
    routes = route_roles(
        ("implementer", "verifier"),
        (
            RouteCandidate("fast", "qwen", "openai", 0.7, 0.9, 0.9, 0.1, 0.1),
            RouteCandidate(
                "strong", "claude", "anthropic", 0.95, 0.9, 0.95, 0.3, 0.4
            ),
        ),
    )
    assert routes[0].model == "claude"
    assert routes[1].model == "qwen"


def test_evidence_gate_rejects_unproved_or_failed_claims():
    requirements = (
        CompletionRequirement("changed auth", (ProofKind.MUTATION,)),
        CompletionRequirement("tests pass", (ProofKind.TEST,)),
    )
    audit = EvidenceGate().audit(requirements, (
        ClaimProof("changed auth", ProofKind.MUTATION, "ledger:1"),
        ClaimProof("tests pass", ProofKind.TEST, "pytest", verified=False),
    ))
    assert not audit.passed
    assert audit.rejected == ("tests pass",)


def test_analysis_validation_and_cache_stability():
    with pytest.raises(ValueError):
        TaskAnalysis(1.1, 0)
    assert stable_cache_key("repo", {"b": 2, "a": 1}) == stable_cache_key(
        "repo", {"a": 1, "b": 2}
    )


def test_quality_metrics_summary():
    metrics = QualityMetrics()
    metrics.record(success=True, latency_ms=100, input_tokens=10, output_tokens=5)
    metrics.record(
        success=False,
        latency_ms=300,
        input_tokens=20,
        output_tokens=5,
        tool_failures=2,
    )
    assert metrics.summary() == {
        "runs": 2.0,
        "success_rate": 0.5,
        "avg_latency_ms": 200,
        "avg_tokens": 20,
        "avg_tool_failures": 1,
    }
