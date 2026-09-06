from jarvis_core.quality import ClaimProof, CompletionRequirement, EvidenceGate, ProofKind


def test_independent_gate_accepts_distinct_execution_identities():
    gate = EvidenceGate()
    requirement = CompletionRequirement("verification", (ProofKind.TEST,))
    proofs = [
        ClaimProof("verification", ProofKind.TEST, "run-a", independent_key="verifier-a"),
    ]
    assert gate.audit_independent((requirement,), proofs).passed


def test_independent_gate_rejects_missing_evidence():
    gate = EvidenceGate()
    requirement = CompletionRequirement("verification", (ProofKind.TEST,))
    assert not gate.audit_independent((requirement,), ()).passed


def test_digest_validation_rejects_malformed_digest():
    proof = ClaimProof("x", ProofKind.COMMAND, "ref", digest="not-a-digest")
    assert not EvidenceGate().validate_digest(proof)
