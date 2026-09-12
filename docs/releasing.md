# Jarvis Core release process

Jarvis Core uses semantic versioning and an explicit, reviewable release flow. The package version and release documentation are changed together in a pull request; release publication is performed by the repository's release workflow.

## Version rules

- `fix:` / `perf:` or compatible documentation-only release corrections -> patch release;
- `feat:` -> minor release;
- `BREAKING CHANGE:` or a `!` breaking-change commit -> major release;
- patch releases must remain compatible within the current minor line;
- new public contracts and reusable runtime capabilities use a new minor version while the API remains pre-1.0.

For example, `0.12.0` becomes `0.12.1` for a compatible fix and `0.13.0` for a new feature.

## Release lifecycle

```text
version/documentation PR
    -> CI
    -> merge to main
    -> exact merged SHA is validated and built
    -> GitHub Release vX.Y.Z
    -> PyPI Trusted Publishing
    -> downstream applications may update independently
```

The release workflow validates formatting, lint, typing, tests, coverage and package metadata before building distributions. It verifies the wheel in a clean environment, generates SHA-256 checksums, creates provenance attestations and publishes the exact validated distributions.

The workflow can also be started manually for an existing immutable tag when a publication retry is required. Corrections to code or documentation require a new semantic version.

## PyPI setup

The repository uses PyPI Trusted Publishing through the `pypi` GitHub environment. No long-lived PyPI API token is required by the workflow.

## Documentation and changelog

Every release PR must leave the public documentation internally consistent with the release being published. At minimum, update:

- `pyproject.toml` package version;
- `README.md` installation and release-flow references;
- `docs/releasing.md` release instructions;
- `CHANGELOG.md` with release notes;
- `.release-please-manifest.json` when required by the release automation.

The README is also the PyPI project description. Documentation intended to appear on PyPI therefore requires a new package version.

## Emergency release

If a release is incorrect, fix it with a new PR before publishing. Do not manually retag or overwrite an existing PyPI release. PyPI releases are immutable; corrections use the next semantic version.
