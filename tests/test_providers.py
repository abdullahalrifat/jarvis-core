from jarvis_core import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    ToolCall,
    make_model_response,
    normalize_tool_call,
    normalize_usage,
)


def test_provider_contract_is_runtime_implementable() -> None:
    class FakeProvider:
        provider = "fake"
        model = "fake-model"
        last_usage = ModelUsage(input_tokens=2, output_tokens=3, total_tokens=5)

        def complete(self, request: ModelRequest) -> ModelResponse:
            assert request.messages[0]["role"] == "user"
            assert request.max_output_tokens == 128
            return ModelResponse(
                content="ok",
                tool_calls=(ToolCall("1", "noop", {}),),
                usage=self.last_usage,
                provider=self.provider,
                model=self.model,
            )

    provider: ModelProvider = FakeProvider()
    response = provider.complete(
        ModelRequest(
            messages=({"role": "user", "content": "hi"},), max_output_tokens=128
        )
    )
    assert response.content == "ok"
    assert response.usage.total_tokens == 5
    assert response.tool_calls[0].name == "noop"


def test_normalize_usage_supports_openai_style_fields() -> None:
    usage = normalize_usage({"prompt_tokens": 3, "completion_tokens": 5})
    assert usage == ModelUsage(input_tokens=3, output_tokens=5, total_tokens=8)


def test_normalize_tool_call_supports_openai_function_shape() -> None:
    call = normalize_tool_call(
        {"id": "call-1", "function": {"name": "search", "arguments": {"q": "x"}}}
    )
    assert call == ToolCall(id="call-1", name="search", arguments={"q": "x"})


def test_make_model_response_is_canonical() -> None:
    response = make_model_response(
        content="done",
        tool_calls=[ToolCall("1", "search", {"q": "x"})],
        usage={"input_tokens": 2, "output_tokens": 4},
        provider="example",
        model="example-model",
    )
    assert isinstance(response, ModelResponse)
    assert response.content == "done"
    assert response.usage.total_tokens == 6
