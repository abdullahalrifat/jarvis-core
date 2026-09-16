# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifat/jarvis-core/releases)
[![PyPI](https://img.shields.io/pypi/v/jarvis-agent-core.svg)](https://pypi.org/project/jarvis-agent-core/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is a small, typed, dependency-free Python library for building portable AI-agent runtimes. It provides reusable contracts and deterministic runtime primitives without requiring a particular model vendor, application, database, deployment platform, user interface or operating-system sandbox.

The package is designed to be useful **standalone**. Any Python application can install it, implement the provider protocol, and reuse the shared runtime contracts.

## Install

Python 3.10+ is required. The current release is **0.16.1**.

```bash
python -m pip install "jarvis-agent-core==0.16.1"
```

For development:

```bash
git clone https://github.com/abdullahalrifat/jarvis-core.git
cd jarvis-core
python -m pip install -e . -r requirements-dev.txt
python -m pytest
```

## 0.16.1 highlights

The 0.16.1 release adds the cost-aware local-first routing layer and keeps the previous empirical calibration and token-efficiency primitives intact:

- **Cost-aware tier routing** chooses between local, cheap-cloud and frontier tiers using deterministic task signals.
- **Bounded escalation** prevents repeated failures from creating unbounded model retries and escalates only after the configured tier budget is exhausted.
- **Cheapest eligible model selection** allows consumers to select the least expensive enabled model within a tier using estimated input, cached-input and output costs.
- **Verification-aware decisions** mark security-sensitive or elevated-risk work for downstream verification.
- **Provider-neutral design** keeps concrete provider SDKs, credentials, pricing configuration and model execution outside Core.
- **Black formatting compliance** keeps the new routing implementation and tests aligned with the repository's CI formatter.

### Cost-aware routing ownership

Core owns the reusable routing policy; applications map the abstract tiers to concrete providers and models:

```text
Deterministic tools
       │
       ├── no LLM when possible
       │
       ▼
   LOCAL tier
       │
       │ bounded failures / elevated complexity
       ▼
   CHEAP tier
       │
       │ bounded failures / high risk
       ▼
 FRONTIER tier
```

- **Core:** routing signals, tier decisions, failure budgets and cost-aware model selection.
- **AI Stack:** provider execution, concrete model configuration, pricing data, telemetry and persistence.
- **Jarvis:** CLI behavior, workload definitions, user approvals and task-level evaluation.

The intended default for a constrained personal server is local-first execution. Cloud tiers remain opt-in and should only be configured when a stronger model is needed.

The 0.16.0 release added provider-neutral empirical route calibration:

- **Empirical route observations** capture quality, correctness, latency, token usage, cost, tool failures, cache usage, source and timestamp.
- **Recency-weighted scoring** gives recent production evidence more influence than stale observations.
- **Conservative routing safeguards** require a minimum sample count and configurable quality floor before measured evidence can change route selection.
- **Reusable utility scoring** balances quality and reliability with latency, cost and tool failures.
- **Backward-compatible observations** allow existing consumers to continue loading older route evidence.

The 0.15.0 release added provider-neutral primitives for making agent execution more token-efficient and predictable:

- **Context budgets** for bounded prompt/context construction.
- **Deterministic context compilation** so relevant context can be selected and ordered consistently.
- **Agent state ledgers** for compact, structured execution state instead of repeatedly replaying large histories.
- **Token estimation and usage/cost accounting** for requests and accumulated model usage.
- **Route budgets and adaptive routing** so applications can choose an appropriate model based on remaining budget and task signals.
- **Failure and command/file state recording** for compact runtime bookkeeping.

These primitives are intentionally provider-neutral. Anthropic, Ollama, Hugging Face, LiteLLM and other provider integrations remain responsibilities of the consuming application. Provider-specific caching metadata, SDK behavior, credentials and transport logic do not belong in Core.

A typical application can use the primitives to keep the agent loop efficient: retrieve only relevant repository context, keep stable state structured and compact, use lightweight/local models for simple work, escalate to stronger models when task signals justify it, and rely on deterministic tools and verification rather than spending model tokens on work the runtime can perform directly.

See [CHANGELOG.md](CHANGELOG.md) for the complete release history.

## What Core provides

Core contains provider-neutral building blocks for:

- model requests, responses, usage and tool calls;
- provider capability and routing primitives;
- cost-aware local/cheap/frontier routing and empirical route calibration;
- agent capabilities and approval decisions;
- portable sandbox requirements and consumer-owned sandbox executor contracts;
- token accounting, budgets and context compaction;
- artifacts and content-addressed references;
- evidence, verification and completion requirements;
- failure classification, recovery and retry policy;
- multi-agent tasks, teams and orchestration;
- instructions, memory and MCP permission vocabulary;
- schedules, remote-run and execution-state contracts;
- leases, permissions and execution-proof records;
- repository/developer-intelligence primitives;
- evaluation cases, benchmarks and tracing;
- review/change transactions and verification policy;
- reusable sandbox policy and host-boundary validation.

## Common agent brain boundary

Core owns the **meaning** of agent execution: model contracts, tool vocabulary, capabilities, approval semantics, evidence, verification, execution state and portable isolation requirements. Applications own the actual execution adapters.

The Core boundary is deliberately implementation-neutral. A CLI can implement a sandbox with native OS primitives, while a server can implement the same requirements with containers or another isolated worker. Both consume the same policy semantics.

## Provider-neutral model boundary

Core defines the model boundary but never ships a model-provider SDK. Concrete HTTP transports, SDK clients, credentials, endpoint-specific request formatting, retries and provider-specific error handling remain application responsibilities.

## What Core deliberately does not do

Core does not:

- call model APIs;
- store API keys or credentials;
- execute shell commands or arbitrary repository changes;
- provide a database or persistence backend;
- provide a web server, CLI or user interface;
- start MCP processes;
- enforce operating-system isolation itself;
- provide a cloud-worker implementation;
- impose tenancy, deployment or organization policy.

This boundary keeps the package portable and safe to embed in different applications.

## Compatibility and release policy

- semantic versioning is used while the pre-1.0 API stabilizes;
- patch releases should remain compatible within a minor line;
- breaking public contracts require a new minor version while the API remains pre-1.0;
- releases are immutable once published;
- PyPI publication uses GitHub Actions Trusted Publishing;
- the package README is the PyPI project description, so documentation changes intended for PyPI require a new package version;
- every release-worthy change must update `pyproject.toml`, `CHANGELOG.md`, `README.md` when applicable, and relevant `docs/` files in the same PR;
- CI enforces that the package version, changelog entry and README current-release/install version stay synchronized.

### Release flow

```text
code/docs change
    -> version + CHANGELOG + README/docs
    -> CI metadata consistency check
    -> full CI
    -> merge to main
    -> validate exact merged SHA
    -> build wheel + sdist
    -> clean-environment install check
    -> checksums + provenance
    -> GitHub Release
    -> PyPI Trusted Publishing
```

Consumers should depend on a published PyPI version rather than a mutable Git branch. During local development, an editable checkout may be used explicitly.

## Development checks

```bash
python scripts/check_release_consistency.py
black --check src tests scripts
ruff check src tests scripts --select E9,F63,F7,F82
pytest -q --cov=jarvis_core --cov-report=term-missing --cov-fail-under=85
python -m build
python -m twine check dist/*
```

See [docs/contract-boundaries.md](docs/contract-boundaries.md), [docs/cost-aware-routing.md](docs/cost-aware-routing.md), [docs/empirical-calibration.md](docs/empirical-calibration.md), [docs/releasing.md](docs/releasing.md), [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) and [SECURITY.md](SECURITY.md).

## License

Jarvis Core is available under the [MIT License](LICENSE).
