# Lineage and extension contract

`jarvis-agent-core` is intentionally provider-neutral. `AgentLineage` and `LineageProof` provide a stable parent/child delegation contract without introducing HTTP, Git, IDE, scheduler or model-provider dependencies.

A parent creates a child lineage node with:

- `parent_task_id`
- `root_task_id`
- `depth`
- `role`

A child result can be bound to evidence digests through `LineageProof`. The proof digest makes changes to the lineage or evidence detectable.

Applications can therefore add parallel subagents, reviewers, research agents or remote workers without changing Core when the model/provider changes.

## Boundary

Core owns portable contracts, validation and reusable runtime primitives. The embedding application owns user experience, transport, persistence, scheduling, credentials, provider adapters and infrastructure enforcement.

## Extension rule

New reusable behavior belongs in Core only when it is provider-neutral, application-agnostic and testable without external services. Provider SDKs, network clients, databases and deployment-specific implementations stay outside Core.

## CI

The formatting gate uses Black's diff mode so a future formatting regression identifies the exact source transformation required in the CI log.
