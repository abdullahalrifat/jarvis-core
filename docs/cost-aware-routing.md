# Cost-aware hybrid routing

`jarvis-agent-core` 0.16.1 provides a provider-neutral routing policy for local-first agent execution.

## Policy

1. Deterministic operations should bypass the LLM.
2. Ordinary reasoning starts on the local tier.
3. Moderate/high difficulty or repeated local failures can escalate to the cheap tier.
4. Security-sensitive work and repeated multi-tier failures can escalate to the frontier tier.
5. A tier has a bounded failure budget; retries do not loop indefinitely.
6. The application maps tiers to concrete providers/models, keeping credentials, provider SDKs and pricing configuration outside Core.

## Routing signals

`RoutingSignals` combines normalized complexity, risk, uncertainty and retrieval confidence with execution evidence such as tool failures and attempts. `security_sensitive` forces frontier routing, while `deterministic_only` identifies work that should bypass model inference entirely.

## Failure budgets

The default policy allows two attempts on the local tier and two on the cheap tier before escalation. Frontier work is bounded to three attempts. Consumers can supply a different `FailureBudget` when their execution policy requires it.

```text
LOCAL --(budget exhausted)--> CHEAP --(budget exhausted)--> FRONTIER
```

## Cost-aware model selection

`RouteModel` represents an application-supplied model profile with input, cached-input and output prices. `select_model()` chooses the least expensive enabled model in the requested tier, with priority and name used as deterministic tie-breakers. Core does not own provider pricing data.

The model cost estimate is:

```text
uncached_input * input_price
+ cached_input * cached_input_price
+ output * output_price
```

where prices are supplied per million tokens.

## Consumer responsibilities

Core only decides the abstract tier and model-selection policy. The consuming application is responsible for mapping tiers to actual Ollama, Hugging Face, LiteLLM, Anthropic, OpenAI or other provider models, loading pricing metadata, executing requests and recording telemetry.

For a 16 GB CPU-only personal server, keep the local tier populated with the available Ollama aliases and leave cloud tiers empty unless remote providers are intentionally configured. This preserves local-first behavior while retaining a controlled escalation path.

## API

The routing API is available from `jarvis_core.cost_router`:

- `RouteTier` — local, cheap and frontier tiers.
- `RoutingSignals` — normalized routing evidence.
- `RoutingDecision` — selected tier, reason, attempt budget and verification requirement.
- `choose_tier()` — deterministic local/cheap/frontier decision.
- `FailureBudget` and `next_tier()` — bounded escalation.
- `RouteModel` and `select_model()` — cost-aware model selection inside a tier.
