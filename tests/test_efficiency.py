from jarvis_core.efficiency import AgentState, ContextBudget, ModelPricing, RouteBudget, build_context, choose_route
from jarvis_core.quality import Scope, TaskAnalysis
from jarvis_core.reliability import ContextItem


def test_agent_state_deduplicates():
    state = AgentState()
    assert state.remember_file("src/a.py")
    assert not state.remember_file("src/a.py")
    assert state.remember_command("test-command")
    assert not state.remember_command("test-command")


def test_context_budget_and_deduplication():
    items = [
        ContextItem.build("file", "a", "important", relevance=1.0),
        ContextItem.build("file", "duplicate", "important", relevance=0.1),
        ContextItem.build("file", "b", "other " * 100, relevance=0.5),
    ]
    budget = ContextBudget(total_tokens=256, stable_tokens=64, state_tokens=64, evidence_tokens=64, history_tokens=64)
    result = build_context(items, budget=budget)
    assert result.compiled.total_tokens <= 256
    assert len(result.compiled.items) == 2


def test_model_pricing_and_route_budget():
    assert ModelPricing(2, 10, 0.2).cost(input_tokens=10000, cached_input_tokens=8000, output_tokens=1000) == 0.0156
    budget = RouteBudget(1.0)
    assert budget.permits(1.0)
    assert not budget.after(0.75).permits(0.30)


def test_route_uses_task_analysis():
    cheap = TaskAnalysis(complexity=0.1, risk=0.1, scope=Scope.SINGLE_FILE)
    complex_task = TaskAnalysis(complexity=0.9, risk=0.8, scope=Scope.REPOSITORY)
    assert choose_route(cheap) == "cheap"
    assert choose_route(complex_task, uncertainty=0.8) == "expert"
