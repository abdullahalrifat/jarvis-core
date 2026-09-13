"""Measured, provider-neutral route calibration from observed task outcomes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp
import json
from pathlib import Path
from time import time
from typing import Any, Iterable


@dataclass(frozen=True)
class RouteObservation:
    """Provider-neutral runtime or benchmark evidence for one route."""
    route: str
    category: str
    success: bool
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    tool_failures: int = 0
    incorrect_completion: bool = False
    quality: float = 0.0
    cached_input_tokens: int = 0
    source: str = "runtime"
    recorded_at: float = 0.0

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
    quality: float = 0.0
    mean_cached_input_tokens: float = 0.0
    effective_samples: float = 0.0


class RouteCalibrator:
    """Persistent empirical router with conservative evidence safeguards."""
    def __init__(self, path: str | Path | None = None, *, min_samples: int = 3, quality_floor: float = 0.70, half_life_days: float = 30.0) -> None:
        self.path = Path(path).expanduser() if path else None
        self.min_samples = max(1, min_samples)
        self.quality_floor = max(0.0, min(1.0, quality_floor))
        self.half_life_days = max(0.0, half_life_days)
        self.observations: list[RouteObservation] = []
        if self.path and self.path.is_file():
            self.load()

    def record(self, observation: RouteObservation) -> None:
        if not 0.0 <= observation.quality <= 1.0:
            raise ValueError("quality must be between zero and one")
        if observation.latency_ms < 0 or observation.cost < 0:
            raise ValueError("latency_ms and cost must not be negative")
        self.observations.append(observation)
        if self.path:
            self.save()

    def extend(self, observations: Iterable[RouteObservation]) -> None:
        for observation in observations:
            self.record(observation)
        if self.path:
            self.save()

    def _weight(self, observation: RouteObservation, now: float) -> float:
        if not observation.recorded_at or self.half_life_days == 0:
            return 1.0
        age_days = max(0.0, now - observation.recorded_at) / 86400.0
        return exp(-0.69314718056 * age_days / self.half_life_days)

    def score(self, route: str, category: str, *, now: float | None = None) -> RouteScore | None:
        now = time() if now is None else now
        rows = [item for item in self.observations if item.route == route and item.category in {category, "*"}]
        if not rows:
            return None
        weighted = [(item, self._weight(item, now)) for item in rows]
        total = sum(weight for _, weight in weighted) or 1.0

        def average(value: Any) -> float:
            return sum(float(value(item)) * weight for item, weight in weighted) / total

        success_rate = average(lambda item: item.success)
        incorrect_rate = average(lambda item: item.incorrect_completion)
        quality = average(lambda item: item.quality if item.quality else float(item.success))
        mean_latency = average(lambda item: max(0.0, item.latency_ms))
        mean_tokens = average(lambda item: max(0, item.input_tokens + item.output_tokens))
        mean_cost = average(lambda item: max(0.0, item.cost))
        mean_failures = average(lambda item: max(0, item.tool_failures))
        mean_cached = average(lambda item: max(0, item.cached_input_tokens))
        utility = quality * 0.45 + success_rate * 0.30 - incorrect_rate * 0.15 - min(mean_failures / 5.0, 1.0) * 0.05 - min(mean_latency / 10_000.0, 1.0) * 0.025 - min(mean_cost, 1.0) * 0.025
        return RouteScore(route, category, len(rows), success_rate, incorrect_rate, mean_latency, mean_tokens, mean_cost, mean_failures, utility, quality, mean_cached, total)

    def select(self, routes: Iterable[str], category: str, *, fallback: str | None = None, quality_floor: float | None = None) -> str:
        route_list = list(routes)
        if not route_list:
            raise LookupError("no routes available")
        floor = self.quality_floor if quality_floor is None else quality_floor
        measured = []
        for route in route_list:
            score = self.score(route, category)
            if score is None or score.samples < self.min_samples or score.quality < floor:
                continue
            measured.append((route, score))
        if not measured:
            return fallback if fallback is not None else route_list[0]
        return max(measured, key=lambda item: (item[1].utility, item[1].effective_samples))[0]

    def leaderboard(self, category: str) -> list[RouteScore]:
        routes = sorted({item.route for item in self.observations})
        scores = [score for route in routes if (score := self.score(route, category)) is not None]
        return sorted(scores, key=lambda item: (item.utility, item.effective_samples), reverse=True)

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps([item.to_dict() for item in self.observations], indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> None:
        if not self.path:
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.observations = [RouteObservation(**item) for item in payload]
