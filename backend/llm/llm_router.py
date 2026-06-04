from typing import List, Dict, Optional
from .openai_client import OpenAIClient
from .granite_client import GraniteClient
from .fallback_handler import FallbackHandler


class LLMRouter:
    """
    Routes requests between OpenAI, Granite, or fallback models.
    """

    def __init__(self):
        self.openai = OpenAIClient()
        self.granite = GraniteClient()
        self.fallback = FallbackHandler()

        self.primary = "openai"

    def route(self, messages: List[Dict[str, str]], provider: Optional[str] = None) -> str:
        provider = provider or self.primary

        try:
            if provider == "openai":
                return self.openai.chat(messages)

            elif provider == "granite":
                return self.granite.chat(messages)

            else:
                raise ValueError(f"Unknown provider: {provider}")

        except Exception as e:
            return self.fallback.handle_failure(e)

    def stream_route(self, messages: List[Dict[str, str]], provider: str = "openai"):
        try:
            if provider == "openai":
                yield from self.openai.stream_chat(messages)
            else:
                # Granite streaming not implemented
                yield self.route(messages, provider)
        except Exception as e:
            yield self.fallback.handle_failure(e)
