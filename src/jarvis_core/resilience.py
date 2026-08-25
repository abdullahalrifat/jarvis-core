"""Deterministic provider resilience and retry-safe execution contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ProviderHealth:
    name: str
    failure_threshold: int = 3
    recovery_seconds: float = 30.0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    latency_ms_ema: float | None = None
    opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        if self.opened_at is None:
            return CircuitState.CLOSED
        if monotonic() - self.opened_at >= self.recovery_seconds:
            return CircuitState.HALF_OPEN
        return CircuitState.OPEN

    @property
    def score(self) -> float:
        reliability = (self.successes + 1) / (self.successes + self.failures + 2)
        latency_penalty = min((self.latency_ms_ema or 0.0) / 60_000.0, 0.5)
        circuit_penalty = 1.0 if self.state is CircuitState.OPEN else 0.0
        return max(0.0, reliability - latency_penalty - circuit_penalty)

    def record_success(self, latency_ms: float) -> None:
        self.successes += 1
        self.consecutive_failures = 0
        self.opened_at = None
        alpha = 0.2
        self.latency_ms_ema = (
            latency_ms
            if self.latency_ms_ema is None
            else alpha * latency_ms + (1 - alpha) * self.latency_ms_ema
        )

    def record_failure(self) -> None:
        self.failures += 1
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.opened_at = monotonic()


@dataclass
class ProviderPool(Generic[T]):
    providers: list[T]
    name: Callable[[T], str]
    health: dict[str, ProviderHealth] = field(default_factory=dict)

    def ordered(self) -> list[T]:
        available = [
            provider
            for provider in self.providers
            if self.health.setdefault(
                self.name(provider), ProviderHealth(self.name(provider))
            ).state
            is not CircuitState.OPEN
        ]
        return sorted(
            available,
            key=lambda item: self.health[self.name(item)].score,
            reverse=True,
        )

    def call(self, invoke: Callable[[T], T]) -> T:
        errors: list[BaseException] = []
        for provider in self.ordered():
            started = monotonic()
            health = self.health[self.name(provider)]
            try:
                result = invoke(provider)
            except BaseException as exc:
                health.record_failure()
                errors.append(exc)
                continue
            health.record_success((monotonic() - started) * 1000)
            return result
        if errors:
            raise RuntimeError("all configured providers failed") from errors[-1]
        raise RuntimeError("no healthy provider is available")


@dataclass
class IdempotencyLedger:
    """Caches completed tool results so retries never repeat side effects."""

    completed: dict[str, object] = field(default_factory=dict)
    in_flight: set[str] = field(default_factory=set)

    def execute(self, key: str, operation: Callable[[], T]) -> T:
        if key in self.completed:
            return self.completed[key]  # type: ignore[return-value]
        if key in self.in_flight:
            raise RuntimeError(f"operation is already in flight: {key}")
        self.in_flight.add(key)
        try:
            result = operation()
            self.completed[key] = result
            return result
        finally:
            self.in_flight.discard(key)
