"""OpenTelemetry-compatible tracing with a dependency-free fallback."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from time import perf_counter, time
from typing import Any, Iterator
import uuid


@dataclass
class SpanRecord:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    started_at: float
    ended_at: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.ended_at is None:
            return None
        return max(0.0, (self.ended_at - self.started_at) * 1000.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes,
        }


class Telemetry:
    """Small tracing facade that emits JSONL and optionally native OTel spans."""

    def __init__(
        self,
        *,
        service_name: str = "jarvis",
        jsonl_path: str | Path | None = None,
    ) -> None:
        self.service_name = service_name
        self.jsonl_path = Path(jsonl_path).expanduser() if jsonl_path else None
        self.records: list[SpanRecord] = []
        self._otel_tracer = None
        try:
            from opentelemetry import trace  # type: ignore

            self._otel_tracer = trace.get_tracer(service_name)
        except Exception:
            self._otel_tracer = None

    @contextmanager
    def span(
        self,
        name: str,
        *,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        **attributes: Any,
    ) -> Iterator[SpanRecord]:
        record = SpanRecord(
            name=name,
            trace_id=trace_id or uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_span_id,
            started_at=time(),
            attributes={"service.name": self.service_name, **attributes},
        )
        started = perf_counter()
        otel_cm = (
            self._otel_tracer.start_as_current_span(name)
            if self._otel_tracer
            else None
        )
        native = otel_cm.__enter__() if otel_cm else None
        if native is not None:
            for key, value in record.attributes.items():
                try:
                    native.set_attribute(key, value)
                except Exception:
                    pass
        try:
            yield record
        except BaseException as exc:
            record.status = "error"
            record.error = str(exc)[:4000]
            if native is not None:
                try:
                    native.record_exception(exc)
                except Exception:
                    pass
            raise
        finally:
            elapsed = perf_counter() - started
            record.ended_at = record.started_at + elapsed
            self.records.append(record)
            self._write(record)
            if otel_cm:
                otel_cm.__exit__(None, None, None)

    def _write(self, record: SpanRecord) -> None:
        path = self.jsonl_path
        if path is None:
            configured = os.getenv("JARVIS_OTEL_JSONL")
            path = Path(configured).expanduser() if configured else None
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(record.to_dict(), ensure_ascii=False, default=str) + "\n"
            )

    def summary(self) -> dict[str, Any]:
        durations = [item.duration_ms or 0.0 for item in self.records]
        return {
            "service": self.service_name,
            "spans": len(self.records),
            "errors": sum(item.status == "error" for item in self.records),
            "duration_ms": sum(durations),
        }
