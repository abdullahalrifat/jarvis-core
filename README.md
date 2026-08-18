# Jarvis Core

Shared, dependency-free runtime contracts for Jarvis and AI Stack Server.

It provides atomic token budgeting, structured evidence and verification,
protocol-safe context compaction, content-addressed artifact retrieval,
versioned role prompts, and selective multi-agent orchestration.

## Install

```bash
pip install jarvis-agent-core
```

## Release

Releases use PyPI Trusted Publishing and require no stored API token.

1. Configure the PyPI project or pending publisher for repository
   `abdullahalrifat/jarvis-core`, workflow `release.yml`, environment `pypi`.
2. Update `project.version` in `pyproject.toml` and merge it to `main`.
3. Push an annotated tag with the same version, prefixed by `v`.

```bash
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0
```

The release workflow verifies the version, builds and checks the wheel and source
distribution, publishes them to PyPI, and creates the corresponding GitHub
Release only after publication succeeds. PyPI versions and Git tags are
immutable; increment the version instead of reusing a failed or published tag.
