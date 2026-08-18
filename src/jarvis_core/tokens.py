"""Thread-safe token estimation, reservation, and usage accounting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from threading import RLock
from typing import Callable, Mapping
from uuid import uuid4


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


@dataclass(frozen=True)
class TokenReservation:
    id: str
    agent: str
    input_tokens: int
    output_tokens: int


@dataclass
class TokenLedger:
    """Atomic budget ledger safe for parallel agent calls."""

    budget: TokenBudget = field(default_factory=TokenBudget)
    entries: list[Usage] = field(default_factory=list)
    _reservations: dict[str, TokenReservation] = field(default_factory=dict, init=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    @staticmethod
    def _sum(entries: list[Usage], agent: str | None = None) -> Usage:
        total = Usage(agent=agent or "run")
        for entry in entries:
            if agent is not None and entry.agent != agent:
                continue
            total.input_tokens += entry.input_tokens
            total.cached_input_tokens += entry.cached_input_tokens
            total.output_tokens += entry.output_tokens
            total.tool_result_tokens += entry.tool_result_tokens
            total.compaction_saved_tokens += entry.compaction_saved_tokens
        return total

    def totals(
        self, agent: str | None = None, *, include_reserved: bool = False
    ) -> Usage:
        with self._lock:
            total = self._sum(self.entries, agent)
            if include_reserved:
                for reservation in self._reservations.values():
                    if agent is None or reservation.agent == agent:
                        total.input_tokens += reservation.input_tokens
                        total.output_tokens += reservation.output_tokens
            return total

    def _validate(self, agent: str, input_tokens: int, output_tokens: int) -> None:
        if min(input_tokens, output_tokens) < 0:
            raise ValueError("token counts must be non-negative")
        run = self.totals(include_reserved=True)
        current = self.totals(agent, include_reserved=True)
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

    def reserve(
        self, agent: str, input_tokens: int, output_tokens: int
    ) -> TokenReservation:
        with self._lock:
            self._validate(agent, input_tokens, output_tokens)
            reservation = TokenReservation(
                str(uuid4()), agent, input_tokens, output_tokens
            )
            self._reservations[reservation.id] = reservation
            return reservation

    def commit(
        self, reservation: TokenReservation, usage: Usage | None = None
    ) -> Usage:
        """Commit actual usage and release unused reserved capacity."""
        with self._lock:
            held = self._reservations.pop(reservation.id, None)
            if held is None:
                raise ValueError("unknown or already closed reservation")
            actual = usage or Usage(
                agent=held.agent,
                input_tokens=held.input_tokens,
                output_tokens=held.output_tokens,
            )
            if actual.agent != held.agent:
                raise ValueError("usage agent does not match reservation")
            # The reservation is now removed, so validate the complete actual usage.
            # This also catches providers that report more than the estimate.
            self._validate(actual.agent, actual.input_tokens, actual.output_tokens)
            self.entries.append(actual)
            return actual

    def refund(self, reservation: TokenReservation) -> None:
        with self._lock:
            if self._reservations.pop(reservation.id, None) is None:
                raise ValueError("unknown or already closed reservation")

    def record(self, usage: Usage) -> None:
        reservation = self.reserve(usage.agent, usage.input_tokens, usage.output_tokens)
        self.commit(reservation, usage)

    @staticmethod
    def usage_from_provider(
        agent: str, model: str, usage: Mapping[str, int] | None
    ) -> Usage | None:
        """Normalize common OpenAI/Hugging Face usage field names."""
        if not usage:
            return None
        return Usage(
            agent=agent,
            model=model,
            input_tokens=int(usage.get("input_tokens", usage.get("prompt_tokens", 0))),
            cached_input_tokens=int(usage.get("cached_input_tokens", 0)),
            output_tokens=int(
                usage.get("output_tokens", usage.get("completion_tokens", 0))
            ),
        )

    def call(
        self,
        *,
        agent: str,
        model: str,
        prompt: object,
        max_output_tokens: int,
        invoke: Callable[[], object],
        extract_usage: Callable[[object], Mapping[str, int] | None] | None = None,
    ) -> object:
        input_tokens = estimate_tokens(prompt)
        reservation = self.reserve(agent, input_tokens, max_output_tokens)
        try:
            response = invoke()
        except BaseException:
            self.refund(reservation)
            raise
        provider_usage = extract_usage(response) if extract_usage else None
        usage = self.usage_from_provider(agent, model, provider_usage) or Usage(
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=estimate_tokens(response),
        )
        self.commit(reservation, usage)
        return response

    def to_dict(self) -> dict[str, object]:
        with self._lock:
            return {
                "budget": asdict(self.budget),
                "totals": self.totals().to_dict(),
                "reserved": self.totals(include_reserved=True).to_dict(),
                "entries": [entry.to_dict() for entry in self.entries],
            }
