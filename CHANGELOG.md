# Changelog

## 0.16.0

### Features

- Centralize empirical route calibration as a provider-neutral Core primitive.
- Add runtime/benchmark observation metadata for quality, cache usage, source and timestamp.
- Add 30-day recency weighting, minimum sample safeguards and configurable quality floors.
- Keep cost, latency, correctness and tool failures in one reusable route utility score.
- Preserve compatibility with existing route observations and downstream consumers.

### Architecture

- `jarvis-core` owns the reusable calibration algorithm and observation contract.
- AI Stack owns model execution, provider telemetry and persistence adapters.
- Jarvis owns real workload definitions and task-level evaluation.
- Downstream repositories must reuse Core calibration rather than maintain a second routing algorithm.

## 0.15.0

### Features

- Add token-efficient agent runtime primitives for bounded context and model usage.
- Add context budgeting across stable instructions, task state, evidence and history.
- Add deterministic context compilation with deduplication and relevance ranking.
- Add an agent state ledger for inspected files, executed commands, failures and decisions to avoid repeated work.
- Add provider-neutral usage and cost accounting, including cache-aware token accounting.
- Add route budgets and adaptive model routing based on task complexity, risk and uncertainty.
- Add request token estimation before model execution.

### Architecture

- Keep token-efficiency policy and accounting provider-neutral in Core.
- Keep provider SDKs, transports, credentials and deployment-specific routing outside Core.
- Reuse existing context compaction, artifact handling, escalation and reliability primitives instead of duplicating them.
- Enable consumers to combine deterministic tooling, local models and cloud models while minimizing unnecessary model context.

## 0.14.0

### Features

- Add provider-neutral background-process handles and lifecycle states.
- Add live steering and checkpoint contracts for pause/resume/cancel/redirect/rewind controls.
- Add deterministic checkpoint identities and a helper for translating real execution observations into Core evidence.

### Architecture

- Keep execution meaning and evidence semantics in Core while leaving process spawning, OS isolation, persistence and provider integrations to consumers.
- Treat real command and test observations as evidence inputs; model prose remains non-authoritative.
