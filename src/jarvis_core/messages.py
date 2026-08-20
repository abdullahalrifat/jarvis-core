"""Canonical transcripts and provider-specific message conversion."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def canonical_message(
    role: str,
    content: Any,
    *,
    tool_calls: list[dict[str, Any]] | None = None,
    tool_call_id: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable message without discarding structured blocks."""
    message: dict[str, Any] = {"role": role, "content": deepcopy(content)}
    if tool_calls:
        message["tool_calls"] = deepcopy(tool_calls)
    if tool_call_id:
        message["tool_call_id"] = tool_call_id
    return message


def to_openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert a canonical transcript to OpenAI chat-completions messages."""
    converted: list[dict[str, Any]] = []
    for item in messages:
        role = item.get("role")
        content = deepcopy(item.get("content", ""))
        if role == "assistant" and isinstance(content, list):
            text = "".join(
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
            calls = [
                {
                    "id": block["id"],
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": __import__("json").dumps(block.get("input") or {}),
                    },
                }
                for block in content
                if isinstance(block, dict) and block.get("type") == "tool_use"
            ]
            message = {"role": "assistant", "content": text or None}
            if calls:
                message["tool_calls"] = calls
            converted.append(message)
        elif role == "user" and isinstance(content, list) and any(
            isinstance(block, dict) and block.get("type") == "tool_result"
            for block in content
        ):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    converted.append(
                        {
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": block.get("content", ""),
                        }
                    )
        else:
            converted.append(deepcopy(item))
    return converted


def to_anthropic_messages(
    messages: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Convert a canonical transcript to Anthropic Messages API form."""
    import json

    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for item in messages:
        role = item.get("role")
        content = deepcopy(item.get("content", ""))
        if role == "system":
            system_parts.append(str(content))
        elif role == "assistant" and item.get("tool_calls"):
            blocks: list[dict[str, Any]] = []
            if content:
                blocks.append({"type": "text", "text": str(content)})
            for call in item["tool_calls"]:
                function = call.get("function") or call
                arguments = function.get("arguments") or {}
                if isinstance(arguments, str):
                    arguments = json.loads(arguments or "{}")
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": call.get("id"),
                        "name": function.get("name"),
                        "input": arguments,
                    }
                )
            converted.append({"role": "assistant", "content": blocks})
        elif role == "tool":
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": item["tool_call_id"],
                            "content": content,
                        }
                    ],
                }
            )
        else:
            converted.append({"role": role, "content": content})
    return "\n\n".join(system_parts), converted
