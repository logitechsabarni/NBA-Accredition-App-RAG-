import os
from typing import List, Dict, Optional


class GraniteClient:
    """
    Mock/adapter for IBM Granite models or any external enterprise LLM.
    Replace endpoint with actual IBM watsonx or Granite API.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: str = None):
        self.api_key = api_key or os.getenv("GRANITE_API_KEY")
        self.endpoint = endpoint or os.getenv("GRANITE_ENDPOINT", "")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Placeholder implementation.
        Replace with real HTTP call to Granite API.
        """
        user_msg = messages[-1]["content"] if messages else ""
        return f"[Granite Mock Response]: Processed query -> {user_msg}"
