"""Deterministic context reduction and delta construction."""

from __future__ import annotations

import json
from typing import Any, Iterable

from .artifacts import ArtifactStore
from .tokens import estimate_tokens


def _window(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    head = limit * 2 // 3
    return text[:head] + "\n...[omitted]...\n" + text[-(limit - head) :]


def summarize_tool_result(
    tool_name: str,
    result: Any,
    *,
    max_chars: int = 6_000,
    artifact_store: ArtifactStore | None = None,
) -> dict[str, Any]:
    """Produce a compact schema while retaining full output as an artifact."""
    raw = (
        result
        if isinstance(result, str)
        else json.dumps(result, ensure_ascii=False, default=str)
    )
    artifact = None
    if len(raw) > max_chars and artifact_store is not None:
        artifact = artifact_store.put(
            raw, "application/json" if not isinstance(result, str) else "text/plain"
        )

    if tool_name in {"run_tests", "test", "pytest"} and isinstance(result, dict):
        summary = {
            key: result[key]
            for key in ("status", "passed", "failed", "skipped", "duration_ms")
            if key in result
        }
        if result.get("failures"):
            summary["failures"] = result["failures"][:5]
    elif tool_name in {"search", "search_text", "search_code"} and isinstance(
        result, dict
    ):
        matches = result.get("matches", [])
        summary = {
            "matches": matches[:12],
            "omitted_matches": max(0, len(matches) - 12),
        }
    elif tool_name in {"list_files", "tree"} and isinstance(result, list):
        summary = {"items": result[:20], "omitted_items": max(0, len(result) - 20)}
    elif tool_name in {"read_file", "inspect_files"} and isinstance(result, dict):
        summary = dict(result)
        if "content" in summary:
            summary["content"] = _window(str(summary["content"]), max_chars)
    else:
        summary = {"output": _window(raw, max_chars)}

    if artifact is not None:
        summary["artifact"] = {
            "uri": artifact.uri,
            "sha256": artifact.digest,
            "size": artifact.size,
            "preview": artifact.preview,
        }
    return summary


def compact_messages(
    messages: list[dict[str, Any]],
    *,
    keep_recent: int = 4,
    max_summary_chars: int = 8_000,
) -> tuple[list[dict[str, Any]], int]:
    """Fold older turns into structured state without another model call."""
    if len(messages) <= keep_recent + 2:
        return messages, 0
    original = estimate_tokens(messages)
    head = messages[:2]
    middle = messages[2:-keep_recent]
    recent = messages[-keep_recent:]
    state: dict[str, Any] = {
        "decisions": [],
        "files": [],
        "tools": [],
        "failures": [],
        "observations": [],
    }
    for message in middle:
        content = message.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, default=str)
        name = str(message.get("name", ""))
        if name:
            state["tools"].append(name)
        lowered = content.lower()
        bucket = (
            "failures"
            if any(word in lowered for word in ("error", "failed", "exception"))
            else "observations"
        )
        state[bucket].append(_window(content, 500))
        for token in content.replace('"', " ").replace("'", " ").split():
            if "/" in token and "." in token and len(token) < 180:
                state["files"].append(token.strip(".,:;()[]{}"))
    state["tools"] = list(dict.fromkeys(state["tools"]))[-20:]
    state["files"] = list(dict.fromkeys(state["files"]))[-40:]
    for key in ("observations", "failures"):
        state[key] = state[key][-12:]
    serialized = _window(json.dumps(state, ensure_ascii=False), max_summary_chars)
    compacted = (
        head
        + [
            {
                "role": "system",
                "content": "Structured state from earlier turns:\n" + serialized,
            }
        ]
        + recent
    )
    return compacted, max(0, original - estimate_tokens(compacted))


def delta_context(
    *,
    stable: dict[str, Any] | None = None,
    previous: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
    recent_messages: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Return only state changed since the prior turn plus recent messages."""
    stable = stable or {}
    previous = previous or {}
    current = current or {}
    changed = {
        key: value
        for key, value in current.items()
        if key not in previous or previous[key] != value
    }
    removed = sorted(set(previous) - set(current))
    return {
        "stable": stable,
        "changed": changed,
        "removed": removed,
        "recent": list(recent_messages),
    }
