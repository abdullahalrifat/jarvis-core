# Changelog

## 0.9.0

- Add a versioned execution-proof envelope shared by independent agent clients
  and servers.
- Fence completion proof to the exact task ID, lease ID and attempt.
- Bind workspace, mutation, verification output and result artifacts with
  SHA-256 digests.
- Reject malformed proof versions, failed verification records and mismatched
  execution identities.
- Export `ExecutionProof`, `VerificationRecord` and
  `PROOF_SCHEMA_VERSION` as public Core contracts.
- Add regression coverage for deterministic proof serialization, digest
  stability and stale/mismatched fence rejection.

## Fixes after 0.8.0

- Make token reservation commits transactional when reported provider usage fails
  validation, and release reservations when provider usage extraction fails.

## Documentation after 0.8.0

- Document the contract-versus-enforcement boundary explicitly: Core permission, fencing, proof and policy types require end-to-end enforcement in Jarvis/Server.
- Record the verified v0.8.0 wheel SHA-256 and coordinated release-order rule.
- Clarify that consumer production maturity is not implied by the presence of Core contracts.

No package version or v0.8.0 release asset is changed by these documentation updates.

## 0.8.0

- Add autonomous execution-state contracts and validated transition rules for leased, running, verifying, uploading, cancellation, retry, timeout and terminal states.
- Add attempt-scoped lease/fencing-token contracts for distributed workers.
- Add execution proof-ledger records for tests, commands, patches, sources, verification, approvals and routing.
- Add deterministic permission-policy decisions and plan-mode primitives.
- Add shared standard cron matching/next-run semantics, including lists/ranges/steps, Sunday `0/7` and day-of-month/day-of-week OR behavior.

Verified wheel SHA-256:

```text
d9569b69385e58a681ea01e900eb81c395d3f202a09a92878eb82bf4d4b8618a
```

## 0.7.0

- Add selective speculation, failure-driven escalation, verifier isolation, evidence confidence, impact-aware verification, retry ceilings and patch-minimization contracts.
- Add deterministic task-policy scoring so runtime decisions can be tested independently of model output.
- Extend efficiency/reliability regression coverage for simple paths, high-risk escalation, speculation pressure, evidence confidence and repeated-failure stop conditions.

## 0.6.0

- Add shared agent-team task/status/board contracts for dependency-aware parallel work.
- Add durable job, schedule, plugin-manifest and remote/cloud-run contracts shared by CLI and Server.
- Add route observations/calibration penalizing incorrect completion, latency, token use and tool failures.
- Add OpenTelemetry-compatible span records with dependency-free JSONL fallback.

## 0.5.0

- Extend repository/developer-intelligence contracts used by the v0.5 consumer line while preserving Core's runtime-neutral boundary.

## 0.4.0

- Add adaptive complexity/risk planning, heterogeneous role routing, execution-backed completion evidence, quality metrics and stable cache identities.

## 0.3.0

- Add provider health scoring, circuit breakers, ordered fallback and retry-safe operation idempotency.
- Add claim/source assessment, primary-source ranking, contradiction/freshness/diversity/confidence scoring.
- Add benchmark observations and task-specific calibrated model selection.
- Add per-hunk transactional review/reversible change-ledger contracts.
- Add hierarchical instruction resolution, expiring memory, MCP transport/tool policy and multimodal attachment budgets.

## 0.2.0

- Add strict token reservations/provider usage accounting.
- Add provider-neutral compaction with untrusted-state boundaries and preserved OpenAI/Anthropic tool exchanges.
- Add content-addressed memory/file artifact stores with bounded retrieval.
- Add structured evidence, verification verdicts, versioned role prompts, selective multi-agent contracts, capability routing, recovery, citation-safe search evidence, evaluation runners and redacted trace/replay primitives.
