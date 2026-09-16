# Changelog

## 0.16.1

### Features

- Add provider-neutral cost-aware local/cheap/frontier tier routing.
- Add bounded failure-budget escalation from local to cheap and frontier tiers.
- Add cheapest eligible model selection using input, cached-input and output cost estimates.
- Add verification requirements for elevated-risk and security-sensitive routing decisions.
- Keep provider SDKs, credentials, pricing configuration and execution adapters outside Core.

### Documentation

- Document the local-first hybrid routing policy and tier ownership.
- Align README and PyPI project documentation with the new routing primitives.

### Maintenance

- Format the new routing implementation and tests with the repository's Black configuration.
- Bump the package version to 0.16.1.

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

### Documentation

- Document the token-efficient runtime capabilities and release in the README.

## 0.14.0

### Features

- Add provider-neutral background-process handles and lifecycle states.
- Add live steering and checkpoint contracts for pause/resume/cancel/redirect/rewind controls.
- Add deterministic checkpoint identities and a helper for translating real execution observations into Core evidence.

### Architecture

- Keep execution meaning and evidence semantics in Core while leaving process spawning, OS isolation, persistence and provider integrations to Core consumers.
- Treat real command and test observations as evidence inputs; model prose remains non-authoritative.

## 0.13.0

### Features

- Add provider-neutral capability and approval primitives for shared agent runtimes.
- Add portable sandbox requirements and a consumer-owned `SandboxExecutor` protocol.
- Keep platform enforcement in consumers while making capability, approval and isolation semantics common Core contracts.

### Architecture

- Establish Core as the common agent brain: contracts and policy semantics live here; CLI/server execution adapters remain consumer-owned.
- Avoid duplicating execution-state semantics: the existing autonomous execution lifecycle remains the canonical shared state machine.

## 0.12.0

### Features

- Extend the provider-neutral model boundary with reusable usage, tool-call and response normalization helpers.
- Export the normalization helpers from the public Core API so independent agent applications can share canonical model semantics.
- Keep the provider contract dependency-free and suitable for any application or integration.

### Architecture

- Core owns provider-neutral contracts and reusable runtime primitives only.
- Provider SDKs, HTTP transports, credentials, persistence, user interfaces, deployment and operating-system enforcement remain outside Core.
- Core documentation is standalone and does not depend on or name downstream/private applications.
