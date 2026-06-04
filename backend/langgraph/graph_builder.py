"""
Graph builder for LangGraph-based multi-agent workflows.
Constructs and compiles StateGraph instances for NBA AI platform.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph

from backend.langgraph.workflow_state import (
    AgentRole,
    WorkflowState,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Constructs LangGraph StateGraph workflows from registered agent nodes.
    Supports conditional routing, parallel branches, and error recovery edges.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Callable[[WorkflowState], WorkflowState]] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable, dict[str, str]]] = []
        self._entry_point: str | None = None

    def register_node(
        self,
        name: str,
        handler: Callable[[WorkflowState], WorkflowState],
    ) -> "GraphBuilder":
        if name in self._nodes:
            raise ValueError(f"Node '{name}' already registered")
        self._nodes[name] = handler
        logger.debug("Registered graph node: %s", name)
        return self

    def set_entry_point(self, name: str) -> "GraphBuilder":
        if name not in self._nodes:
            raise ValueError(f"Entry point node '{name}' is not registered")
        self._entry_point = name
        return self

    def add_edge(self, from_node: str, to_node: str) -> "GraphBuilder":
        self._edges.append((from_node, to_node))
        return self

    def add_conditional_edge(
        self,
        from_node: str,
        condition_fn: Callable[[WorkflowState], str],
        routing_map: dict[str, str],
    ) -> "GraphBuilder":
        self._conditional_edges.append((from_node, condition_fn, routing_map))
        return self

    def build(self) -> CompiledGraph:
        if not self._entry_point:
            raise RuntimeError("Entry point not set — call set_entry_point() first")

        graph = StateGraph(WorkflowState)

        for name, handler in self._nodes.items():
            graph.add_node(name, handler)
            logger.debug("Added node to graph: %s", name)

        graph.set_entry_point(self._entry_point)

        for from_node, to_node in self._edges:
            resolved_to = END if to_node == "__end__" else to_node
            graph.add_edge(from_node, resolved_to)
            logger.debug("Added edge: %s -> %s", from_node, to_node)

        for from_node, condition_fn, routing_map in self._conditional_edges:
            resolved_map = {
                k: (END if v == "__end__" else v)
                for k, v in routing_map.items()
            }
            graph.add_conditional_edges(from_node, condition_fn, resolved_map)
            logger.debug("Added conditional edges from: %s", from_node)

        compiled = graph.compile()
        logger.info("LangGraph compiled successfully with %d nodes", len(self._nodes))
        return compiled


def build_standard_workflow(
    router_node: Callable,
    analyst_node: Callable,
    retriever_node: Callable,
    summarizer_node: Callable,
    validator_node: Callable,
) -> CompiledGraph:
    """
    Assembles the standard NBA AI multi-agent workflow graph.
    Flow: router -> analyst -> retriever -> summarizer -> validator -> END
    With conditional retry on failure.
    """

    def route_after_router(state: WorkflowState) -> str:
        if state.status == WorkflowStatus.FAILED:
            return "failed"
        return state.next_agent.value if state.next_agent else "analyst"

    def route_after_validator(state: WorkflowState) -> str:
        if state.status == WorkflowStatus.FAILED and state.can_retry():
            return "router"
        if state.status == WorkflowStatus.FAILED:
            return "failed"
        return "completed"

    def noop_failed(state: WorkflowState) -> WorkflowState:
        logger.error(
            "Workflow entered failed terminal node | workflow_id=%s",
            state.context.workflow_id,
        )
        state.status = WorkflowStatus.FAILED
        return state

    def noop_completed(state: WorkflowState) -> WorkflowState:
        state.status = WorkflowStatus.COMPLETED
        logger.info(
            "Workflow completed successfully | workflow_id=%s",
            state.context.workflow_id,
        )
        return state

    builder = GraphBuilder()

    builder.register_node(AgentRole.ROUTER.value, router_node)
    builder.register_node(AgentRole.ANALYST.value, analyst_node)
    builder.register_node(AgentRole.RETRIEVER.value, retriever_node)
    builder.register_node(AgentRole.SUMMARIZER.value, summarizer_node)
    builder.register_node(AgentRole.VALIDATOR.value, validator_node)
    builder.register_node("failed", noop_failed)
    builder.register_node("completed", noop_completed)

    builder.set_entry_point(AgentRole.ROUTER.value)

    builder.add_conditional_edge(
        AgentRole.ROUTER.value,
        route_after_router,
        {
            AgentRole.ANALYST.value: AgentRole.ANALYST.value,
            AgentRole.RETRIEVER.value: AgentRole.RETRIEVER.value,
            "failed": "failed",
        },
    )

    builder.add_edge(AgentRole.ANALYST.value, AgentRole.RETRIEVER.value)
    builder.add_edge(AgentRole.RETRIEVER.value, AgentRole.SUMMARIZER.value)
    builder.add_edge(AgentRole.SUMMARIZER.value, AgentRole.VALIDATOR.value)

    builder.add_conditional_edge(
        AgentRole.VALIDATOR.value,
        route_after_validator,
        {
            AgentRole.ROUTER.value: AgentRole.ROUTER.value,
            "failed": "failed",
            "completed": "completed",
        },
    )

    builder.add_edge("failed", "__end__")
    builder.add_edge("completed", "__end__")

    return builder.build()
