# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifat/jarvis-core/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is the small typed dependency-free Python contract/runtime library shared by standalone [Jarvis](https://github.com/abdullahalrifat/jarvis) and [AI Stack Server](https://github.com/abdullahalrifat/ai-stack). It standardizes portable agent behavior without owning product-specific tools, storage, credentials, deployment policy or OS isolation.

The project is public and MIT-licensed.

## Install

Python 3.10+ is required. The verified v0.8.0 release wheel is:

```bash
python -m pip install \
  "jarvis-agent-core @ https://github.com/abdullahalrifat/jarvis-core/releases/download/v0.8.0/jarvis_agent_core-0.8.0-py3-none-any.whl#sha256=d9569b69385e58a681ea01e900eb81c395d3f202a09a92878eb82bf4d4b8618a"
```

The wheel was independently downloaded, installed and checked against the release `SHA256SUMS` during the v0.8 post-merge audit.

For development:

```bash
git clone https://github.com/abdullahalrifat/jarvis-core.git
cd jarvis-core
python -m pip install -e . -r requirements-dev.txt
python -m pytest
```

## Capabilities

Core provides typed deterministic contracts/primitives for:

- token budgets/reservations/refunds/provider usage accounting;
- provider-neutral context compaction preserving OpenAI/Anthropic tool groups;
- bounded content-addressed artifact references and retrieval;
- evidence ledgers, verification verdicts and quality measurements;
- model capability profiles, routing, calibration and benchmark observations;
- failure classification, bounded recovery and resilience/provider health;
- multi-agent roles/tasks/results and adaptive execution decisions;
- hierarchical instructions, expiring memory and attachment descriptors;
- persistent MCP server/tool permission vocabulary;
- team/job/schedule/remote/platform contracts;
- deterministic execution states/transitions;
- attempt-scoped lease fencing tokens;
- proof-ledger and permission-decision contracts;
- conventional cron semantics including Sunday `0/7` and DOM/DOW OR behavior;
- normalized citation-aware search evidence, redacted trace types and eval cases.

Core deliberately does **not** access repositories, execute commands, call model endpoints, start MCP processes, persist product sessions, run cloud workers, enforce tenancy, implement OS sandboxes or approve changes. Jarvis/Server must wire contracts into the real execution path.

See [docs/contract-boundaries.md](docs/contract-boundaries.md) for the enforcement and trust boundary.

## Contract enforcement matters

A Core field is not automatically a security control. Examples:

- `ToolPermission.requires_approval` must be enforced by the consumer before dispatch;
- cloud heartbeat/state/completion must include the current lease fence in durable database predicates;
- permission decisions must wrap actual tool mutations;
- proof should derive from successful tool/test execution rather than model claims;
- provider credentials must stay outside portable task payloads.

Consumer compatibility and end-to-end enforcement tests are therefore required in addition to Core unit tests.

## Library example

```python
from jarvis_core import (
    CapabilityRegistry,
    ModelCapabilities,
    ModelProfile,
    TokenBudget,
    TokenLedger,
    Usage,
)

ledger = TokenLedger(TokenBudget(max_run_input=10_000, max_run_output=2_000))
reservation = ledger.reserve(
    "implementer", input_tokens=2_000, output_tokens=500
)
ledger.commit(
    reservation,
    Usage(
        agent="implementer",
        model="my-model",
        input_tokens=650,
        output_tokens=180,
    ),
)

registry = CapabilityRegistry()
registry.add(
    ModelProfile(
        name="local-coder",
        provider="openai",
        model="my-model",
        base_url="http://127.0.0.1:8000/v1",
        capabilities=ModelCapabilities(tool_calling=True),
    )
)
```

See [`src/jarvis_core/__init__.py`](src/jarvis_core/__init__.py) for the supported top-level import surface and tests for executable examples.

## Compatibility and release policy

- semantic versioning is used while the pre-1.0 API stabilizes;
- patch releases should remain compatible within a minor line;
- deprecations are documented in [CHANGELOG.md](CHANGELOG.md);
- breaking contracts require coordinated Core/Jarvis/Server releases;
- publish Core first, then pin consumers to the immutable released artifact/checksum and execute consumer/cross-repository gates;
- an existing GitHub Release is never silently replaced.

Current coordinated line:

| Core | Jarvis | AI Stack Server | Python |
| --- | --- | --- | --- |
| 0.8.0 | v0.8.x consumer | v0.8.x consumer | 3.10+ |

The consumer v0.8.1 audit specifically corrected a release drift where merged v0.8 source still packaged Core 0.7.0. The release-order rule above is now documented and consumer regressions enforce the pin.

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

A new package version merged to `main` is built/validated and, when the tag/version does not already exist, published as a GitHub Release with checksums and build-provenance attestations. PyPI is optional.

Docs-only pushes with unchanged `project.version` may execute the Release workflow, but the workflow detects the existing v0.8.0 release and leaves its immutable assets unchanged.

## License

Jarvis Core is available under the [MIT License](LICENSE).
