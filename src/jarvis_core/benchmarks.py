"""Benchmark observations and calibrated model selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean

from .capabilities import ModelProfile


@dataclass(frozen=True)
class BenchmarkObservation:
    model: str
    task: str
    quality: float
    tool_success: float
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def utility(self) -> float:
        latency = 1 / (1 + max(0.0, self.latency_ms) / 10_000)
        efficiency = 1 / (1 + (self.input_tokens + self.output_tokens) / 100_000)
        return (
            0.55 * self.quality
            + 0.25 * self.tool_success
            + 0.1 * latency
            + 0.1 * efficiency
        )


@dataclass
class BenchmarkRegistry:
    observations: list[BenchmarkObservation] = field(default_factory=list)

    def record(self, observation: BenchmarkObservation) -> None:
        if not 0 <= observation.quality <= 1 or not 0 <= observation.tool_success <= 1:
            raise ValueError("benchmark scores must be between zero and one")
        self.observations.append(observation)

    def score(self, model: str, task: str | None = None) -> float:
        matches = [
            item.utility
            for item in self.observations
            if item.model == model and (task is None or item.task == task)
        ]
        return fmean(matches) if matches else 0.0

    def select(self, profiles: list[ModelProfile], task: str) -> ModelProfile:
        if not profiles:
            raise LookupError("no model profiles are available")
        return max(
            profiles,
            key=lambda profile: (
                self.score(profile.name, task),
                profile.priority,
                profile.name,
            ),
        )
