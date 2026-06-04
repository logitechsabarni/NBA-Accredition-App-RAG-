from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseNode(ABC):
    """
    Base class for all LangGraph nodes in the NBA Enterprise AI Platform.
    
    Each node represents a unit of computation in the workflow graph:
    - LLM call node
    - RAG retrieval node
    - routing node
    - memory node
    - post-processing node
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute node logic and return updated state.
        Must be implemented by all child nodes.
        """
        pass

    def before(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook: runs before execution (optional override)
        """
        return state

    def after(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook: runs after execution (optional override)
        """
        return state

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standard execution pipeline for all nodes.
        """
        state = self.before(state)
        state = self.execute(state)
        state = self.after(state)
        return state

    def __repr__(self):
        return f"<Node:{self.name}>"
