"""
Chat service — manages conversation history, streaming, and AI response orchestration.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger(__name__)


class ChatService:
    """Manages NBA AI chat sessions with conversation memory."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self._history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to history."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": time.strftime("%H:%M:%S"),
        }
        if metadata:
            msg.update(metadata)
        self._history.append(msg)

        # Trim to max_history
        if len(self._history) > self.max_history * 2:
            self._history = self._history[-self.max_history * 2:]

    def get_history(self, last_n: int = 6) -> List[Dict[str, str]]:
        """Return last N messages for prompt context."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self._history[-last_n:]
        ]

    def clear(self):
        """Clear conversation history."""
        self._history.clear()

    def generate_response(
        self,
        query: str,
        use_rag: bool = True,
        use_langgraph: bool = True,
        temperature: float = 0.7,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate a response using LangGraph pipeline or direct RAG fallback.

        Returns:
            Dict with response, sources, intent, latency.
        """
        start = time.time()

        if use_langgraph:
            try:
                from langgraph.graph_builder import run_pipeline
                result = run_pipeline(
                    user_query=query,
                    chat_history=self.get_history(),
                )
                self.add_message("user", query)
                self.add_message(
                    "assistant",
                    result["response"],
                    {"sources": result.get("sources", []), "intent": result.get("intent")},
                )
                result["latency_ms"] = round((time.time() - start) * 1000)
                return result
            except Exception as e:
                logger.warning(f"LangGraph pipeline failed, falling back to RAG: {e}")

        # Direct RAG fallback
        from utils.rag_engine import get_rag_engine
        rag = get_rag_engine(top_k=top_k, temperature=temperature)
        result = rag.generate(query, chat_history=self.get_history(), use_rag=use_rag)

        self.add_message("user", query)
        self.add_message(
            "assistant",
            result["response"],
            {"sources": result.get("sources", [])},
        )

        result["latency_ms"] = round((time.time() - start) * 1000)
        result["intent"] = "general_nba"
        return result

    def export_history(self) -> str:
        """Export chat history as formatted text."""
        lines = ["NBA AI Assistant — Chat Export", "=" * 50, ""]
        for msg in self._history:
            role = "You" if msg["role"] == "user" else "NBA AI"
            ts = msg.get("timestamp", "")
            lines.append(f"[{ts}] {role}:")
            lines.append(msg["content"])
            lines.append("")
        return "\n".join(lines)

    @property
    def message_count(self) -> int:
        return len(self._history)

    @property
    def history(self) -> List[Dict[str, Any]]:
        return self._history


_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
