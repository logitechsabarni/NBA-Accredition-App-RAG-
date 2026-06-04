from typing import List, Dict


class FallbackHandler:
    """
    Handles fallback when primary LLM fails.
    """

    def __init__(self):
        self.fallback_message = (
            "I'm currently unable to fetch a full response. "
            "Please try again or refine your query."
        )

    def handle_failure(self, error: Exception) -> str:
        return f"{self.fallback_message}\nError: {str(error)}"

    def safe_chat(self, llm_call, messages: List[Dict[str, str]]) -> str:
        try:
            return llm_call(messages)
        except Exception as e:
            return self.handle_failure(e)
