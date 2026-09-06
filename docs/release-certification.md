# Coordinated release certification

The current published Core release is **Jarvis Core 0.9.3**. PR #23 prepares **Core 0.9.4** with stricter independent-evidence enforcement. Jarvis and AI Stack consumer pins must be updated to 0.9.4 only after the v0.9.4 artifact is published and its checksum is verified.

## Contract gates

Before a coordinated release:

1. Build Core from a clean checkout and verify the published artifact checksum.
2. Run Core formatting, lint, type checking, tests and the 85% coverage floor.
3. Install the exact Core wheel in Jarvis and Server; never validate against a mutable Core checkout.
4. Verify the consumer-declared Core version and checksum.
5. Run cross-repository protocol conformance for execution proof, leases, state transitions and completion validation.
6. For v0.9.4, verify that independent evidence rejects reference-only proofs, malformed digests and duplicate evidence identities for the same claim.

## Evidence boundary

`EvidenceLedger` and `EvidenceGate` are provider-neutral contracts. A consumer must translate real observations—tool execution, source locations, test results and independently verified outcomes—into Core evidence/proofs before using the gate as a completion control. Model prose alone is not evidence.

Independent evidence must have a verifiable identity (`independent_key` or a valid digest). Reference-only evidence and duplicate evidence identities for the same claim must not satisfy an independent-evidence requirement.

## Security boundary

Core does not provide OS isolation, credential storage, command execution, network policy or tenancy. Those controls belong to Jarvis/Server and must be tested at the consumer boundary.

## Release certification is broader than CI

Passing package CI proves deterministic software contracts for the tested matrix. It does not prove model quality, resistance to prompt injection, shared-worker isolation, disaster recovery or production SLOs. Those require real-repository benchmarks, adversarial canaries, chaos/soak tests and deployment-level certification in the consumer repositories.

## Version transition rule

v0.9.3 remains the published/consumable version until the v0.9.4 release workflow succeeds. Do not publish or reference a guessed v0.9.4 checksum. After release, update Jarvis and AI Stack to the exact v0.9.4 wheel/checksum and rerun their cross-repository CI.
