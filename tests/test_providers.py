from jarvis_core import ModelProvider, ModelRequest, ModelResponse, ModelUsage, ToolCall


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
    response = provider.complete(ModelRequest(messages=({"role": "user", "content": "hi"},), max_output_tokens=128))
    assert response.content == "ok"
    assert response.usage.total_tokens == 5
    assert response.tool_calls[0].name == "noop"
