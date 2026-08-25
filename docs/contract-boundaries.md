# Jarvis Core contract boundaries

`jarvis-agent-core` is the provider-neutral contract/runtime library shared by
standalone Jarvis and optional AI Stack Server. It deliberately does **not** own
filesystem tools, subprocess execution, cloud worker processes, durable
databases, channel adapters, UI, OS sandbox implementation or provider
credentials.

## What Core v0.8.0 owns

Core v0.8.0 provides stable vocabulary/deterministic primitives for:

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

A Core dataclass/helper is not a runtime security boundary by itself. Consumers
must connect contracts to the actual execution path.

Examples:

- tool approval policy is checked before dispatch;
- lease/fencing token participates in every heartbeat/state/completion durable
  predicate;
- permission decisions wrap actual mutation/command/browser/MCP tools;
- proof derives from successful/failed tool/test execution rather than model
  claims;
- provider credentials remain outside portable task/handoff payloads;
- sandbox/network/workspace trust is implemented by the consumer OS/runtime;
- cancellation reaches owned model/process/tool work;
- artifact/proof access is authorized by the product control plane.

Consumer tests must therefore verify both Core contract behavior and end-to-end
enforcement.

## Trust model

Core treats repository, web, connector and model content as data. Runtime
consumers should keep privilege-granting policy in a user/operator-owned control
plane. Repository configuration is restrict-only unless a separate explicit
workspace-trust mechanism is designed and audited.

A model output cannot increase a budget, grant a side-effect capability, change
its own provider credential source or claim verification without execution
evidence.

## v0.9 design boundary

The dated v0.9 audit identified portable semantics that should be shared before
Jarvis/Server implement richer live execution independently:

- complete inference-route identity;
- versioned agent event envelopes;
- idempotent steer/interrupt/approval commands;
- typed side-effect capabilities;
- explicit verification `not_run|passed|failed|blocked` states;
- hard run/session budget snapshots and decisions;
- portable process lifecycle state;
- exact run/task/attempt/lease/proof identity;
- immutable Skill/plugin lock identity;
- credential-free local/cloud handoff descriptors.

These are **design targets**, not claims about Core 0.8.0. See
[v0.9-world-class-contracts.md](v0.9-world-class-contracts.md).

Core should define only the portable state/decision vocabulary. Jarvis owns local
streaming/process/browser/repository enforcement. Server owns durable event,
tenant, queue, lease, approval and artifact enforcement.

## Release ordering

Coordinated releases follow this order:

1. merge and validate Core contracts;
2. publish immutable Core release artifact/checksum/provenance;
3. pin Jarvis and Server to that exact artifact;
4. execute consumer compatibility/unit/integration/cross-repository gates;
5. release consumers only after the exact pinned configuration is validated.

Verified Core v0.8.0 wheel SHA-256:

```text
d9569b69385e58a681ea01e900eb81c395d3f202a09a92878eb82bf4d4b8618a
```

A consumer source tree importing new contracts while packaging an older Core
wheel is a release defect even if development tests accidentally import a local
checkout.

## Maturity language

Core feature presence is not a claim that Jarvis or Server is production-ready.
Runtime maturity requires executable compatibility, malformed-input,
timeout/cancellation, permission, cleanup, recovery and security tests plus
retained benchmark evidence.

A planned contract in a design document is `NOT STARTED` until implemented and
validated in Core; it does not automatically become `INTEGRATED` when a consumer
has a similar local type.
