"""Token estimation, budgets, and usage accounting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Callable


class BudgetExceeded(RuntimeError):
    """Raised before a call that would exceed a configured token budget."""


def estimate_tokens(value: object) -> int:
    """Conservative tokenizer-free estimate suitable for unknown open models."""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, default=str)
    if not value:
        return 0
    ascii_chars = sum(ord(char) < 128 for char in value)
    non_ascii = len(value) - ascii_chars
    return max(1, (ascii_chars + 2 * non_ascii + 2) // 3)


@dataclass(frozen=True)
class TokenBudget:
    max_run_input: int = 32_000
    max_run_output: int = 3_000
    max_turn_input: int = 16_000
    max_turn_output: int = 2_000
    max_agent_input: int = 24_000
    max_agent_output: int = 2_500


@dataclass
class Usage:
    agent: str
    model: str = ""
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    tool_result_tokens: int = 0
    compaction_saved_tokens: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class TokenLedger:
    budget: TokenBudget = field(default_factory=TokenBudget)
    entries: list[Usage] = field(default_factory=list)

    def totals(self, agent: str | None = None) -> Usage:
        selected = (
            self.entries
            if agent is None
            else [entry for entry in self.entries if entry.agent == agent]
        )
        total = Usage(agent=agent or "run")
        for entry in selected:
            total.input_tokens += entry.input_tokens
            total.cached_input_tokens += entry.cached_input_tokens
            total.output_tokens += entry.output_tokens
            total.tool_result_tokens += entry.tool_result_tokens
            total.compaction_saved_tokens += entry.compaction_saved_tokens
        return total

    def reserve(
        self,
        agent: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        run = self.totals()
        current = self.totals(agent)
        if input_tokens > self.budget.max_turn_input:
            raise BudgetExceeded("turn input token budget exceeded")
        if output_tokens > self.budget.max_turn_output:
            raise BudgetExceeded("turn output token budget exceeded")
        if run.input_tokens + input_tokens > self.budget.max_run_input:
            raise BudgetExceeded("run input token budget exceeded")
        if run.output_tokens + output_tokens > self.budget.max_run_output:
            raise BudgetExceeded("run output token budget exceeded")
        if current.input_tokens + input_tokens > self.budget.max_agent_input:
            raise BudgetExceeded(f"{agent} input token budget exceeded")
        if current.output_tokens + output_tokens > self.budget.max_agent_output:
            raise BudgetExceeded(f"{agent} output token budget exceeded")

    def record(self, usage: Usage) -> None:
        self.reserve(usage.agent, usage.input_tokens, usage.output_tokens)
        self.entries.append(usage)

    def call(
        self,
        *,
        agent: str,
        model: str,
        prompt: object,
        max_output_tokens: int,
        invoke: Callable[[], object],
    ) -> object:
        input_tokens = estimate_tokens(prompt)
        self.reserve(agent, input_tokens, max_output_tokens)
        response = invoke()
        output_tokens = estimate_tokens(response)
        self.record(
            Usage(
                agent=agent,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        )
        return response

    def to_dict(self) -> dict[str, object]:
        return {
            "budget": asdict(self.budget),
            "totals": self.totals().to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
        }
