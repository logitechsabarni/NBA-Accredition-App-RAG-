"""
Execution engine — runs compiled LangGraph graphs with tracing,
retry logic, and real-time event emission.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator

from langgraph.graph.graph import CompiledGraph

from backend.langgraph.memory_manager import MemoryManager
from backend.langgraph.workflow_state import (
    WorkflowContext,
    WorkflowState,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Manages the lifecycle of a LangGraph workflow execution:
    - Invokes the compiled graph
    - Persists intermediate checkpoints via MemoryManager
    - Emits structured events for WebSocket streaming
    - Handles retry on transient failures
    """

    def __init__(
        self,
        graph: CompiledGraph,
        memory_manager: MemoryManager,
    ) -> None:
        self._graph = graph
        self._memory = memory_manager

    async def execute(
        self,
        initial_state: WorkflowState,
        stream_events: bool = False,
    ) -> WorkflowState:
        workflow_id = initial_state.context.workflow_id
        logger.info(
            "Starting workflow execution | workflow_id=%s session_id=%s",
            workflow_id,
            initial_state.context.session_id,
        )

        initial_state.status = WorkflowStatus.RUNNING
        await self._memory.save_state(initial_state)

        attempt = 0
        last_exc: Exception | None = None

        while attempt <= initial_state.retry_policy.max_retries:
            try:
                start_ts = time.perf_counter()
                result_state = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._graph.invoke(initial_state.to_dict()),
                )
                elapsed_ms = (time.perf_counter() - start_ts) * 1000

                final_state = WorkflowState.model_validate(result_state)
                await self._memory.save_state(final_state)

                logger.info(
                    "Workflow execution complete | workflow_id=%s duration_ms=%.2f status=%s",
                    workflow_id,
                    elapsed_ms,
                    final_state.status,
                )
                return final_state

            except Exception as exc:
                last_exc = exc
                attempt += 1
                delay = min(
                    initial_state.retry_policy.initial_delay_ms
                    * (initial_state.retry_policy.backoff_factor ** attempt),
                    initial_state.retry_policy.max_delay_ms,
                )
                logger.warning(
                    "Workflow execution error — retrying | workflow_id=%s attempt=%d delay_ms=%.0f error=%s",
                    workflow_id,
                    attempt,
                    delay,
                    exc,
                )
                initial_state.retry_count = attempt
                await asyncio.sleep(delay / 1000)

        logger.error(
            "Workflow exhausted retries | workflow_id=%s error=%s",
            workflow_id,
            last_exc,
        )
        initial_state.status = WorkflowStatus.FAILED
        initial_state.error = str(last_exc)
        await self._memory.save_state(initial_state)
        return initial_state

    async def stream_execute(
        self,
        initial_state: WorkflowState,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Streams intermediate step events using LangGraph's streaming API.
        Yields dicts with event type and partial state info.
        """
        workflow_id = initial_state.context.workflow_id
        initial_state.status = WorkflowStatus.RUNNING
        await self._memory.save_state(initial_state)

        try:
            async for chunk in self._graph.astream(initial_state.to_dict()):
                for node_name, node_output in chunk.items():
                    event: dict[str, Any] = {
                        "event": "step_complete",
                        "workflow_id": workflow_id,
                        "node": node_name,
                        "status": node_output.get("status"),
                        "step_count": len(node_output.get("steps", [])),
                    }
                    logger.debug("Stream event | %s", event)
                    yield event

                    partial = WorkflowState.model_validate(node_output)
                    await self._memory.checkpoint(partial)

            yield {"event": "workflow_complete", "workflow_id": workflow_id}

        except Exception as exc:
            logger.exception(
                "Stream execution failed | workflow_id=%s", workflow_id
            )
            yield {
                "event": "workflow_failed",
                "workflow_id": workflow_id,
                "error": str(exc),
            }
