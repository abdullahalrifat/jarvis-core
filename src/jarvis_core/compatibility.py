"""Cross-component compatibility helpers.

Applications use these pure functions at startup/CI to fail closed when a
shared Core contract is outside the supported compatibility window.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ComponentVersion:
    name: str
    version: str

@dataclass(frozen=True)
class CompatibilityReport:
    core_version: str
    components: tuple[ComponentVersion, ...]
    compatible: bool
    reason: str

def compatible_core_version(actual: str, expected: str) -> bool:
    return actual == expected

def report(core_version: str, expected_core: str, *components: ComponentVersion) -> CompatibilityReport:
    ok = compatible_core_version(core_version, expected_core)
    reason = "exact Core contract match" if ok else f"Core {core_version} != required {expected_core}"
    return CompatibilityReport(core_version, tuple(components), ok, reason)
