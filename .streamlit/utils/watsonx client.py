import os
import time
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class WatsonxClient:
    """IBM Watsonx.ai client for Granite model inference."""

    def __init__(self):
        self.api_key: Optional[str] = os.getenv("WATSONX_API_KEY")
        self.project_id: Optional[str] = os.getenv("WATSONX_PROJECT_ID")
        self.url: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.model_id: str = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2")
        self.client = None
        self.model = None
        self._connected = False
        self._last_response_time: float = 0.0

    def connect(self) -> bool:
        """Initialize IBM Watsonx connection."""
        if not self.api_key or not self.project_id:
            logger.warning("Watsonx credentials not configured.")
            self._connected = False
            return False
        try:
            from ibm_watsonx_ai import APIClient, Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            credentials = Credentials(url=self.url, api_key=self.api_key)
            self.client = APIClient(credentials)
            self.model = ModelInference(
                model_id=self.model_id,
                api_client=self.client,
                project_id=self.project_id,
                params={
                    "decoding_method": "greedy",
                    "max_new_tokens": 1024,
                    "min_new_tokens": 1,
                    "temperature": 0.7,
                    "top_k": 50,
                    "top_p": 1,
                    "repetition_penalty": 1.1,
                },
            )
            self._connected = True
            logger.info("IBM Watsonx connected successfully.")
            return True
        except ImportError:
            logger.error("ibm-watsonx-ai package not installed.")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Watsonx connection error: {e}")
            self._connected = False
            return False

    def test_connection(self) -> Dict[str, Any]:
        """Test the Watsonx connection and return diagnostics."""
        start = time.time()
        if not self._connected:
            connected = self.connect()
        else:
            connected = True

        elapsed = round((time.time() - start) * 1000, 1)

        if connected and self.model:
            try:
                _ = self.generate_response("Hello, respond with OK", max_tokens=10)
                connected = True
            except Exception as e:
                connected = False
                logger.error(f"Test generation failed: {e}")

        return {
            "connected": connected,
            "project_id": self.project_id or "Not Set",
            "model_id": self.model_id,
            "provider": "IBM Watsonx.ai",
            "url": self.url,
            "response_time_ms": elapsed,
        }

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_k: int = 50,
        system_prompt: str = "",
    ) -> str:
        """Generate a response from the Granite model."""
        if not self._connected:
            if not self.connect():
                raise ConnectionError("Watsonx not connected. Check credentials in Settings.")

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        start = time.time()
        try:
            from ibm_watsonx_ai.foundation_models import ModelInference

            params = {
                "decoding_method": "greedy",
                "max_new_tokens": max_tokens,
                "min_new_tokens": 1,
                "temperature": temperature,
                "top_k": top_k,
                "repetition_penalty": 1.1,
            }
            response = self.model.generate_text(prompt=full_prompt, params=params)
            self._last_response_time = round((time.time() - start) * 1000, 1)
            return response.strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise RuntimeError(f"Watsonx generation failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "model_id": self.model_id,
            "provider": "IBM Watsonx.ai",
            "project_id": self.project_id or "Not Configured",
            "url": self.url,
            "connected": self._connected,
            "last_response_time_ms": self._last_response_time,
        }

    @property
    def is_connected(self) -> bool:
        return self._connected


# Singleton instance
_watsonx_client: Optional[WatsonxClient] = None


def get_watsonx_client() -> WatsonxClient:
    global _watsonx_client
    if _watsonx_client is None:
        _watsonx_client = WatsonxClient()
    return _watsonx_client
