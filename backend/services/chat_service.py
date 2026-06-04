from typing import Optional
from backend.core.orchestrator.service import OrchestratorService


class ChatService:
    """
    Handles chat-level business logic.
    """

    def __init__(self):
        self.orchestrator = OrchestratorService()

    def get_response(self, query: str, context: Optional[str] = None, provider: str = "openai"):
        return self.orchestrator.run_chat(query, context or "", provider)
