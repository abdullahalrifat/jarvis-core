# Changelog

## 0.12.0

### Features

- Extend the provider-neutral model boundary with reusable usage, tool-call and response normalization helpers.
- Export the normalization helpers from the public Core API so independent agent applications can share canonical model semantics.
- Keep the provider contract dependency-free and suitable for any application or integration.

### Architecture

- Core owns provider-neutral contracts and reusable runtime primitives only.
- Provider SDKs, HTTP transports, credentials, persistence, user interfaces, deployment and operating-system enforcement remain outside Core.
- Core documentation is standalone and does not depend on or name downstream/private applications.

### Documentation

- Rewrite the package architecture documentation around standalone reuse.
- Remove downstream application-specific release instructions from the public Core documentation.
- Clarify that the PyPI README is generated from the exact release commit.

## 0.11.0

### Features

- Add dependency-free, provider-neutral model contracts for shared agent runtimes.
- Add `ModelRequest` for normalized completion requests.
- Add `ModelResponse` for normalized model output and tool calls.
- Add `ModelUsage` for provider-independent token accounting.
- Add `ToolCall` for normalized model-requested tool invocations.
- Add the `ModelProvider` protocol as the stable boundary between shared agent logic and concrete model-provider adapters.

### Architecture

- Keep provider SDKs and concrete integrations outside Core.
- Preserve Core's dependency-free contract boundary so shared agent behavior remains portable across local and hosted model backends.

### Documentation

- Align the README with the 0.11.0 package version.
- Document the provider-neutral model contract architecture.
- Document that the package README is the PyPI project description and therefore documentation changes require a new package version.

## [0.10.0](https://github.com/abdullahalrifat/jarvis-core/compare/jarvis-agent-core-v0.9.5...jarvis-agent-core-v0.10.0) (2026-09-12)

### Highlights

- Added benchmark, policy, resilience, review, verification, execution-proof and sandbox contracts.
- Added the shared token-efficient agent runtime and provider-neutral subagent proof lineage.
- Added model routing/calibration, evidence independence, execution verification and release workflow improvements.
- Added coordinated-release, PyPI Trusted Publishing and automated release lifecycle documentation.

## 0.9.4

- Enforce independent evidence identities in `EvidenceGate.audit_independent()`.
- Reject reference-only evidence when independent proof is required.
- Reject malformed evidence digests and duplicate evidence identities for the same claim.
- Add regression coverage for independent-evidence acceptance and fail-closed rejection cases.

## 0.9.3

- Current published Core release following the 0.9.2 consumer line.

## 0.9.2

- Fix optional evidence line handling so autonomous execution does not compare `None` with integers.
- Tighten public typing across autonomous execution, messaging and telemetry contracts.
- Enforce `mypy` in pull-request and exact-release validation.

## 0.9.1

- Gate release publication on formatting, lint, tests, coverage and package validation for the exact release commit.
- Verify the built wheel in a clean environment before publication.
- Bind uploaded artifacts, attestations and the GitHub release tag to the same validated commit SHA.
- Supersede the unvalidated v0.9.0 build without mutating its published assets.

## 0.9.0

- Add a versioned execution-proof envelope shared by independent agent clients and servers.
- Fence completion proof to the exact task ID, lease ID and attempt.
- Bind workspace, mutation, verification output and result artifacts with SHA-256 digests.
- Reject malformed proof versions, failed verification records and mismatched execution identities.
- Export `ExecutionProof`, `VerificationRecord` and `PROOF_SCHEMA_VERSION` as public Core contracts.

## 0.8.0

- Add autonomous execution-state contracts and validated transition rules for leased, running, verifying, uploading, cancellation, retry, timeout and terminal states.
- Add attempt-scoped lease/fencing-token contracts, execution proof-ledger records and deterministic permission-policy decisions.
- Add shared cron matching/next-run semantics.

## 0.7.0

- Add selective speculation, failure-driven escalation, verifier isolation, evidence confidence, impact-aware verification, retry ceilings and patch-minimization contracts.

## 0.6.0

- Add shared agent-team task/status/board contracts, durable job/schedule/plugin/remote-run contracts, route calibration and OpenTelemetry-compatible tracing records.

## 0.5.0

- Extend repository/developer-intelligence contracts while preserving Core's runtime-neutral boundary.

## 0.4.0

- Add adaptive complexity/risk planning, heterogeneous role routing, execution-backed completion evidence, quality metrics and stable cache identities.

## 0.3.0

- Add provider health scoring, circuit breakers, ordered fallback and retry-safe operation idempotency.
- Add source assessment, benchmark observations, calibrated model selection, reversible change-ledger contracts, hierarchical instructions, memory, MCP policy and multimodal attachment budgets.

## 0.2.0

- Add token reservations/provider usage accounting, provider-neutral compaction, content-addressed artifacts, structured evidence, verification verdicts, versioned role prompts, multi-agent contracts, capability routing, recovery, citation-safe search evidence, evaluation runners and redacted trace/replay primitives.
