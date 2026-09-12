# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifat/jarvis-core/releases)
[![PyPI](https://img.shields.io/pypi/v/jarvis-agent-core.svg)](https://pypi.org/project/jarvis-agent-core/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is a small, typed, dependency-free Python library for building portable AI-agent runtimes. It provides reusable contracts and deterministic runtime primitives without requiring a particular model vendor, application, database, deployment platform, user interface or operating-system sandbox.

The package is designed to be useful **standalone**. Any Python application can install it, implement the provider protocol, and reuse the shared runtime contracts.

## Install

Python 3.10+ is required. The current release is **0.13.0**.

```bash
python -m pip install "jarvis-agent-core==0.13.0"
```

For development:

```bash
git clone https://github.com/abdullahalrifat/jarvis-core.git
cd jarvis-core
python -m pip install -e . -r requirements-dev.txt
python -m pytest
```

## What Core provides

Core contains provider-neutral building blocks for:

- model requests, responses, usage and tool calls;
- provider capability and routing primitives;
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

```text
                    jarvis-agent-core
                ┌────────────────────────┐
                │ Model / tool contracts  │
                │ Capabilities / approval │
                │ Execution state / proof │
                │ Evidence / verification│
                │ Sandbox requirements   │
                └───────────┬────────────┘
                            │
              ┌─────────────┴──────────────┐
              │                            │
       local application             server application
       CLI / OS sandbox              API / worker / Docker
```

The Core boundary is deliberately implementation-neutral. A CLI can implement a sandbox with native OS primitives, while a server can implement the same requirements with containers or another isolated worker. Both consume the same policy semantics.

## Provider-neutral model boundary

Core defines the model boundary but never ships a model-provider SDK.

```text
Your application
      │
      │ implements ModelProvider
      ▼
┌──────────────────────────────┐
│        jarvis-agent-core     │
│ ModelRequest / Response      │
│ ModelUsage / ToolCall        │
│ ModelProvider                │
│ normalization helpers        │
│ runtime contracts/primitives │
└──────────────────────────────┘
```

Concrete HTTP transports, SDK clients, credentials, endpoint-specific request formatting, retries and provider-specific error handling remain application responsibilities.

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
- the package README is the PyPI project description, so documentation changes intended for PyPI require a new package version.

### Release flow

```text
code/docs change
    -> CI
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
black --check src tests
ruff check src tests --select E9,F63,F7,F82
pytest -q --cov=jarvis_core --cov-report=term-missing --cov-fail-under=85
python -m build
python -m twine check dist/*
```

See [docs/contract-boundaries.md](docs/contract-boundaries.md), [docs/releasing.md](docs/releasing.md), [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

Jarvis Core is available under the [MIT License](LICENSE).
