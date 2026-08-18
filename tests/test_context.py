from jarvis_core.artifacts import MemoryArtifactStore
from jarvis_core.context import compact_messages, delta_context, summarize_tool_result


def test_large_result_becomes_artifact():
    store = MemoryArtifactStore()
    result = summarize_tool_result("command", "x" * 1000, max_chars=100, artifact_store=store)
    assert result["artifact"]["uri"].startswith("artifact://sha256/")
    assert len(result["output"]) < 140


def test_compaction_preserves_recent_messages():
    messages = [{"role": "user", "content": str(index) * 200} for index in range(10)]
    compacted, saved = compact_messages(messages, keep_recent=2)
    assert compacted[-2:] == messages[-2:]
    assert saved > 0


def test_delta_context_only_includes_changes():
    result = delta_context(previous={"a": 1, "b": 2}, current={"a": 1, "b": 3, "c": 4})
    assert result["changed"] == {"b": 3, "c": 4}
