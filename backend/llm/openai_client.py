import os
from typing import List, Dict, Any, Optional
from openai import OpenAI


class OpenAIClient:
    """
    Wrapper around OpenAI Chat Completions API.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: List[Dict[str, str]]):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
