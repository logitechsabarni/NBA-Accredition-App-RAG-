"""
Memory manager — persists and retrieves WorkflowState across sessions.
Uses Redis for short-term memory and PostgreSQL for long-term storage.
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import redis.asyncio as aioredis

from backend.langgraph.workflow_state import WorkflowState

logger = logging.getLogger(__name__)

_DEFAULT_TTL = timedelta(hours=24)
_KEY_PREFIX = "nba:workflow:"


class MemoryManager:
    """
    Provides short-term (Redis) memory for in-flight workflows
    and exposes hooks for long-term persistence integration.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    def _make_key(self, workflow_id: str) -> str:
        return f"{_KEY_PREFIX}{workflow_id}"

    async def save_state(
        self,
        state: WorkflowState,
        ttl: timedelta = _DEFAULT_TTL,
    ) -> None:
        key = self._make_key(state.context.workflow_id)
        payload = state.model_dump_json()
        await self._redis.setex(key, int(ttl.total_seconds()), payload)
        logger.debug(
            "Saved workflow state | workflow_id=%s ttl_seconds=%d",
            state.context.workflow_id,
            ttl.total_seconds(),
        )

    async def load_state(self, workflow_id: str) -> WorkflowState | None:
        key = self._make_key(workflow_id)
        raw = await self._redis.get(key)
        if raw is None:
            logger.debug("No cached state found | workflow_id=%s", workflow_id)
            return None
        state = WorkflowState.model_validate_json(raw)
        logger.debug("Loaded workflow state | workflow_id=%s", workflow_id)
        return state

    async def delete_state(self, workflow_id: str) -> None:
        key = self._make_key(workflow_id)
        await self._redis.delete(key)
        logger.debug("Deleted workflow state | workflow_id=%s", workflow_id)

    async def extend_ttl(
        self,
        workflow_id: str,
        ttl: timedelta = _DEFAULT_TTL,
    ) -> None:
        key = self._make_key(workflow_id)
        await self._redis.expire(key, int(ttl.total_seconds()))

    async def list_active_workflows(self, tenant_id: str) -> list[str]:
        pattern = f"{_KEY_PREFIX}*"
        keys: list[bytes] = await self._redis.keys(pattern)
        workflow_ids: list[str] = []
        for key in keys:
            raw = await self._redis.get(key)
            if raw:
                try:
                    data = json.loads(raw)
                    if data.get("context", {}).get("tenant_id") == tenant_id:
                        workflow_ids.append(
                            data["context"]["workflow_id"]
                        )
                except (json.JSONDecodeError, KeyError):
                    continue
        return workflow_ids

    async def checkpoint(self, state: WorkflowState) -> None:
        """Lightweight checkpoint — updates TTL and re-saves current state."""
        await self.save_state(state)
        logger.debug(
            "Checkpoint saved | workflow_id=%s step_count=%d",
            state.context.workflow_id,
            len(state.steps),
        )
