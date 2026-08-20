"""Claim-level evidence verification and source-quality scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlparse


class SourceKind(str, Enum):
    PRIMARY = "primary"
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    NEWS = "news"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


_SOURCE_WEIGHT = {
    SourceKind.PRIMARY: 1.0,
    SourceKind.GOVERNMENT: 0.95,
    SourceKind.ACADEMIC: 0.9,
    SourceKind.NEWS: 0.7,
    SourceKind.COMMUNITY: 0.45,
    SourceKind.UNKNOWN: 0.3,
}


@dataclass(frozen=True)
class SourceAssessment:
    url: str
    title: str
    kind: SourceKind = SourceKind.UNKNOWN
    published_at: datetime | None = None
    supports: bool = True

    def freshness(self, now: datetime | None = None, half_life_days: int = 365) -> float:
        if self.published_at is None:
            return 0.5
        current = now or datetime.now(timezone.utc)
        published = self.published_at
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age = max(0.0, (current - published).total_seconds() / 86400)
        return 0.5 ** (age / max(1, half_life_days))

    @property
    def domain(self) -> str:
        return (urlparse(self.url).hostname or "").lower()


@dataclass
class ClaimAssessment:
    claim: str
    sources: list[SourceAssessment] = field(default_factory=list)

    @property
    def contradictions(self) -> bool:
        return any(item.supports for item in self.sources) and any(
            not item.supports for item in self.sources
        )

    @property
    def independent_domains(self) -> int:
        return len({item.domain for item in self.sources if item.domain})

    def consensus(self) -> float:
        if not self.sources:
            return 0.0
        signed = [
            _SOURCE_WEIGHT[item.kind] * item.freshness() * (1 if item.supports else -1)
            for item in self.sources
        ]
        return sum(signed) / max(sum(abs(item) for item in signed), 1e-9)

    def confidence(self) -> float:
        if not self.sources:
            return 0.0
        quality = max(
            _SOURCE_WEIGHT[item.kind] * item.freshness() for item in self.sources
        )
        diversity = min(self.independent_domains / 3, 1.0)
        contradiction_penalty = 0.35 if self.contradictions else 0.0
        return max(0.0, min(1.0, 0.65 * quality + 0.35 * diversity - contradiction_penalty))


def rank_sources(sources: list[SourceAssessment]) -> list[SourceAssessment]:
    return sorted(
        sources,
        key=lambda item: (
            _SOURCE_WEIGHT[item.kind] * item.freshness(),
            item.domain,
            item.title,
        ),
        reverse=True,
    )
