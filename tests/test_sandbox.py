import pytest

from jarvis_core.sandbox import (
    SandboxError,
    TaskResourceLimits,
    TaskSandboxPolicy,
    build_task_command,
    validate_host_boundary,
)


def test_policy_requires_image(monkeypatch):
    monkeypatch.delenv("JARVIS_CLOUD_SANDBOX_IMAGE", raising=False)
    with pytest.raises(SandboxError):
        TaskSandboxPolicy.from_env()


def test_egress_requires_dedicated_network():
    policy = TaskSandboxPolicy(
        image="worker:test", network="egress", egress_network="bridge"
    )
    with pytest.raises(SandboxError, match="dedicated"):
        policy.validate()


def test_root_is_rejected():
    with pytest.raises(SandboxError, match="root"):
        TaskSandboxPolicy(image="worker:test", user="0").validate()


def test_resource_limits_are_bounded():
    with pytest.raises(ValueError, match="cpus"):
        TaskResourceLimits(cpus=0).validate()
    with pytest.raises(ValueError, match="pids"):
        TaskResourceLimits(pids=1).validate()


def test_command_is_resource_constrained_and_isolated(tmp_path):
    policy = TaskSandboxPolicy(
        image="worker:test",
        limits=TaskResourceLimits(cpus=1.5, memory="1g", pids=128, disk="4g"),
    )
    command = build_task_command(
        ["python", "-m", "pytest", "-q"],
        tmp_path,
        policy,
        require_docker=False,
    )
    assert command[:3] == ["docker", "run", "--rm"]
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--cpus") + 1] == "1.5"
    assert command[command.index("--memory") + 1] == "1g"
    assert command[command.index("--pids-limit") + 1] == "128"
    assert command[command.index("--storage-opt") + 1] == "size=4g"
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--user") + 1] != "0"
    assert "dst=/workspace" in command[command.index("--mount") + 1]


def test_egress_command_uses_policy_network(tmp_path):
    policy = TaskSandboxPolicy(
        image="worker:test",
        network="egress",
        egress_network="policy-egress",
    )
    command = build_task_command(
        ["python", "-c", "print(1)"],
        tmp_path,
        policy,
        require_docker=False,
    )
    assert command[command.index("--network") + 1] == "policy-egress"
    assert "host" not in command


def test_socket_mount_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "DOCKER_SOCKET_MOUNT", "/var/run/docker.sock:/var/run/docker.sock"
    )
    with pytest.raises(SandboxError):
        validate_host_boundary()
