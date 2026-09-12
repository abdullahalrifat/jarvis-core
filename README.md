# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifat/jarvis-core/releases)
[![PyPI](https://img.shields.io/pypi/v/jarvis-agent-core.svg)](https://pypi.org/project/jarvis-agent-core/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is the small typed dependency-free Python contract/runtime library shared by standalone Jarvis and AI Stack Server. It standardizes portable agent behavior without owning product-specific tools, storage, credentials, deployment policy or OS isolation.

## Install

Python 3.10+ is required. The current Core release is **0.10.1**:

```bash
python -m pip install "jarvis-agent-core==0.10.1"
```

For development:

```bash
git clone https://github.com/abdullahalrifat/jarvis-core.git
cd jarvis-core
python -m pip install -e . -r requirements-dev.txt
python -m pytest
```

## Capabilities

Core provides typed deterministic contracts/primitives for token accounting, context compaction, artifacts, evidence/verification, model routing/calibration, failure recovery, multi-agent orchestration, instructions/memory, MCP permissions, schedules/remote execution, leases, proof records, citations and evaluation cases. The 0.10.x line also exposes the shared per-task sandbox policy used by Jarvis and AI Stack Server.

Core deliberately does **not** access repositories, execute commands, call model endpoints, start MCP processes, persist product sessions, run cloud workers, enforce tenancy, or approve changes. Jarvis/Server must wire contracts into the real execution path; OS sandbox enforcement remains a consumer/runtime responsibility.

See [docs/contract-boundaries.md](docs/contract-boundaries.md) for the enforcement and trust boundary.

## Contract enforcement matters

A Core field is not automatically a security control. Consumers must enforce approval before dispatch, durable lease predicates for cloud state, real execution-derived proof, and credential isolation. Independent evidence must also have a verifiable identity and must not be satisfied by reference-only or duplicate evidence for the same claim.

## Compatibility and release policy

- semantic versioning is used while the pre-1.0 API stabilizes;
- patch releases should remain compatible within a minor line;
- breaking contracts require coordinated Core/Jarvis/Server releases;
- publish Core first, then pin consumers to the released package version;
- an existing GitHub Release is never silently replaced;
- PyPI publication uses GitHub Actions Trusted Publishing; no long-lived PyPI API token is stored in GitHub.

Current release coordination:

| Component | Version |
| --- | --- |
| Core | **0.10.1** |
| Jarvis | update to **0.10.1 Core** after the Core release is published |
| AI Stack Server | update to **0.10.1 Core** after the Core release is published |
| Python | 3.10+ |

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

Core releases are versioned explicitly. A version bump merged to `main` is validated against the exact commit, built as a wheel and sdist, checked with Twine, smoke-tested in a clean environment, checksummed, provenance-attested and published as a GitHub Release. The same release workflow then publishes the exact validated distributions to PyPI using Trusted Publishing. Existing immutable releases are never replaced.

### Release flow

```text
version/documentation PR
    -> CI
    -> merge to main
    -> validate exact merged SHA
    -> build wheel/sdist
    -> clean-environment install check
    -> SHA-256 checksums + provenance attestation
    -> GitHub Release vX.Y.Z
    -> PyPI Trusted Publishing
    -> consumer repositories update their pinned Core version
```

For an already-created GitHub release that needs a publication retry, maintainers can use the `workflow_dispatch` input on `.github/workflows/release.yml` and select the immutable release tag. This is for republishing an existing version only; a documentation or code correction must use a new semantic version.

Consumers should depend on the PyPI package rather than a Git checkout or mutable branch. During local development, use an editable install of a checked-out `jarvis-core` repository.

## License

Jarvis Core is available under the [MIT License](LICENSE).
