"""Deterministic recovery classification for model and tool failures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureKind(str, Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    TRANSPORT = "transport"
    MALFORMED_TOOL_CALL = "malformed_tool_call"
    UNKNOWN_PATH = "unknown_path"
    PATCH_CONFLICT = "patch_conflict"
    CONTEXT_OVERFLOW = "context_overflow"
    TOOL_REFUSAL = "tool_refusal"
    TEST_FAILURE = "test_failure"
    REPEATED_ACTION = "repeated_action"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RecoveryDecision:
    kind: FailureKind
    action: str
    retryable: bool
    switch_model: bool = False


_RULES = (
    (FailureKind.RATE_LIMIT, ("429", "rate limit", "too many requests"), "backoff"),
    (FailureKind.TIMEOUT, ("timeout", "timed out", "deadline"), "retry_smaller"),
    (FailureKind.CONTEXT_OVERFLOW, ("context length", "too many tokens"), "compact"),
    (
        FailureKind.MALFORMED_TOOL_CALL,
        ("invalid tool", "malformed tool", "arguments"),
        "repair_schema",
    ),
    (
        FailureKind.UNKNOWN_PATH,
        ("file not found", "unknown path", "no such file"),
        "refresh_repository_map",
    ),
    (
        FailureKind.PATCH_CONFLICT,
        ("old_string not found", "patch failed", "stale"),
        "reread_and_patch",
    ),
    (
        FailureKind.TOOL_REFUSAL,
        ("cannot call tools", "native tool calling failed"),
        "switch_model",
    ),
    (
        FailureKind.TEST_FAILURE,
        ("test failed", "tests failed", "assertionerror"),
        "repair_from_test_evidence",
    ),
    (
        FailureKind.REPEATED_ACTION,
        ("repeated action", "already executed", "duplicate tool"),
        "replan",
    ),
    (
        FailureKind.TRANSPORT,
        ("connection", "gateway", "unavailable", "502", "503", "504"),
        "retry",
    ),
)


def classify_failure(error: BaseException | str) -> RecoveryDecision:
    text = str(error).casefold()
    for kind, markers, action in _RULES:
        if any(marker in text for marker in markers):
            return RecoveryDecision(
                kind=kind,
                action=action,
                retryable=True,
                switch_model=kind is FailureKind.TOOL_REFUSAL,
            )
    return RecoveryDecision(FailureKind.UNKNOWN, "stop", False)
