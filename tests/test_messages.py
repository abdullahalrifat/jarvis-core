from jarvis_core import (
    canonical_message,
    to_anthropic_messages,
    to_openai_messages,
)


def test_provider_message_round_trip_preserves_tool_exchange():
    transcript = [
        canonical_message("system", "safe"),
        canonical_message("user", "inspect"),
        canonical_message(
            "assistant",
            "",
            tool_calls=[
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path":"a.py"}'},
                }
            ],
        ),
        canonical_message("tool", "contents", tool_call_id="call-1"),
    ]
    system, anthropic = to_anthropic_messages(transcript)
    assert system == "safe"
    assert anthropic[1]["content"][0]["type"] == "tool_use"
    assert anthropic[2]["content"][0]["tool_use_id"] == "call-1"

    restored = to_openai_messages([{"role": "system", "content": system}, *anthropic])
    assert restored[2]["tool_calls"][0]["function"]["name"] == "read_file"
    assert restored[3] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": "contents",
    }
