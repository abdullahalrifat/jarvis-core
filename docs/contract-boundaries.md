# Jarvis Core contract boundaries

`jarvis-agent-core` is the provider-neutral contract library shared by the standalone Jarvis CLI and the optional AI Stack Server. It deliberately does **not** own filesystem tools, subprocess execution, cloud worker processes, durable databases, channel adapters, UI, OS sandbox implementation or provider credentials.

## What Core owns

Core v0.8.0 provides stable vocabulary and deterministic primitives for areas such as:

- token/context budgets, compaction and artifact references;
- provider/model capabilities, routing and benchmark observations;
- evidence, verification and quality contracts;
- resilience/provider health and failure policy;
- multi-agent role/task/result contracts;
- MCP server/tool permission types;
- instructions, memory and attachment descriptors;
- jobs/schedules/remote-run/platform contracts;
- execution states and transition validation;
- lease fencing tokens and attempt ownership vocabulary;
- proof/evidence ledger types;
- deterministic permission decisions;
- conventional cron semantics.

## What consumers must enforce

A Core dataclass or helper does not enforce a runtime security boundary by itself. Consumers are responsible for connecting contracts to the real execution path.

Examples:

- `ToolPermission.requires_approval` must be checked before a CLI/Server MCP call is dispatched;
- a lease/fencing token must be included in every worker heartbeat/state/completion database predicate;
- permission decisions must wrap the actual mutation/command/browser/MCP tools;
- proof records must derive from tool/test execution rather than model self-report;
- provider credentials must remain outside portable cloud task payloads;
- sandbox/network and workspace-trust decisions are runtime responsibilities, not Core contracts.

Consumer tests should therefore verify both contract behavior and end-to-end enforcement.

## Trust model

Core treats repository, web, connector and model content as data. It provides policy vocabulary but does not designate repository configuration as trusted. Runtime consumers should keep privilege-granting policy in a user/operator-owned control plane and allow repository configuration only to restrict permissions unless an explicit workspace-trust decision has been made.

## Release ordering

Coordinated releases follow this order:

1. merge and validate Core contracts;
2. publish an immutable Core release artifact and checksum;
3. pin Jarvis and Server to that exact artifact;
4. execute consumer compatibility/unit/integration/cross-repository gates;
5. release consumers only after the exact pinned configuration is validated.

The verified Core v0.8.0 wheel SHA-256 is:

```text
d9569b69385e58a681ea01e900eb81c395d3f202a09a92878eb82bf4d4b8618a
```

A consumer source tree that imports v0.8 contracts while packaging an older Core wheel is a release defect even if development tests happen to import a checkout.

## Maturity language

Core feature presence should not be interpreted as a claim that Jarvis or Server is production-ready. Runtime maturity requires executable compatibility, malformed-input, timeout/cancellation, permission, recovery and security tests plus retained benchmark evidence. See each consumer repository for its own readiness status.
