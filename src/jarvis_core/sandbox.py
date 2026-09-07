"""Provider-neutral, fail-closed sandbox policy for task execution."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
from typing import Sequence


class SandboxError(RuntimeError):
    """Raised when the requested task isolation policy cannot be enforced."""


@dataclass(frozen=True)
class TaskResourceLimits:
    cpus: float = 2.0
    memory: str = "2g"
    pids: int = 256
    disk: str = "8g"
    tmpfs: str = "512m"

    def validate(self) -> None:
        if self.cpus <= 0 or self.cpus > 128:
            raise ValueError("sandbox cpus must be between 0 and 128")
        if self.pids < 16 or self.pids > 100_000:
            raise ValueError("sandbox pids must be between 16 and 100000")
        for name, value in (
            ("memory", self.memory),
            ("disk", self.disk),
            ("tmpfs", self.tmpfs),
        ):
            if not value or any(char in value for char in "\r\n"):
                raise ValueError(f"sandbox {name} is invalid")


@dataclass(frozen=True)
class TaskSandboxPolicy:
    image: str
    network: str = "deny"
    egress_network: str | None = None
    workspace_read_only: bool = False
    user: str = "65532:65532"
    seccomp: str = "default"
    apparmor_profile: str | None = None
    limits: TaskResourceLimits = TaskResourceLimits()

    @classmethod
    def from_env(cls, prefix: str = "JARVIS_CLOUD_") -> "TaskSandboxPolicy":
        network = os.getenv(f"{prefix}SANDBOX_NETWORK", "deny").casefold()
        policy = cls(
            image=os.getenv(f"{prefix}SANDBOX_IMAGE", "").strip(),
            network=network,
            egress_network=os.getenv(f"{prefix}EGRESS_NETWORK") or None,
            workspace_read_only=os.getenv(
                f"{prefix}WORKSPACE_READONLY", "0"
            ).casefold()
            in {"1", "true", "yes"},
            user=os.getenv(f"{prefix}SANDBOX_USER", "65532:65532"),
            seccomp=os.getenv(f"{prefix}SECCOMP", "default"),
            apparmor_profile=os.getenv(f"{prefix}APPARMOR") or None,
            limits=TaskResourceLimits(
                cpus=float(os.getenv(f"{prefix}CPUS", "2")),
                memory=os.getenv(f"{prefix}MEMORY", "2g"),
                pids=int(os.getenv(f"{prefix}PIDS", "256")),
                disk=os.getenv(f"{prefix}DISK", "8g"),
                tmpfs=os.getenv(f"{prefix}TMPFS", "512m"),
            ),
        )
        policy.validate()
        return policy

    def validate(self) -> None:
        if not self.image:
            raise SandboxError("per-task isolation requires a sandbox image")
        if self.network not in {"deny", "egress"}:
            raise SandboxError("sandbox network must be deny or egress")
        if self.network == "egress" and (
            not self.egress_network or self.egress_network in {"bridge", "host"}
        ):
            raise SandboxError(
                "egress isolation requires a dedicated policy-enforced Docker network"
            )
        if not self.user or self.user == "0" or self.user.startswith("0:"):
            raise SandboxError("sandbox must not run as root")
        self.limits.validate()


def docker_available() -> bool:
    return shutil.which("docker") is not None


def validate_host_boundary(socket_mount_env: str = "DOCKER_SOCKET_MOUNT") -> None:
    """Fail closed if an operator configures a Docker socket mount."""
    if os.getenv(socket_mount_env, "").strip():
        raise SandboxError("Docker socket exposure is forbidden for sandboxed workers")


def build_task_command(
    argv: Sequence[str],
    workspace: str | Path,
    policy: TaskSandboxPolicy,
    *,
    require_docker: bool = True,
) -> list[str]:
    """Build a non-shell Docker command for one isolated task."""
    policy.validate()
    if require_docker and not docker_available():
        raise SandboxError("Docker is required for per-task isolation")

    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise SandboxError(f"sandbox workspace does not exist: {root}")
    if not argv or str(argv[0]).startswith("-"):
        raise ValueError("sandbox command is invalid")

    limits = policy.limits
    command = [
        "docker",
        "run",
        "--rm",
        "--init",
        "--read-only",
        "--network",
        "none" if policy.network == "deny" else policy.egress_network or "none",
        "--cpus",
        str(limits.cpus),
        "--memory",
        limits.memory,
        "--memory-swap",
        limits.memory,
        "--pids-limit",
        str(limits.pids),
        "--storage-opt",
        f"size={limits.disk}",
        "--tmpfs",
        f"/tmp:rw,nosuid,nodev,noexec,size={limits.tmpfs},mode=1777",
        "--tmpfs",
        "/run:rw,size=64m,mode=755",
        "--tmpfs",
        "/var/tmp:rw,size=64m,mode=1777",
        "--security-opt",
        "no-new-privileges:true",
        "--security-opt",
        f"seccomp={policy.seccomp}",
        "--cap-drop",
        "ALL",
        "--user",
        policy.user,
    ]
    if policy.apparmor_profile:
        command += ["--security-opt", f"apparmor={policy.apparmor_profile}"]
    command += [
        "--mount",
        f"type=bind,src={root},dst=/workspace,readonly={'true' if policy.workspace_read_only else 'false'}",
        "--workdir",
        "/workspace",
        policy.image,
    ]
    return [*command, *[str(item) for item in argv]]


IsolationError = SandboxError
