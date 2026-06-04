"""
Main orchestrator — entry point for all LangGraph workflow execution.
Wires together graph, memory, and execution engine.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, AsyncIterator

import redis.asyncio as aioredis

from backend.langgraph.execution_engine import ExecutionEngine
from backend.langgraph.graph_builder import build_standard_workflow
from backend.langgraph.memory_manager import MemoryManager
from backend.langgraph.task_router import route_task
from backend.langgraph.workflow_state import (
    Message,
    MessageRole,
    RetryPolicy,
    WorkflowContext,
    WorkflowState,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


def _placeholder_analyst(state: WorkflowState) -> WorkflowState:
    from backend.langgraph.workflow_state import AgentRole, AgentStep
    step = AgentStep(agent_role=AgentRole.ANALYST, action="analyze")
    step.output_data = {"analysis": "stub_analysis"}
    step.status = WorkflowStatus.COMPLETED
    state.add_step(step)
    state.variables["analysis_result"] = "stub"
    return state


def _placeholder_retriever(state: WorkflowState) -> WorkflowState:
    from backend.langgraph.workflow_state import AgentRole, AgentStep
    step = AgentStep(agent_role=AgentRole.RETRIEVER, action="retrieve_docs")
    step.output_data = {"docs": []}
    step.status = WorkflowStatus.COMPLETED
    state.add_step(step)
    return state


def _placeholder_summarizer(state: WorkflowState) -> WorkflowState:
    from backend.langgraph.workflow_state import AgentRole, AgentStep
    step = AgentStep(agent_role=AgentRole.SUMMARIZER, action="summarize")
    step.output_data = {"summary": "stub_summary"}
    step.status = WorkflowStatus.COMPLETED
    state.add_step(step)
    state.final_output = "stub_summary"
    return state


def _placeholder_validator(state: WorkflowState) -> WorkflowState:
    from backend.langgraph.workflow_state import AgentRole, AgentStep
    step = AgentStep(agent_role=AgentRole.VALIDATOR, action="validate")
    step.status = WorkflowStatus.COMPLETED
    state.add_step(step)
    state.status = WorkflowStatus.COMPLETED
    return state


class Orchestrator:
    """
    High-level facade for starting and managing NBA AI workflows.
    Instantiated once per application and shared via DI.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._memory = MemoryManager(redis_client)
        self._graph = build_standard_workflow(
            router_node=route_task,
            analyst_node=_placeholder_analyst,
            retriever_node=_placeholder_retriever,
            summarizer_node=_placeholder_summarizer,
            validator_node=_placeholder_validator,
        )
        self._engine = ExecutionEngine(self._graph, self._memory)
        logger.info("Orchestrator initialised with standard workflow graph")

    async def run(
        self,
        user_id: str,
        session_id: str,
        tenant_id: str,
        query: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowState:
        state = self._build_initial_state(
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
            query=query,
            metadata=metadata,
        )
        return await self._engine.execute(state)

    async def stream(
        self,
        user_id: str,
        session_id: str,
        tenant_id: str,
        query: str,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        state = self._build_initial_state(
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
            query=query,
            metadata=metadata,
        )
        async for event in self._engine.stream_execute(state):
            yield event

    async def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        return await self._memory.load_state(workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> bool:
        state = await self._memory.load_state(workflow_id)
        if state is None:
            return False
        state.status = WorkflowStatus.CANCELLED
        await self._memory.save_state(state)
        logger.info("Workflow cancelled | workflow_id=%s", workflow_id)
        return True

    def _build_initial_state(
        self,
        user_id: str,
        session_id: str,
        tenant_id: str,
        query: str,
        metadata: dict[str, Any] | None,
    ) -> WorkflowState:
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )
        state = WorkflowState(context=context)
        state.add_message(MessageRole.HUMAN, query)
        return state
