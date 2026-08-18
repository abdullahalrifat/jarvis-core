from jarvis_core.agents import AgentResult, SelectiveOrchestrator, TaskProfile
from jarvis_core.tokens import TokenLedger


class Backend:
    model = "test-model"

    def __init__(self):
        self.roles = []

    def run(self, *, role, task, context, max_output_tokens):
        self.roles.append(role)
        return AgentResult(role=role, summary=task, verified=role == "verifier")


def test_code_flow_explores_implements_and_verifies():
    backend = Backend()
    results = SelectiveOrchestrator(backend, TokenLedger()).run(
        "fix the test", profile=TaskProfile.CODE
    )
    assert [result.role for result in results] == ["explorer", "implementer", "verifier"]


def test_simple_flow_uses_one_agent():
    backend = Backend()
    SelectiveOrchestrator(backend, TokenLedger()).run("explain this", profile=TaskProfile.SIMPLE)
    assert backend.roles == ["implementer"]
