"""Hierarchical instruction, durable memory, MCP, and attachment policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Iterable


class InstructionLevel(IntEnum):
    USER = 10
    WORKSPACE = 20
    DIRECTORY = 30
    SESSION = 40


@dataclass(frozen=True)
class Instruction:
    content: str
    level: InstructionLevel
    source: str
    directory: str | None = None


def resolve_instructions(
    instructions: Iterable[Instruction], target: str | Path
) -> list[Instruction]:
    path = Path(target).resolve()
    applicable = []
    for item in instructions:
        if item.directory is not None:
            directory = Path(item.directory).resolve()
            try:
                path.relative_to(directory)
            except ValueError:
                continue
        applicable.append(item)
    return sorted(applicable, key=lambda item: (item.level, item.source))


@dataclass
class MemoryRecord:
    key: str
    value: str
    scope: str = "user"
    expires_at: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        current = now or datetime.now(timezone.utc)
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return current >= expiry


@dataclass(frozen=True)
class ToolPermission:
    server: str
    tool: str
    allow: bool = False
    requires_approval: bool = True
    read_only: bool = False


@dataclass(frozen=True)
class MCPServerConfig:
    name: str
    transport: str
    endpoint: str
    oauth_audience: str | None = None
    health_interval_seconds: int = 30
    permissions: tuple[ToolPermission, ...] = ()


@dataclass(frozen=True)
class AttachmentDescriptor:
    path: str
    media_type: str
    size_bytes: int
    estimated_tokens: int
    preview: str = ""
    sha256: str = ""

    @staticmethod
    def budget(descriptors: Iterable["AttachmentDescriptor"]) -> dict[str, int]:
        items = list(descriptors)
        return {
            "files": len(items),
            "bytes": sum(item.size_bytes for item in items),
            "estimated_tokens": sum(item.estimated_tokens for item in items),
        }
