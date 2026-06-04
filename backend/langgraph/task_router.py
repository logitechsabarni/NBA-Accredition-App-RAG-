"""
Task router node — determines which agent should handle each workflow step.
Cost-aware and intent-driven routing logic for the NBA AI platform.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from backend.langgraph.workflow_state import (
    AgentRole,
    AgentStep,
    MessageRole,
    WorkflowState,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

_ANALYST_KEYWORDS = frozenset(
    [
        "analyze",
        "analysis",
        "compare",
        "trend",
        "performance",
        "stats",
        "statistics",
        "metrics",
        "ranking",
        "rank",
        "top",
        "best",
        "worst",
        "average",
        "season",
        "game",
        "player",
        "team",
    ]
)

_RETRIEVAL_KEYWORDS = frozenset(
    [
        "find",
        "search",
        "lookup",
        "retrieve",
        "get",
        "fetch",
        "what is",
        "who is",
        "show me",
        "list",
        "give me",
    ]
)


def _extract_intent(text: str) -> str:
    lowered = text.lower()
    tokens = re.findall(r"\b\w+\b", lowered)
    token_set = set(tokens)

    analyst_hits = len(token_set & _ANALYST_KEYWORDS)
    retrieval_hits = len(token_set & _RETRIEVAL_KEYWORDS)

    if analyst_hits >= retrieval_hits:
        return AgentRole.ANALYST.value
    return AgentRole.RETRIEVER.value


def route_task(state: WorkflowState) -> WorkflowState:
    """
    Router node: analyses the latest user message and assigns next_agent.
    Records routing decision in execution trace.
    """
    step = AgentStep(
        agent_role=AgentRole.ROUTER,
        action="route_task",
    )

    try:
        user_messages = [m for m in state.messages if m.role == MessageRole.HUMAN]
        if not user_messages:
            raise ValueError("No human messages found in workflow state")

        latest_query = user_messages[-1].content
        intended_agent = _extract_intent(latest_query)

        state.current_agent = AgentRole.ROUTER
        state.next_agent = AgentRole(intended_agent)
        state.status = WorkflowStatus.RUNNING

        step.output_data = {
            "routed_to": intended_agent,
            "query_preview": latest_query[:120],
        }
        step.status = WorkflowStatus.COMPLETED

        state.record_trace(
            "routing_decision",
            {"routed_to": intended_agent, "query_length": len(latest_query)},
        )

        logger.info(
            "Router decision | workflow_id=%s routed_to=%s",
            state.context.workflow_id,
            intended_agent,
        )

    except Exception as exc:
        logger.exception("Router failed | workflow_id=%s", state.context.workflow_id)
        step.status = WorkflowStatus.FAILED
        step.error = str(exc)
        state.status = WorkflowStatus.FAILED
        state.error = str(exc)

    finally:
        state.add_step(step)

    return state
