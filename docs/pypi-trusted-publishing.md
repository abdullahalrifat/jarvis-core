# PyPI Trusted Publishing

`jarvis-agent-core` is published to PyPI by GitHub Actions using OpenID Connect (OIDC). No PyPI API token is stored in GitHub.

## One-time PyPI configuration

On PyPI, open the `jarvis-agent-core` project and configure a **Trusted Publisher** with:

- **Owner:** `abdullahalrifat`
- **Repository:** `jarvis-core`
- **Workflow:** `.github/workflows/release.yml`
- **Environment:** `pypi`

The GitHub Actions workflow also declares the same `pypi` environment. Keep the environment name identical on both sides.

If the project does not exist on PyPI yet, use PyPI's publishing flow to create the project and add the GitHub trusted publisher before merging the first release that should be published there. Do not add a long-lived PyPI API token to repository secrets.

## Release behavior

After a version bump is merged to `main`:

1. `Release` validates formatting, lint, typing, tests and coverage.
2. The exact commit is built into a wheel and source distribution.
3. The wheel is installed in a clean virtual environment and smoke-tested.
4. SHA-256 checksums and build-provenance attestations are generated.
5. The exact validated artifacts are attached to GitHub Release `vX.Y.Z`.
6. The same artifacts are published to PyPI through the `pypa/gh-action-pypi-publish` Trusted Publishing action.

An existing GitHub release is never replaced, and an existing package version on PyPI cannot be overwritten. Therefore a version must be incremented for every new publication.

## Consumer usage

Production consumers should use the package name and version range rather than a Git checkout:

```toml
dependencies = [
    "jarvis-agent-core>=0.9.4,<1.0",
]
```

For a fully reproducible application lockfile, resolve and lock an exact version and hashes using the consumer's normal dependency-management tooling.

## Local development

Use an editable checkout when changing Core and a consumer simultaneously:

```bash
python -m pip install -e ../jarvis-core
```

Do not publish temporary development changes to PyPI just to test a consumer integration.
