from typing import Dict, Any
from backend.llm.llm_router import LLMRouter
from backend.llm.prompt_engine import PromptEngine


class OrchestratorService:
    """
    Central orchestration layer connecting:
    - LangGraph workflows
    - LLM routing
    - RAG context injection
    """

    def __init__(self):
        self.llm_router = LLMRouter()
        self.prompt_engine = PromptEngine()

    def run_chat(self, query: str, context: str = "", provider: str = "openai") -> str:
        messages = self.prompt_engine.build_chat_prompt(query, context)
        return self.llm_router.route(messages, provider)

    def run_agent_state(self, state: Dict[str, Any], provider: str = "openai") -> str:
        messages = self.prompt_engine.build_agent_prompt(state)
        return self.llm_router.route(messages, provider)
