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


def test_failed_commit_preserves_reservation_until_refunded():
    ledger = TokenLedger(TokenBudget(max_run_input=10, max_turn_input=10))
    reservation = ledger.reserve("agent", input_tokens=5, output_tokens=0)

    with pytest.raises(BudgetExceeded):
        ledger.commit(reservation, Usage(agent="agent", input_tokens=11))

    assert ledger.totals(include_reserved=True).input_tokens == 5
    ledger.refund(reservation)
    assert ledger.totals(include_reserved=True).input_tokens == 0


def test_call_refunds_reservation_when_usage_extraction_fails():
    ledger = TokenLedger(TokenBudget(max_run_input=10, max_turn_input=10))

    def fail_extraction(_response):
        raise RuntimeError("invalid provider usage")

    with pytest.raises(RuntimeError, match="invalid provider usage"):
        ledger.call(
            agent="agent",
            model="model",
            prompt="hello",
            max_output_tokens=1,
            invoke=lambda: "response",
            extract_usage=fail_extraction,
        )

    assert ledger.totals(include_reserved=True).input_tokens == 0
