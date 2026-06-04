from backend.core.orchestrator.service import OrchestratorService


def test_orchestrator():
    orch = OrchestratorService()
    result = orch.run_chat("Hello NBA AI")
    assert isinstance(result, str)
