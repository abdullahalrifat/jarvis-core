"""Selective Explorer -> Implementer -> Verifier orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .tokens import TokenLedger


class TaskProfile(str, Enum):
    SIMPLE = "simple"
    CODE = "code"
    COMPLEX = "complex"
    HIGH_RISK = "high_risk"


@dataclass
class AgentResult:
    role: str
    summary: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    verified: bool = False
    retryable: bool = False


class AgentBackend(Protocol):
    model: str

    def run(
        self,
        *,
        role: str,
        task: str,
        context: dict[str, Any],
        max_output_tokens: int,
    ) -> AgentResult: ...


def classify_task(task: str) -> TaskProfile:
    lowered = task.lower()
    if any(
        word in lowered
        for word in ("security", "authentication", "migration", "permission", "payment")
    ):
        return TaskProfile.HIGH_RISK
    if any(
        word in lowered
        for word in (
            "architecture",
            "refactor",
            "across",
            "multi-service",
            "entire repository",
        )
    ):
        return TaskProfile.COMPLEX
    if any(word in lowered for word in ("fix", "implement", "edit", "test", "review")):
        return TaskProfile.CODE
    return TaskProfile.SIMPLE


class SelectiveOrchestrator:
    """Use extra agents only when task shape justifies their token cost."""

    def __init__(
        self,
        backend: AgentBackend,
        ledger: TokenLedger,
        *,
        max_verification_retries: int = 1,
    ) -> None:
        self.backend = backend
        self.ledger = ledger
        self.max_verification_retries = max_verification_retries

    def _run(
        self,
        role: str,
        task: str,
        context: dict[str, Any],
        max_output_tokens: int,
    ) -> AgentResult:
        if getattr(self.backend, "metered", False):
            result = self.backend.run(
                role=role,
                task=task,
                context=context,
                max_output_tokens=max_output_tokens,
            )
        else:
            prompt = {"role": role, "task": task, "context": context}
            result = self.ledger.call(
                agent=role,
                model=self.backend.model,
                prompt=prompt,
                max_output_tokens=max_output_tokens,
                invoke=lambda: self.backend.run(
                    role=role,
                    task=task,
                    context=context,
                    max_output_tokens=max_output_tokens,
                ),
            )
        if not isinstance(result, AgentResult):
            raise TypeError("agent backend must return AgentResult")
        return result

    def run(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        *,
        profile: TaskProfile | None = None,
    ) -> list[AgentResult]:
        context = dict(context or {})
        profile = profile or classify_task(task)
        if profile is TaskProfile.SIMPLE:
            return [self._run("implementer", task, context, 900)]

        results: list[AgentResult] = []
        explorer = self._run("explorer", task, context, 900)
        results.append(explorer)
        context["exploration"] = {
            "summary": explorer.summary,
            "evidence": explorer.evidence,
        }
        if profile is TaskProfile.HIGH_RISK:
            risk = self._run("risk", task, context, 700)
            results.append(risk)
            context["risk"] = {"summary": risk.summary, "evidence": risk.evidence}

        implementer = self._run("implementer", task, context, 1_500)
        results.append(implementer)
        context["implementation"] = {
            "summary": implementer.summary,
            "changes": implementer.changes,
            "evidence": implementer.evidence,
        }
        verifier = self._run("verifier", task, context, 900)
        results.append(verifier)
        retries = 0
        while (
            not verifier.verified
            and verifier.retryable
            and retries < self.max_verification_retries
        ):
            context["verification_failure"] = {
                "summary": verifier.summary,
                "evidence": verifier.evidence,
            }
            implementer = self._run("implementer", task, context, 1_200)
            results.append(implementer)
            context["implementation"] = {
                "summary": implementer.summary,
                "changes": implementer.changes,
                "evidence": implementer.evidence,
            }
            verifier = self._run("verifier", task, context, 700)
            results.append(verifier)
            retries += 1
        return results
