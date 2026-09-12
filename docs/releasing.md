# Jarvis Core release process

Jarvis Core uses Conventional Commits and Release Please. Maintainers do not edit the package version or changelog on `main` by hand.

## Version rules

- `fix:` / `perf:` -> patch release
- `feat:` -> minor release
- `BREAKING CHANGE:` or a `!` breaking-change commit -> major release
- Release Please updates `pyproject.toml`, `CHANGELOG.md`, the release manifest and the GitHub release PR.

For example, `0.9.5` becomes `0.9.6` for a fix, `0.10.0` for a feature, and `1.0.0` for a breaking change.

## Release lifecycle

```text
feature/fix PR
    -> CI
    -> merge to main
    -> Release Please opens/updates release PR
    -> maintainer reviews and merges release PR
    -> GitHub tag + release
    -> publish workflow checks out that exact tag
    -> full CI + build + clean-install verification
    -> PyPI Trusted Publishing
```

Publishing is therefore never performed from an unreviewed working branch, and the PyPI artifact is built from the exact released tag that passed validation.

## Consumer repositories

`jarvis` and `ai-stack` pin the released `jarvis-agent-core` package and use Dependabot to open update PRs when a new Core release is published. Those update PRs run the normal consumer CI and are reviewed independently; maintainers do not manually chase Core version numbers across repositories.

## PyPI setup

The repository uses PyPI Trusted Publishing through the `pypi` GitHub environment. Configure the PyPI trusted publisher for this repository/workflow before the first automated publication. No long-lived PyPI API token is required by the workflow.

## Emergency release

If a release PR is incorrect, close it and fix the underlying Conventional Commit history. Do not manually retag or overwrite an existing PyPI release. PyPI releases are immutable; a correction must use the next semantic version.
