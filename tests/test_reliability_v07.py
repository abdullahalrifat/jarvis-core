from pathlib import Path

from jarvis_core import (
    ContextItem,
    FailureClass,
    FailureMemory,
    FailureMemoryRecord,
    FailureSignature,
    ImpactGraph,
    ImpactNode,
    PatchPlan,
    PatchTarget,
    VerifierEnvelope,
    compile_context,
    compress_tool_result,
    escalation_policy,
    evidence_confidence,
    retry_policy,
    speculation_policy,
)


def test_context_compiler_deduplicates_and_respects_budget():
    duplicate = ContextItem.build("file", "a.py", "important symbol", 0.9)
    context = compile_context(
        [
            duplicate,
            ContextItem.build("file", "copy.py", "important symbol", 0.4),
            ContextItem.build("git", "history", "recent change", 0.8),
        ],
        256,
    )
    assert len(context.items) == 2
    assert context.total_tokens <= context.token_budget
    assert "important symbol" in context.render()


def test_speculation_and_escalation_are_bounded():
    simple = speculation_policy(
        complexity=0.2, uncertainty=0.1, risk=0.1, token_pressure=0.2
    )
    assert not simple.enabled and simple.candidates == 1
    complex_policy = speculation_policy(
        complexity=0.9, uncertainty=0.9, risk=0.5, token_pressure=0.2
    )
    assert complex_policy.enabled and complex_policy.candidates in {2, 3}
    escalation = escalation_policy(
        complexity=0.9,
        uncertainty=0.8,
        risk=0.9,
        tool_failures=2,
        conflicting_evidence=True,
        retrieval_confidence=0.2,
    )
    assert escalation.tier == "expert"
    assert escalation.require_independent_verifier


def test_failure_taxonomy_stops_repeated_identical_failures(tmp_path: Path):
    signature = FailureSignature.from_error("HTTP 429 rate limit", attempts=1)
    assert signature.kind is FailureClass.RATE_LIMIT
    assert retry_policy(signature).retry
    repeated = FailureSignature.from_error("HTTP 429 rate limit", attempts=3)
    decision = retry_policy(repeated)
    assert not decision.retry and decision.escalate

    memory = FailureMemory(tmp_path / "failures.json")
    memory.remember(FailureMemoryRecord(signature, "bugfix", "fallback provider"))
    memory.remember(FailureMemoryRecord(signature, "bugfix", "fallback provider"))
    assert memory.relevant("bugfix")[0].count == 2


def test_evidence_confidence_uses_execution_signals():
    strong = evidence_confidence(
        tests_passed=5,
        tests_failed=0,
        requirements_verified=4,
        requirements_total=4,
        verifier_passed=True,
        unresolved_diagnostics=0,
        unverified_assumptions=0,
    )
    weak = evidence_confidence(
        tests_passed=0,
        tests_failed=1,
        requirements_verified=1,
        requirements_total=4,
        verifier_passed=False,
        unresolved_diagnostics=3,
        unverified_assumptions=2,
    )
    assert strong.score > 0.9
    assert weak.score < strong.score


def test_impact_graph_selects_transitive_tests():
    graph = ImpactGraph(
        [
            ImpactNode("auth.py", "source"),
            ImpactNode("api.py", "source", ("auth.py",)),
            ImpactNode("test_api.py", "test", ("api.py",)),
        ]
    )
    assert graph.tests_for(["auth.py"]) == ("test_api.py",)


def test_patch_plan_and_verifier_envelope_are_narrative_free():
    plan = PatchPlan(
        "fix auth", (PatchTarget("auth.py", ("login",), tests=("test_auth.py",)),)
    )
    assert plan.permits("auth.py", "login")
    assert not plan.permits("payments.py")
    prompt = VerifierEnvelope(
        task="fix auth",
        diff="diff --git a/auth.py b/auth.py",
        evidence=({"test": "pytest", "exit_code": 0},),
        tests="1 passed",
    ).to_prompt()
    assert "hidden reasoning" not in prompt
    assert "exit_code" in prompt


def test_tool_result_compression_is_content_addressed():
    content = "line\n" * 5000
    artifact = compress_tool_result(content, max_chars=1000)
    assert len(artifact.summary) <= 1000
    assert len(artifact.digest) == 64
    assert artifact.content == content
