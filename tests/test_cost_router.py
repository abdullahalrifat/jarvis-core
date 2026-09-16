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
    assert (
        next_tier(RouteTier.LOCAL, success=False, budget=budget, attempts=1)
        is RouteTier.LOCAL
    )
    assert (
        next_tier(RouteTier.LOCAL, success=False, budget=budget, attempts=2)
        is RouteTier.CHEAP
    )
    assert (
        next_tier(RouteTier.CHEAP, success=False, budget=budget, attempts=2)
        is RouteTier.FRONTIER
    )


def test_model_selection_prefers_cheapest_route():
    models = (
        RouteModel("local", RouteTier.LOCAL),
        RouteModel(
            "cloud-a", RouteTier.CHEAP, input_per_million=1, output_per_million=2
        ),
        RouteModel(
            "cloud-b", RouteTier.CHEAP, input_per_million=0.5, output_per_million=1
        ),
    )
    selected = select_model(
        models, RouteTier.CHEAP, input_tokens=1000, output_tokens=1000
    )
    assert selected.name == "cloud-b"
