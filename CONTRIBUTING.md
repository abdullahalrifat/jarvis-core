# Contributing to Jarvis Core

Thank you for helping improve Jarvis Core. Contributions of bug reports,
documentation, tests, and code are welcome.

## Before opening a change

1. Search existing issues and pull requests.
2. Open an issue for large API or behavioral changes.
3. Keep Core provider-neutral and dependency-free at runtime.
4. Do not move product-specific tools, storage, credentials, or policy into Core.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -r requirements-dev.txt build twine
python -m pytest
```

Before submitting a pull request, run:

```bash
black --check src tests
ruff check src tests --select E9,F63,F7,F82
pytest -q --cov=jarvis_core --cov-report=term-missing --cov-fail-under=85
python -m build
python -m twine check dist/*
```

## Pull requests

- Make one focused change per pull request.
- Add or update tests for behavior changes.
- Update README, changelog, typing, and compatibility notes when applicable.
- Explain user-visible behavior, risks, and validation in the description.
- Preserve backward compatibility within a minor release when practical.

By participating, you agree to follow the Code of Conduct. Please report
security vulnerabilities through the private process in SECURITY.md.
