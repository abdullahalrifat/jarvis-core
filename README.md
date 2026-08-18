# Jarvis Core

Shared, dependency-free agent runtime used by the standalone Jarvis CLI and AI
Stack Server.

## Capabilities

- model-independent token estimation and enforceable run/agent/turn budgets;
- usage ledger with cached-input, tool, output, and compaction accounting;
- structured tool-result summaries and deterministic transcript compaction;
- content-addressed artifacts for large evidence and command output;
- delta-context construction that avoids replaying unchanged material;
- selective Explorer -> Implementer -> Verifier orchestration.

The package contains no filesystem or process tools. Consumers supply their own
model backend and product-specific tools.

```bash
pip install jarvis-agent-core
pytest
```
