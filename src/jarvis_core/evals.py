"""Small dependency-free evaluation contracts for agent runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class EvalCase:
    name: str
    task: str
    expected_contains: tuple[str, ...] = ()
    forbidden_contains: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalResult:
    case: str
    passed: bool
    score: float
    output: str
    failures: tuple[str, ...] = ()
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_output(case: EvalCase, output: str) -> EvalResult:
    lowered = output.casefold()
    failures = [
        f"missing expected text: {value}"
        for value in case.expected_contains
        if value.casefold() not in lowered
    ]
    failures.extend(
        f"contained forbidden text: {value}"
        for value in case.forbidden_contains
        if value.casefold() in lowered
    )
    checks = len(case.expected_contains) + len(case.forbidden_contains)
    score = 1.0 if checks == 0 else max(0.0, 1.0 - len(failures) / checks)
    return EvalResult(
        case=case.name,
        passed=not failures,
        score=score,
        output=output,
        failures=tuple(failures),
    )


def run_evals(
    cases: Iterable[EvalCase],
    invoke: Callable[[EvalCase], str],
) -> list[EvalResult]:
    return [score_output(case, invoke(case)) for case in cases]
