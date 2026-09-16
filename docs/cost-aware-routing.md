# Cost-aware hybrid routing

`jarvis-core` now provides a provider-neutral routing policy for local-first agent execution.

## Policy

1. Deterministic operations should bypass the LLM.
2. Ordinary reasoning starts on the local tier.
3. Moderate/high difficulty or repeated local failures can escalate to the cheap tier.
4. Security-sensitive work and repeated multi-tier failures can escalate to the frontier tier.
5. A tier has a bounded failure budget; retries do not loop indefinitely.
6. The application maps tiers to concrete providers/models, keeping credentials and SDKs outside Core.

The core API is exposed by `jarvis_core.cost_router`:

- `RoutingSignals` — normalized routing evidence.
- `choose_tier()` — deterministic local/cheap/frontier decision.
- `FailureBudget` and `next_tier()` — bounded escalation.
- `RouteModel` and `select_model()` — cheapest eligible model selection inside a tier.

For the 16 GB CPU-only profile, configure `JARVIS_LOCAL_MODELS` with the Ollama aliases and leave cloud tiers empty unless remote providers are intentionally configured. This keeps normal personal use local while preserving a controlled path to stronger models.
