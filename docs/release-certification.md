# Release certification

The current published Core release is **Jarvis Core 0.12.0**.

## Contract gates

Before publication, the exact release commit must pass formatting, lint, typing, tests, coverage, package builds, clean-environment installation, metadata validation, checksums and provenance generation.

## Provider neutrality

Core remains dependency-free with respect to model-provider SDKs and infrastructure clients. Provider normalization helpers operate on ordinary Python mappings and Core contracts without importing vendor libraries.

## Evidence boundary

`EvidenceLedger` and `EvidenceGate` are provider-neutral contracts. Embedding applications translate real observations—tool execution, source locations, test results and independently verified outcomes—into Core evidence/proofs before using the gate as a completion control. Model prose alone is not evidence.

Independent evidence must have a verifiable identity. Reference-only evidence and duplicate evidence identities for the same claim must not satisfy an independent-evidence requirement.

## Security boundary

Core does not provide OS isolation, credential storage, command execution, network policy or tenancy. Those controls belong to the embedding application and must be tested at that application's boundary.

## Release certification is broader than CI

Passing package CI proves deterministic software contracts for the tested matrix. It does not prove model quality, prompt-injection resistance, shared-worker isolation, disaster recovery or production SLOs. Those require application-level benchmarks, adversarial canaries, chaos/soak tests and deployment-level certification.

## Version transition rule

Published Core releases are immutable. Corrections to code or documentation require a new semantic version. Applications should consume an exact published Core version and rerun compatibility/integration gates after every Core upgrade.
