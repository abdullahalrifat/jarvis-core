"""Shared task-board contracts for coordinated agent teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from threading import RLock
from time import time
from typing import Any
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TeamTask:
    title: str
    description: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_id: str | None = None
    owner: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    dependencies: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    worktree: str | None = None
    branch: str | None = None
    error: str | None = None
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


class TeamBoard:
    """Thread-safe dependency-aware task board used by local and remote teams."""

    def __init__(self, tasks: list[TeamTask] | None = None) -> None:
        self._lock = RLock()
        self._tasks: dict[str, TeamTask] = {}
        for task in tasks or []:
            self.add(task)

    def add(self, task: TeamTask) -> TeamTask:
        with self._lock:
            if task.id in self._tasks:
                raise ValueError(f"duplicate team task: {task.id}")
            missing = [dep for dep in task.dependencies if dep not in self._tasks]
            if missing:
                raise ValueError("unknown dependencies: " + ", ".join(missing))
            self._tasks[task.id] = task
            self._refresh_locked()
            return task

    def get(self, task_id: str) -> TeamTask:
        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError as exc:
                raise KeyError(f"unknown team task: {task_id}") from exc

    def list(self) -> list[TeamTask]:
        with self._lock:
            self._refresh_locked()
            return sorted(self._tasks.values(), key=lambda item: item.created_at)

    def ready(self) -> list[TeamTask]:
        return [task for task in self.list() if task.status == TaskStatus.READY]

    def claim(
        self,
        task_id: str,
        owner: str,
        *,
        worktree: str | None = None,
        branch: str | None = None,
    ) -> TeamTask:
        with self._lock:
            task = self.get(task_id)
            if task.status != TaskStatus.READY:
                raise ValueError(f"task {task_id} is not ready: {task.status.value}")
            task.owner = owner
            task.worktree = worktree
            task.branch = branch
            task.status = TaskStatus.RUNNING
            task.updated_at = time()
            return task

    def complete(
        self,
        task_id: str,
        *,
        artifacts: tuple[str, ...] = (),
        evidence: tuple[dict[str, Any], ...] = (),
    ) -> TeamTask:
        with self._lock:
            task = self.get(task_id)
            if task.status != TaskStatus.RUNNING:
                raise ValueError(f"task {task_id} is not running")
            task.artifacts = artifacts
            task.evidence = evidence
            task.status = TaskStatus.COMPLETED
            task.updated_at = time()
            self._refresh_locked()
            return task

    def fail(self, task_id: str, error: str) -> TeamTask:
        with self._lock:
            task = self.get(task_id)
            task.error = error[:4000]
            task.status = TaskStatus.FAILED
            task.updated_at = time()
            self._refresh_locked()
            return task

    def cancel(self, task_id: str) -> TeamTask:
        with self._lock:
            task = self.get(task_id)
            task.status = TaskStatus.CANCELLED
            task.updated_at = time()
            self._refresh_locked()
            return task

    def _refresh_locked(self) -> None:
        for task in self._tasks.values():
            if task.status not in {
                TaskStatus.PENDING,
                TaskStatus.READY,
                TaskStatus.BLOCKED,
            }:
                continue
            deps = [self._tasks[dep].status for dep in task.dependencies]
            if any(
                status in {TaskStatus.FAILED, TaskStatus.CANCELLED}
                for status in deps
            ):
                task.status = TaskStatus.BLOCKED
            elif all(status == TaskStatus.COMPLETED for status in deps):
                task.status = TaskStatus.READY
            else:
                task.status = TaskStatus.PENDING
            task.updated_at = time()

    def to_dict(self) -> dict[str, Any]:
        tasks = self.list()
        return {
            "tasks": [task.to_dict() for task in tasks],
            "counts": {
                status.value: sum(task.status == status for task in tasks)
                for status in TaskStatus
            },
        }
