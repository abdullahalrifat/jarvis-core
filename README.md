# Jarvis Core

`jarvis-agent-core` is the small, dependency-free runtime shared by standalone
Jarvis and AI Stack Server. It standardizes agent behavior without sharing
product-specific tools, storage, permissions, or deployment policy.

## Install

```bash
pip install jarvis-agent-core
```

Python 3.10+ is required. The package is typed and has no runtime dependencies.

## What it owns

- atomic token reservations, refunds, and provider usage accounting;
- provider-neutral context compaction that preserves OpenAI and Anthropic tool
  call/result groups;
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

## What it does not own

Jarvis Core does not access files, execute commands, call model endpoints, start
MCP processes, persist product sessions, enforce Server tenancy, or approve
changes. Jarvis and Server implement those concerns independently.

## Automated releases

Merging a new version to `main` is sufficient. The Release workflow:

1. validates the version and distributions;
2. builds the wheel and source archive;
3. creates SHA-256 checksums and build-provenance attestations;
4. creates `v<project.version>` and the GitHub Release when that version is new;
5. uploads all artifacts without depending on PyPI.

Repeated pushes with the same project version leave the existing release
unchanged. Increment `project.version` for every new release.

PyPI publication is optional. After Trusted Publishing is repaired, set the
repository variable `PUBLISH_PYPI=true`, or manually dispatch the Release
workflow with `publish_pypi` enabled. A PyPI problem cannot block the GitHub
Release.

Consumers may temporarily install the immutable GitHub wheel or a full commit
archive. Jarvis and Server CI bootstrap the pinned Core commit automatically;
developers do not run a separate installation command.

## Release compatibility

Jarvis and Server pin a compatible minor range. Release Core first, then
validate and release each consumer. There is intentionally no legacy
compatibility layer: incompatible contracts require a coordinated version
change.
