# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifafit/jarvis-core/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is the small typed dependency-free Python contract/runtime library shared by standalone Jarvis and AI Stack Server. It standardizes portable agent behavior without owning product-specific tools, storage, credentials, deployment policy or OS isolation.

The current coordinated release is **Core 0.9.2**.

## Install

Python 3.10+ is required. The verified v0.9.2 release wheel is:

```bash
python -m pip install \
  "jarvis-agent-core @ https://github.com/abdullahalrifat/jarvis-core/releases/download/v0.9.2/jarvis_agent_core-0.9.2-py3-none-any.whl#sha256=0ff9b5cfba29dca8d05df69a48573c3a69cc73ca9654e7122411b89a489f1130"
```

The release asset is checksum-addressed so consumers do not depend on a mutable branch or checkout.

For development:

```bash
git clone https://github.com/abdullahalrifat/jarvis-core.git
cd jarvis-core
python -m pip install -e . -r requirements-dev.txt
python -m pytest
```

## Capabilities

Core provides typed deterministic contracts/primitives for token accounting, context compaction, artifacts, evidence/verification, model routing/calibration, failure recovery, multi-agent orchestration, instructions/memory, MCP permissions, schedules/remote execution, leases, proof records, citations and evaluation cases.

Core deliberately does **not** access repositories, execute commands, call model endpoints, start MCP processes, persist product sessions, run cloud workers, enforce tenancy, implement OS sandboxes or approve changes. Jarvis/Server must wire contracts into the real execution path.

See [docs/contract-boundaries.md](docs/contract-boundaries.md) for the enforcement and trust boundary.

## Contract enforcement matters

A Core field is not automatically a security control. Consumers must enforce approval before dispatch, durable lease predicates for cloud state, real execution-derived proof, and credential isolation.

## Compatibility and release policy

- semantic versioning is used while the pre-1.0 API stabilizes;
- patch releases should remain compatible within a minor line;
- breaking contracts require coordinated Core/Jarvis/Server releases;
- publish Core first, then pin consumers to the immutable released artifact/checksum;
- an existing GitHub Release is never silently replaced.

Current coordinated line:

| Core | Jarvis | AI Stack Server | Python |
| --- | --- | --- | --- |
| **0.9.2** | **0.9.1** | **0.9.2 contract consumer** | 3.10+ |

The 0.9.2 release is the source of truth for the current consumer pin. Consumer CI verifies the exact version/checksum rather than a mutable branch.

## Development

```bash
black --check src tests
ruff check src tests --select E9,F63,F7,F82
pytest -q --cov=jarvis_core --cov-report=term-missing --cov-fail-under=85
python -m build
python -m twine check dist/*
```

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md) before contributing/reporting issues.

## Releases and supply chain

A new package version merged to `main` is built/validated and, when the tag/version does not already exist, published as a GitHub Release with checksums and build-provenance attestations. Existing immutable releases are never replaced.

## License

Jarvis Core is available under the [MIT License](LICENSE).
