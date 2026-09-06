# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifat/jarvis-core/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is the small typed dependency-free Python contract/runtime library shared by standalone Jarvis and AI Stack Server. It standardizes portable agent behavior without owning product-specific tools, storage, credentials, deployment policy or OS isolation.

The current published release is **Core 0.9.3**. The pending evidence-independence fix in this branch is prepared as **Core 0.9.4** and must be released only after this PR is merged and the release workflow validates the exact release commit.

## Install

Python 3.10+ is required. For the currently published v0.9.3 release, install the exact immutable release artifact from the GitHub Releases page. After PR #23 is merged and v0.9.4 is published, update consumers to the v0.9.4 wheel and its generated SHA-256 checksum; do not guess or pre-publish a checksum.

```bash
python -m pip install "jarvis-agent-core @ https://github.com/abdullahalrifat/jarvis-core/releases/download/v0.9.3/jarvis_agent_core-0.9.3-py3-none-any.whl"
```

The release asset is checksum-addressed in consumer lockfiles so consumers do not depend on a mutable branch or checkout.

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

A Core field is not automatically a security control. Consumers must enforce approval before dispatch, durable lease predicates for cloud state, real execution-derived proof, and credential isolation. Independent evidence must also have a verifiable identity and must not be satisfied by reference-only or duplicate evidence for the same claim.

## Compatibility and release policy

- semantic versioning is used while the pre-1.0 API stabilizes;
- patch releases should remain compatible within a minor line;
- breaking contracts require coordinated Core/Jarvis/Server releases;
- publish Core first, then pin consumers to the immutable released artifact/checksum;
- an existing GitHub Release is never silently replaced.

Current coordinated line:

| Core | Jarvis | AI Stack Server | Python |
| --- | --- | --- | --- |
| **0.9.3 published / 0.9.4 pending** | **0.9.1** | **0.9.3 consumer target** | 3.10+ |

After v0.9.4 is released, consumer repositories must be updated to the exact v0.9.4 artifact and checksum before their coordinated release is declared current.

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

A new package version merged to `main` is built/validated and, when the tag/version does not already exist, published as a GitHub Release with checksums and build-provenance attestations. Existing immutable releases are never replaced. v0.9.4 must not be referenced as a published artifact until the release workflow has completed successfully.

## License

Jarvis Core is available under the [MIT License](LICENSE).
