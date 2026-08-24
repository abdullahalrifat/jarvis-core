# Changelog

## 0.7.0 (unreleased)

- Add task execution policy contracts for selective speculation, failure-driven escalation, verifier isolation, evidence confidence, impact-aware verification, retry ceilings, and patch minimization.
- Add deterministic task-policy scoring so runtime decisions can be tested independently of model output.
- Extend efficiency/reliability regression coverage for cheap/simple paths, high-risk escalation, speculation pressure, evidence confidence, and repeated-failure stop conditions.

## 0.6.0 (unreleased)

- Add shared agent-team task/status/board contracts for dependency-aware parallel work.
- Add durable job, schedule, plugin-manifest and remote/cloud-run contracts shared by CLI and Server.
- Add route observations and empirical calibration that penalize incorrect completion, latency, token use and tool failures.
- Add OpenTelemetry-compatible span records with dependency-free JSONL fallback.
- Add focused v0.6 contract tests for dependency progression, failure blocking, calibration persistence, schedules and telemetry.

## 0.4.0

- Add adaptive complexity/risk planning, heterogeneous role routing, execution-backed completion evidence, quality metrics and stable cache identities.

## 0.3.0

- Add provider health scoring, circuit breakers, ordered fallback, and retry-safe operation idempotency.
- Add claim-to-source assessment, primary-source ranking, contradiction detection, freshness, diversity, confidence, and consensus scoring.
- Add benchmark observations and task-specific calibrated model selection.
- Add per-hunk transactional review and reversible change-ledger contracts.
- Add hierarchical instruction resolution, expiring memory, MCP transport/tool policy, and multimodal attachment-budget contracts.

## 0.2.0

- Add strict token reservations and provider usage accounting.
- Add provider-neutral compaction with untrusted-state boundaries.
- Preserve OpenAI and Anthropic tool exchanges during compaction.
- Add content-addressed memory and file artifact stores with bounded retrieval.
- Add structured evidence, verification verdicts, and versioned role prompts.
- Add selective multi-agent orchestration contracts.
- Add capability-aware model routing and deterministic recovery decisions.
- Add normalized citation-safe search evidence.
- Add redacted trace/replay primitives and dependency-free evaluation runners.
- Add typed package metadata.
- Remove legacy compatibility contracts.
