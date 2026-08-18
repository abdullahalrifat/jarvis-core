"""Versioned prompts with explicit output contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PromptTemplate:
    role: str
    version: str
    system: str
    output_contract: Mapping[str, object]

    @property
    def id(self) -> str:
        return f"{self.role}@{self.version}"


class PromptRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate, *, replace: bool = False) -> None:
        if template.id in self._templates and not replace:
            raise ValueError(f"prompt already registered: {template.id}")
        self._templates[template.id] = template

    def get(self, role: str, version: str = "v1") -> PromptTemplate:
        try:
            return self._templates[f"{role}@{version}"]
        except KeyError as error:
            raise KeyError(f"unknown prompt: {role}@{version}") from error


EVIDENCE_CONTRACT = {
    "summary": "string",
    "evidence": [
        {
            "claim": "string",
            "path": "string|null",
            "start_line": "integer|null",
            "end_line": "integer|null",
            "digest": "string|null",
            "confidence": "number[0,1]",
            "status": "observed|verified|rejected",
        }
    ],
}

VERDICT_CONTRACT = {
    "status": "passed|failed|blocked",
    "checks": ["string"],
    "evidence": EVIDENCE_CONTRACT["evidence"],
    "failed_checks": ["string"],
    "retry_instruction": "string|null",
}


def default_prompt_registry() -> PromptRegistry:
    registry = PromptRegistry()
    shared = (
        "Use tools for facts. Do not invent files, commands, or test results. "
        "Return concise structured output matching the contract. State uncertainty."
    )
    registry.register(
        PromptTemplate(
            "explorer",
            "v1",
            shared
            + " Inspect only; identify relevant code, constraints, and evidence.",
            EVIDENCE_CONTRACT,
        )
    )
    registry.register(
        PromptTemplate(
            "risk",
            "v1",
            shared
            + " Inspect only; identify security, migration, and regression risks.",
            EVIDENCE_CONTRACT,
        )
    )
    registry.register(
        PromptTemplate(
            "implementer",
            "v1",
            shared
            + " Make the smallest coherent change, then report exact changed paths.",
            {**EVIDENCE_CONTRACT, "changes": ["string"]},
        )
    )
    registry.register(
        PromptTemplate(
            "verifier",
            "v1",
            shared
            + " Never infer success from prose. Run applicable checks and emit a verdict; "
            "use blocked when verification cannot run.",
            VERDICT_CONTRACT,
        )
    )
    return registry
