# Changelog

## 0.14.0

### Features

- Add provider-neutral background-process handles and lifecycle states.
- Add live steering and checkpoint contracts for pause/resume/cancel/redirect/rewind controls.
- Add deterministic checkpoint identities and a helper for translating real execution observations into Core evidence.

### Architecture

- Keep execution meaning and evidence semantics in Core while leaving process spawning, OS isolation, persistence and provider integrations to consumers.
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

### Documentation
