# Changelog

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
