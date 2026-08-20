"""Redacted, replayable agent trace events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable


_SECRET_KEYS = {"api_key", "authorization", "cookie", "password", "secret", "token"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): ("[REDACTED]" if str(key).casefold() in _SECRET_KEYS else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


@dataclass(frozen=True)
class TraceEvent:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "payload": redact(self.payload)}


class TraceRecorder:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def record(self, kind: str, **payload: Any) -> TraceEvent:
        event = TraceEvent(kind=kind, payload=redact(payload))
        self.events.append(event)
        return event

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "".join(json.dumps(event.to_dict(), default=str) + "\n" for event in self.events),
            encoding="utf-8",
        )

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "TraceRecorder":
        recorder = cls()
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            recorder.events.append(
                TraceEvent(
                    kind=str(item["kind"]),
                    payload=dict(item.get("payload") or {}),
                    timestamp=str(item["timestamp"]),
                )
            )
        return recorder

    def replay(self, kinds: Iterable[str] | None = None) -> list[TraceEvent]:
        allowed = set(kinds) if kinds is not None else None
        return [
            event
            for event in self.events
            if allowed is None or event.kind in allowed
        ]
