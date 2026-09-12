# Core contract boundaries

`jarvis-agent-core` is a standalone, provider-neutral contract and runtime library. It can be embedded by any Python application that needs common agent semantics without taking a dependency on a particular provider SDK, database, deployment platform or user interface.

## What Core owns

Core provides stable vocabulary and deterministic primitives for:

- token/context budgets, compaction and artifact references;
- provider/model capabilities, routing and benchmark observations;
- provider-neutral model requests, responses, usage and tool calls;
- evidence, verification and quality contracts;
- resilience, provider health and failure policy;
- multi-agent role/task/result contracts;
- MCP server/tool permission types;
- instructions, memory and attachment descriptors;
- jobs, schedules, remote-run and platform contracts;
- execution states and transition validation;
- lease fencing tokens and attempt ownership vocabulary;
- proof/evidence ledger types;
- deterministic permission decisions;
- reusable sandbox policy and host-boundary validation;
- evaluation, tracing and review primitives.

## What applications must implement

A Core dataclass or helper does not enforce a runtime security boundary by itself. The embedding application is responsible for connecting contracts to the real execution path.

Examples:

- approval requirements must be checked before privileged tools are dispatched;
- lease/fencing tokens must participate in every persistent worker state predicate;
- permission decisions must wrap the actual mutation, command, browser or connector tool;
- proof records must derive from tool/test execution rather than model self-report;
- provider credentials must remain outside portable task payloads;
- sandbox, network and workspace-trust decisions must be enforced by the host application.

## Provider boundary

The `ModelProvider` protocol is the stable application boundary. An implementation receives a `ModelRequest` and returns a `ModelResponse`. Core provides normalization helpers but deliberately does not implement HTTP transports or provider SDK clients.

An application may therefore choose any model backend while keeping its agent logic expressed in Core contracts.

## Trust model

Core treats repository, web, connector and model content as data. It provides policy vocabulary but does not designate external content as trusted. Applications should keep privilege-granting policy in an operator-controlled boundary and treat untrusted content as incapable of expanding permissions.

## Release ordering

1. validate the Core change on the exact commit;
2. publish the immutable package artifact;
3. verify the published artifact and checksum;
4. update embedding applications to the exact released package;
5. execute application compatibility and integration gates.

A source tree that imports a newer Core API while packaging an older Core wheel is a release defect.

## Maturity language

Core feature presence is not a production-readiness claim for an embedding application. Production readiness depends on the host application's executable compatibility, malformed-input, timeout/cancellation, permission, recovery and security tests plus retained quality evidence.
