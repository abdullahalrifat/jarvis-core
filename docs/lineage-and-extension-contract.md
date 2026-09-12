# Lineage and extension contract

`jarvis-core` is intentionally provider-neutral. `AgentLineage` and `LineageProof` provide a stable parent/child delegation contract without introducing HTTP, GitHub, IDE, scheduler or model dependencies.

A parent creates a child lineage node with:

- `parent_task_id`
- `root_task_id`
- `depth`
- `role`

A child result can be bound to evidence digests through `LineageProof`. The proof digest makes changes to the lineage or evidence detectable.

Future orchestration systems can therefore add parallel subagents, reviewers, research agents or remote workers without changing Core when the model/provider changes.

## Boundary

Core owns contracts and verification primitives. Jarvis owns workstation UX/protocol adapters. AI Stack owns durable orchestration, provider routing, GitHub automation, scheduling and tenancy policy.
