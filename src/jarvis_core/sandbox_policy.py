"""Provider-neutral sandbox requirements and executor contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SandboxRequirements:
    """Portable isolation requirements; consumers provide enforcement."""

    network: str = "deny"
    workspace_read_only: bool = False
    non_root: bool = True
    cpus: float = 2.0
    memory: str = "2g"
    pids: int = 256

    def validate(self) -> None:
        if self.network not in {"deny", "egress", "allow"}:
            raise ValueError("sandbox network must be deny, egress, or allow")
        if self.cpus <= 0 or self.cpus > 128:
            raise ValueError("sandbox cpus must be between 0 and 128")
        if self.pids < 16 or self.pids > 100_000:
            raise ValueError("sandbox pids must be between 16 and 100000")
        if not self.memory or any(c in self.memory for c in "\r\n"):
            raise ValueError("sandbox memory is invalid")


class SandboxExecutor(Protocol):
    """Consumer-owned executor that enforces Core sandbox requirements."""

    def build_command(
        self,
        argv: list[str],
        workspace: str,
        requirements: SandboxRequirements,
    ) -> list[str]: ...
