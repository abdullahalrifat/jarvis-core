"""Shared platform contracts for plugins, background jobs, and remote execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
import uuid


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    description: str = ""
    skills: tuple[str, ...] = ()
    hooks: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    mcp_servers: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    checksum: str | None = None
    signature: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RemoteRunSpec:
    task: str
    workspace: str
    model: str = "auto"
    allow_write: bool = False
    conversation_id: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BackgroundJob:
    spec: RemoteRunSpec
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: JobStatus = JobStatus.QUEUED
    scheduled_at: float | None = None
    started_at: float | None = None
    finished_at: float | None = None
    run_id: str | None = None
    result: str | None = None
    error: str | None = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class ScheduleSpec:
    name: str
    run: RemoteRunSpec
    interval_seconds: float | None = None
    cron: str | None = None
    enabled: bool = True
    max_concurrency: int = 1

    def __post_init__(self) -> None:
        if bool(self.interval_seconds) == bool(self.cron):
            raise ValueError("exactly one of interval_seconds or cron is required")
        if self.interval_seconds is not None and self.interval_seconds < 60:
            raise ValueError("interval_seconds must be at least 60")
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
