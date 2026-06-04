import time
import uuid
from typing import Dict, Any, List


class TraceEvent:
    """
    Represents a single execution event inside the LangGraph pipeline.
    """

    def __init__(self, node: str, input_state: Dict[str, Any], output_state: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.node = node
        self.input_state = input_state
        self.output_state = output_state
        self.timestamp = time.time()


class ExecutionTracer:
    """
    Traces execution flow of LangGraph nodes for debugging,
    observability, and enterprise monitoring.
    """

    def __init__(self):
        self.events: List[TraceEvent] = []

    def log(self, node_name: str, input_state: Dict[str, Any], output_state: Dict[str, Any]):
        event = TraceEvent(node_name, input_state, output_state)
        self.events.append(event)

    def get_trace(self) -> List[Dict[str, Any]]:
        """
        Returns serialized trace for API/UI consumption.
        """
        return [
            {
                "id": e.id,
                "node": e.node,
                "timestamp": e.timestamp,
                "input": e.input_state,
                "output": e.output_state,
            }
            for e in self.events
        ]

    def clear(self):
        self.events = []

    def summary(self) -> Dict[str, Any]:
        """
        Lightweight execution summary.
        """
        return {
            "total_nodes": len(self.events),
            "start_time": self.events[0].timestamp if self.events else None,
            "end_time": self.events[-1].timestamp if self.events else None,
        }
