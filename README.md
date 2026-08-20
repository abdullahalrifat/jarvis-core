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
changes. Jarvis and Server implement those concerns independently so a local CLI
never inherits remote-control-plane requirements.

## Basic examples

```python
from jarvis_core import (
    CapabilityRegistry,
    ModelCapabilities,
    ModelProfile,
    classify_failure,
)

registry = CapabilityRegistry([
    ModelProfile(
        name="coder",
        provider="openai",
        model="open-coder",
        base_url="https://models.example/v1",
        priority=10,
        capabilities=ModelCapabilities(
            tool_calling=True,
            structured_output=True,
            context_tokens=131_072,
        ),
    )
])
profile = registry.select(required=("tool_calling",))
decision = classify_failure("503 gateway unavailable")
```

Use `compact_messages` before an endpoint context overflow,
`normalize_search_results` plus `citation_context` for web evidence,
`TraceRecorder` for redacted replay data, and `run_evals` for deterministic
regression cases.

## Release and compatibility

Jarvis and Server pin a compatible minor range. Release Core first, publish it,
then validate and release each consumer. There is intentionally no legacy
compatibility layer: incompatible contract changes require a major version or a
coordinated pre-1.0 minor release.

See [CHANGELOG.md](CHANGELOG.md). Every contract must remain provider-neutral,
bounded, serializable, and covered by tests.
