# AI Agent Repository Instructions

These instructions apply to all AI-assisted changes in `jarvis-core`.

## Core release rule

Every change that affects public behavior, public APIs, runtime semantics, packaging, or user-facing documentation MUST include the corresponding release metadata in the same pull request.

For a release-worthy change:

1. Determine the next semantic version before implementation.
2. Update `pyproject.toml` to that version.
3. Add a matching top-level entry to `CHANGELOG.md`.
4. Update `README.md` when public behavior, installation, API surface, architecture, or examples change. The README is also the PyPI long description.
5. Update relevant files under `docs/` when architecture, contracts, or operational/release behavior changes.
6. Add or update tests for behavior changes.
7. Verify that the package version, changelog version, README current-release version, and PR description agree.

Do not merge a release-worthy Core change with stale version or documentation metadata.

## Versioning

- Follow the repository's pre-1.0 semantic-versioning policy.
- Patch releases are for compatible fixes or documentation-only changes that do not alter the public contract.
- Minor releases are required for new public capabilities or public-contract changes while the package is pre-1.0.
- Published versions are immutable; consumers must use a released PyPI version.

## Architecture boundary

`jarvis-core` is provider-neutral and dependency-free at runtime. Keep reusable contracts, policies, algorithms, accounting, calibration, evaluation primitives, and execution semantics here. Do not add provider SDKs, credentials, persistence backends, CLI/UI behavior, deployment code, or product-specific orchestration.

For empirical routing/calibration:

- Core owns the observation contract and calibration algorithm.
- AI Stack owns model execution, telemetry collection, persistence, and adapters into Core observations.
- Jarvis owns real workload definitions and task-level evaluation.

The intended production flow is:

`Jarvis CLI -> AI Stack -> provider/model`

Both downstream applications consume Core; Core must never depend on either downstream application.

## Required validation

Before opening or updating a PR, run the repository validation commands in `CONTRIBUTING.md`, including formatting, linting, type checks, tests, build, and package metadata validation.
