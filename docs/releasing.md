# Jarvis Core release process

Jarvis Core uses semantic versioning and an explicit, reviewable release flow. The package version and release documentation are changed together in a pull request; release publication is performed by the repository's `release.yml` workflow.

## Version rules

- `fix:` / `perf:` or documentation-only release corrections -> patch release
- `feat:` -> minor release
- `BREAKING CHANGE:` or a `!` breaking-change commit -> major release
- patch releases must remain compatible within the current minor line;
- breaking Core contracts require coordinated Core/Jarvis/Server releases.

For example, `0.10.0` becomes `0.10.1` for a compatible fix or documentation correction, `0.11.0` for a new feature, and `1.0.0` for a breaking change.

## Release lifecycle

```text
version/documentation PR
    -> CI
    -> merge to main
    -> exact merged SHA is validated and built
    -> GitHub Release vX.Y.Z
    -> PyPI Trusted Publishing
    -> consumer repositories update their Core pin
```

The release workflow validates formatting, lint, typing, tests, coverage and package metadata before building the distributions. It verifies the wheel in a clean environment, generates SHA-256 checksums, creates provenance attestations and publishes the exact validated distributions.

The workflow can also be started manually with `workflow_dispatch` for an existing immutable tag. Manual publication is intended for retrying a release that was not successfully published; it does not overwrite an existing PyPI version. Corrections to code or documentation require a new semantic version.

## Consumer repositories

`jarvis` and `ai-stack` pin the released `jarvis-agent-core` package. After Core `0.10.1` is published, update those pins to `0.10.1` and run their normal CI before merging the consumer update PRs. Dependabot remains enabled for future Core updates.

## PyPI setup

The repository uses PyPI Trusted Publishing through the `pypi` GitHub environment. The PyPI trusted publisher must identify this repository's `.github/workflows/release.yml` workflow and the `pypi` environment. No long-lived PyPI API token is required by the workflow.

## Documentation and changelog

Every release PR must leave the public documentation internally consistent with the release being published. At minimum, update:

- `pyproject.toml` package version;
- `README.md` installation and release-flow references;
- `docs/releasing.md` release instructions;
- `CHANGELOG.md` with the release notes;
- `.release-please-manifest.json` if it remains in the repository.

## Emergency release

If a release PR is incorrect, fix it with a new PR before publishing. Do not manually retag or overwrite an existing PyPI release. PyPI releases are immutable; a correction must use the next semantic version.
