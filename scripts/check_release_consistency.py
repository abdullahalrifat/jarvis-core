"""Validate release metadata consistency for jarvis-core."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def main() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")

    version_match = re.search(
        r'^version\s*=\s*["\']([^"\']+)["\']', pyproject, re.MULTILINE
    )
    if not version_match:
        raise SystemExit("Could not find project version in pyproject.toml")
    version = version_match.group(1)

    if f"## {version}" not in changelog:
        raise SystemExit(f"CHANGELOG.md has no top-level entry for {version}")

    current_release = re.search(r"The current release is \*\*([^*]+)\*\*", readme)
    if not current_release or current_release.group(1) != version:
        raise SystemExit(
            "README.md current release does not match pyproject.toml: "
            f"expected {version}"
        )

    install_pin = f"jarvis-agent-core=={version}"
    if install_pin not in readme:
        raise SystemExit(f"README.md is missing the pinned install version {version}")

    print(f"release metadata consistent: {version}")


if __name__ == "__main__":
    main()
