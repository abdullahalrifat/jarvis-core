# Jarvis Core

[![Validate](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml/badge.svg)](https://github.com/abdullahalrifat/jarvis-core/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/abdullahalrifat/jarvis-core)](https://github.com/abdullahalrifat/jarvis-core/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`jarvis-agent-core` is the small, typed, dependency-free Python runtime shared
by standalone [Jarvis](https://github.com/abdullahalrifat/jarvis) and
[AI Stack Server](https://github.com/abdullahalrifat/ai-stack). It standardizes
portable agent behavior without owning product-specific tools, storage,
permissions, credentials, or deployment policy.

The project is public and MIT-licensed. You may use it in your own agent,
automation, research, or developer-tool project.

## Install

Python 3.10 or newer is required. Until PyPI publication is available, install
the signed release artifact:

```bash
python -m pip install \
  "jarvis-agent-core @ https://github.com/abdullahalrifat/jarvis-core/releases/download/v0.2.0/jarvis_agent_core-0.2.0-py3-none-any.whl#sha256=285cddb3b5ce917d4acd406825bfd640e3bb3d1a5f66fec01580f4edbdb68bf6"
```

Or install a checkout for development:

```bash
git clone https://github.com/abdullahalrifat/jarvis-core.git
cd jarvis-core
python -m pip install -e . -r requirements-dev.txt
python -m pytest
```

## Capabilities

Core provides:

- atomic token reservations, refunds, and provider usage accounting;
- provider-neutral context compaction that preserves OpenAI and Anthropic
  tool-call/result groups;
- untrusted-state boundaries for repository, attachment, connector, and web
  content;
- content-addressed memory/file artifacts with bounded retrieval;
- structured evidence ledgers and verification verdicts;
- versioned role prompts and selective multi-agent orchestration contracts;
- model capability profiles and deterministic selection;
- failure classification and bounded recovery decisions;
- normalized citation-aware search evidence;
- redacted, replayable JSONL trace events;
- dependency-free evaluation cases, scoring, and runners.

Core deliberately does not access files, execute commands, call model
endpoints, start MCP processes, persist product sessions, enforce tenancy, or
approve changes. Consumers supply those backends and policies.

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
reservation = ledger.reserve("implementer", input_tokens=2_000, output_tokens=500)

# Call your provider, then account for its reported usage.
ledger.commit(
    reservation,
    Usage(agent="implementer", model="my-model", input_tokens=650, output_tokens=180),
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

The package exports typed contracts from `jarvis_core`. See
[`src/jarvis_core/__init__.py`](src/jarvis_core/__init__.py) for the supported
top-level import surface and the tests for executable examples.

## Compatibility policy

- Versioning follows semantic versioning while the public API stabilizes.
- Patch releases should remain compatible within the same minor line.
- Deprecations are documented in [CHANGELOG.md](CHANGELOG.md).
- Breaking contracts require a coordinated Core, Jarvis, and Server release.
- Jarvis and Server must pin an exact verified release artifact or a compatible
  published minor range.

Current consumer compatibility:

| Core | Jarvis | AI Stack Server | Python |
| --- | --- | --- | --- |
| 0.2.x | Current `main` | Current `main` | 3.10+ |

## Development and contribution

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change. All
contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).

```bash
black --check src tests
ruff check src tests --select E9,F63,F7,F82
pytest -q --cov=jarvis_core --cov-report=term-missing --cov-fail-under=85
python -m build
python -m twine check dist/*
```

Use GitHub Issues for reproducible bugs and focused feature requests. Read
[SUPPORT.md](SUPPORT.md) for support boundaries. Report vulnerabilities
privately according to [SECURITY.md](SECURITY.md).

## Releases and supply chain

Merging a new version to `main` runs validation and creates a GitHub Release
when that version is new. The workflow builds the wheel and source archive,
creates SHA-256 checksums, and publishes build-provenance attestations. PyPI is
an optional additional channel and cannot block the GitHub Release.

Release consumers should use the immutable artifact URL plus SHA-256 shown
above. Increment `project.version` for every release; an existing release is
never replaced automatically.

## License

Jarvis Core is available under the [MIT License](LICENSE).
