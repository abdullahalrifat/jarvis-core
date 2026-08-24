"""Measured route calibration driven by observed task outcomes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class RouteObservation:
    route: str
    category: str
    success: bool
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    tool_failures: int = 0
    incorrect_completion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouteScore:
    route: str
    category: str
    samples: int
    success_rate: float
    incorrect_completion_rate: float
    mean_latency_ms: float
    mean_tokens: float
    mean_cost: float
    mean_tool_failures: float
    utility: float


class RouteCalibrator:
    """Persistent empirical router; never trusts model self-reported quality."""

    def __init__(self, path: str | Path | None = None, *, min_samples: int = 3) -> None:
        self.path = Path(path).expanduser() if path else None
        self.min_samples = max(1, min_samples)
        self.observations: list[RouteObservation] = []
        if self.path and self.path.is_file():
            self.load()

    def record(self, observation: RouteObservation) -> None:
        self.observations.append(observation)
        if self.path:
            self.save()

    def extend(self, observations: Iterable[RouteObservation]) -> None:
        self.observations.extend(observations)
        if self.path:
            self.save()

    def score(self, route: str, category: str) -> RouteScore | None:
        rows = [
            item
            for item in self.observations
            if item.route == route and item.category in {category, "*"}
        ]
        if not rows:
            return None
        samples = len(rows)
        success_rate = sum(item.success for item in rows) / samples
        incorrect_rate = sum(item.incorrect_completion for item in rows) / samples
        mean_latency = sum(max(0.0, item.latency_ms) for item in rows) / samples
        mean_tokens = (
            sum(max(0, item.input_tokens + item.output_tokens) for item in rows)
            / samples
        )
        mean_cost = sum(max(0.0, item.cost) for item in rows) / samples
        mean_failures = sum(max(0, item.tool_failures) for item in rows) / samples
        # Reliability dominates. Latency/tokens/cost only break ties among successful routes.
        utility = (
            success_rate * 100.0
            - incorrect_rate * 80.0
            - min(mean_latency / 1000.0, 30.0) * 0.25
            - min(mean_tokens / 10000.0, 20.0) * 0.5
            - min(mean_cost, 10.0) * 2.0
            - mean_failures * 3.0
        )
        if samples < self.min_samples:
            utility -= (self.min_samples - samples) * 5.0
        return RouteScore(
            route,
            category,
            samples,
            success_rate,
            incorrect_rate,
            mean_latency,
            mean_tokens,
            mean_cost,
            mean_failures,
            utility,
        )

    def select(
        self,
        routes: Iterable[str],
        category: str,
        *,
        fallback: str | None = None,
    ) -> str:
        candidates = [(route, self.score(route, category)) for route in routes]
        measured = [(route, score) for route, score in candidates if score is not None]
        if not measured:
            if fallback is not None:
                return fallback
            try:
                return next(iter(routes))
            except StopIteration as exc:
                raise LookupError("no routes available") from exc
        measured.sort(
            key=lambda item: (item[1].utility, item[1].samples),  # type: ignore[union-attr]
            reverse=True,
        )
        return measured[0][0]

    def leaderboard(self, category: str) -> list[RouteScore]:
        routes = sorted({item.route for item in self.observations})
        scores = [
            score
            for route in routes
            if (score := self.score(route, category)) is not None
        ]
        return sorted(
            scores,
            key=lambda item: (item.utility, item.samples),
            reverse=True,
        )

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps([item.to_dict() for item in self.observations], indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def load(self) -> None:
        if not self.path:
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.observations = [RouteObservation(**item) for item in payload]
