import pytest

from jarvis_core.tokens import BudgetExceeded, TokenBudget, TokenLedger, Usage


def test_ledger_enforces_run_budget():
    ledger = TokenLedger(TokenBudget(max_run_input=10, max_turn_input=10))
    ledger.record(Usage(agent="one", input_tokens=8))
    with pytest.raises(BudgetExceeded):
        ledger.record(Usage(agent="two", input_tokens=3))


def test_ledger_serializes_usage():
    ledger = TokenLedger()
    ledger.record(Usage(agent="explorer", input_tokens=10, output_tokens=2))
    assert ledger.to_dict()["totals"]["input_tokens"] == 10
