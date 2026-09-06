# Coordinated release certification

The current coordinated line is Jarvis Core 0.9.2, Jarvis 0.9.1 and AI Stack Server consuming Core 0.9.2.

## Contract gates

Before a coordinated release:

1. Build Core from a clean checkout and verify the published artifact checksum.
2. Run Core formatting, lint, type checking, tests and the 85% coverage floor.
3. Install the exact Core wheel in Jarvis and Server; never validate against a mutable Core checkout.
4. Verify the consumer-declared Core version and checksum.
5. Run cross-repository protocol conformance for execution proof, leases, state transitions and completion validation.

## Evidence boundary

`EvidenceLedger` and `EvidenceGate` are provider-neutral contracts. A consumer must translate real observations—tool execution, source locations, test results and independently verified outcomes—into Core evidence/proofs before using the gate as a completion control. Model prose alone is not evidence.

## Security boundary

Core does not provide OS isolation, credential storage, command execution, network policy or tenancy. Those controls belong to Jarvis/Server and must be tested at the consumer boundary.

## Release certification is broader than CI

Passing package CI proves deterministic software contracts for the tested matrix. It does not prove model quality, resistance to prompt injection, shared-worker isolation, disaster recovery or production SLOs. Those require real-repository benchmarks, adversarial canaries, chaos/soak tests and deployment-level certification in the consumer repositories.
