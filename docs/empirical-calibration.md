# Empirical route calibration

`jarvis-core` is the canonical home for the provider-neutral empirical calibration algorithm.

## Ownership

- **Core:** observation contract, recency weighting, minimum-sample safeguards, quality floor and route utility.
- **AI Stack:** provider execution, runtime telemetry, persistence and conversion of telemetry into Core observations.
- **Jarvis:** real workload corpus and task-level evaluation.

Production flow:

`Jarvis CLI -> AI Stack -> provider/model`

Both downstream applications reuse Core; Core never depends on AI Stack or Jarvis.

## Safety

Automatic routing changes only when enough recent observations exist and the measured quality clears the configured floor. Otherwise the consumer keeps its existing health/benchmark fallback. This prevents a single cheap or lucky request from moving production traffic.
