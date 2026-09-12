from jarvis_core import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalResponse,
    Capability,
    CapabilityPolicy,
    SandboxRequirements,
)


def test_capability_policy_is_fail_closed():
    policy = CapabilityPolicy(
        allowed=frozenset({Capability.READ_FILES}),
        approval_required=frozenset({Capability.WRITE_FILES}),
    )
    assert policy.decide(Capability.READ_FILES) is ApprovalDecision.ALLOW
    assert policy.decide(Capability.WRITE_FILES) is ApprovalDecision.ASK
    assert policy.decide(Capability.NETWORK) is ApprovalDecision.DENY


def test_approval_round_trip_shape():
    request = ApprovalRequest(Capability.GIT_PUSH, "publish reviewed changes", "repository")
    response = ApprovalResponse(request, ApprovalDecision.ALLOW)
    assert response.request.capability is Capability.GIT_PUSH
    assert response.decision is ApprovalDecision.ALLOW


def test_sandbox_requirements_validate():
    SandboxRequirements(network="egress", cpus=4, memory="4g", pids=512).validate()
