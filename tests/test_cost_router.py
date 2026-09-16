from jarvis_core.cost_router import (
    FailureBudget,
    RouteModel,
    RouteTier,
    RoutingSignals,
    choose_tier,
    next_tier,
    select_model,
)


def test_local_is_default():
    decision = choose_tier(RoutingSignals(complexity=0.2, risk=0.1))
    assert decision.tier is RouteTier.LOCAL


def test_complex_work_escalates_to_cheap():
    decision = choose_tier(RoutingSignals(complexity=0.9, uncertainty=0.8))
    assert decision.tier is RouteTier.CHEAP


def test_security_work_uses_frontier():
    decision = choose_tier(RoutingSignals(security_sensitive=True))
    assert decision.tier is RouteTier.FRONTIER
    assert decision.require_verification


def test_failure_budget_escalates_only_after_limit():
    budget = FailureBudget(local=2, cheap=2)
    assert next_tier(RouteTier.LOCAL, success=False, budget=budget, attempts=1) is RouteTier.LOCAL
    assert next_tier(RouteTier.LOCAL, success=False, budget=budget, attempts=2) is RouteTier.CHEAP
    assert next_tier(RouteTier.CHEAP, success=False, budget=budget, attempts=2) is RouteTier.FRONTIER


def test_model_selection_prefers_cheapest_route():
    models = (
        RouteModel("local", RouteTier.LOCAL),
        RouteModel("cloud-a", RouteTier.CHEAP, input_per_million=1, output_per_million=2),
        RouteModel("cloud-b", RouteTier.CHEAP, input_per_million=0.5, output_per_million=1),
    )
    selected = select_model(models, RouteTier.CHEAP, input_tokens=1000, output_tokens=1000)
    assert selected.name == "cloud-b"


def test_deterministic_work_bypasses_model():
    decision = choose_tier(RoutingSignals(deterministic_only=True))
    assert decision.tier is RouteTier.LOCAL
    assert decision.max_attempts == 0
    assert not decision.require_verification


def test_external_evidence_escalates_to_cheap():
    decision = choose_tier(RoutingSignals(external_evidence_required=True))
    assert decision.tier is RouteTier.CHEAP


def test_risk_requires_verification_without_escalation():
    decision = choose_tier(RoutingSignals(risk=0.7))
    assert decision.tier is RouteTier.LOCAL
    assert decision.require_verification


def test_attempt_or_tool_failure_escalates_to_cheap():
    assert choose_tier(RoutingSignals(attempts=2)).tier is RouteTier.CHEAP
    assert choose_tier(RoutingSignals(tool_failures=2)).tier is RouteTier.CHEAP


def test_repeated_failures_escalate_to_frontier():
    decision = choose_tier(RoutingSignals(attempts=2, tool_failures=2))
    assert decision.tier is RouteTier.FRONTIER
    assert decision.require_verification


def test_score_clamps_and_accounts_for_retrieval_and_failures():
    score = RoutingSignals(complexity=2.0, uncertainty=-1.0, risk=2.0, retrieval_confidence=-1.0, tool_failures=99).score()
    assert score == 1.0


def test_failure_budget_and_success_behavior():
    budget = FailureBudget(local=2, cheap=2, frontier=3)
    assert budget.limit(RouteTier.LOCAL) == 2
    assert budget.limit(RouteTier.CHEAP) == 2
    assert budget.limit(RouteTier.FRONTIER) == 3
    assert next_tier(RouteTier.LOCAL, success=True, budget=budget, attempts=99) is RouteTier.LOCAL
    assert next_tier(RouteTier.FRONTIER, success=False, budget=budget, attempts=3) is None


def test_model_cost_cached_tokens_and_negative_values():
    model = RouteModel("cached", RouteTier.CHEAP, input_per_million=1.0, cached_input_per_million=0.25, output_per_million=2.0)
    assert model.estimate_cost(1000, 500, 400) == 0.0014
    assert model.estimate_cost(-1, -1, -1) == 0.0


def test_model_selection_honors_enabled_budget_and_priority():
    models = (
        RouteModel("disabled", RouteTier.CHEAP, input_per_million=0, enabled=False),
        RouteModel("expensive", RouteTier.CHEAP, input_per_million=2, priority=10),
        RouteModel("cheap", RouteTier.CHEAP, input_per_million=1, priority=0),
        RouteModel("same-cost-priority", RouteTier.CHEAP, input_per_million=1, priority=5),
    )
    selected = select_model(models, RouteTier.CHEAP, input_tokens=1000, max_cost_usd=0.001)
    assert selected.name == "same-cost-priority"


def test_model_selection_raises_when_no_model_matches():
    try:
        select_model((), RouteTier.FRONTIER)
    except LookupError as exc:
        assert "frontier" in str(exc)
    else:
        raise AssertionError("expected LookupError")

    try:
        select_model((RouteModel("too-expensive", RouteTier.CHEAP, input_per_million=2),), RouteTier.CHEAP, input_tokens=1000, max_cost_usd=0.001)
    except LookupError:
        pass
    else:
        raise AssertionError("expected LookupError")
