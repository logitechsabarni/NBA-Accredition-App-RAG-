"""
backend/api/websocket/manager.py
─────────────────────────────────
WebSocket connection manager.
Supports per-user channels, room broadcasting, and typed event envelopes.
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


# ── Event envelope ────────────────────────────────────────────────────────────

def make_event(event_type: str, data: Any, *, sender: str = "system") -> dict:
    return {
        "event": event_type,
        "data": data,
        "sender": sender,
        "ts": datetime.utcnow().isoformat(),
    }


# ── Manager ───────────────────────────────────────────────────────────────────

class ConnectionManager:
    """
    Manages WebSocket lifecycles.

    Channels (rooms):
        - ``"global"``          — broadcast to every connected client
        - ``"workflow:<id>"``   — updates for a specific workflow run
        - ``"user:<username>"`` — private channel per user

    Thread-safety: all operations are async; no locking needed for
    asyncio single-thread event loop, but NOT safe across multiple
    worker processes without a pub/sub broker (use Redis Pub/Sub for
    production multi-worker deployments).
    """

    def __init__(self) -> None:
        # channel_id -> {client_id -> WebSocket}
        self._channels: dict[str, dict[str, WebSocket]] = defaultdict(dict)
        # client_id -> set of subscribed channel ids
        self._client_channels: dict[str, set[str]] = defaultdict(set)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        channels: list[str] | None = None,
    ) -> None:
        await websocket.accept()
        default_channels = channels or ["global"]
        for ch in default_channels:
            self._channels[ch][client_id] = websocket
            self._client_channels[client_id].add(ch)
        logger.info("WS connected: client=%s channels=%s", client_id, default_channels)

    def disconnect(self, client_id: str) -> None:
        for ch in list(self._client_channels.get(client_id, [])):
            self._channels[ch].pop(client_id, None)
        self._client_channels.pop(client_id, None)
        logger.info("WS disconnected: client=%s", client_id)

    def subscribe(self, client_id: str, channel: str, websocket: WebSocket) -> None:
        self._channels[channel][client_id] = websocket
        self._client_channels[client_id].add(channel)

    def unsubscribe(self, client_id: str, channel: str) -> None:
        self._channels[channel].pop(client_id, None)
        self._client_channels[client_id].discard(channel)

    # ── Sending ───────────────────────────────────────────────────────────────

    async def send_to(self, client_id: str, event_type: str, data: Any) -> bool:
        """Send an event to a specific client. Returns False if not connected."""
        for ch_sockets in self._channels.values():
            ws = ch_sockets.get(client_id)
            if ws:
                try:
                    await ws.send_json(make_event(event_type, data))
                    return True
                except Exception as exc:
                    logger.warning("send_to failed client=%s: %s", client_id, exc)
                    self.disconnect(client_id)
                    return False
        return False

    async def broadcast(
        self,
        event_type: str,
        data: Any,
        *,
        channel: str = "global",
        exclude: set[str] | None = None,
    ) -> None:
        """Broadcast an event to all clients on a channel."""
        exclude = exclude or set()
        envelope = make_event(event_type, data)
        dead: list[str] = []

        for client_id, ws in list(self._channels[channel].items()):
            if client_id in exclude:
                continue
            try:
                await ws.send_json(envelope)
            except Exception as exc:
                logger.warning("broadcast failed client=%s: %s", client_id, exc)
                dead.append(client_id)

        for cid in dead:
            self.disconnect(cid)

    async def broadcast_workflow_update(
        self,
        workflow_id: str,
        status: str,
        payload: dict | None = None,
    ) -> None:
        """Convenience helper for workflow status change events."""
        await self.broadcast(
            event_type="workflow_update",
            data={"workflow_id": workflow_id, "status": status, **(payload or {})},
            channel=f"workflow:{workflow_id}",
        )
        # Also push to global so dashboard can react
        await self.broadcast(
            event_type="workflow_update",
            data={"workflow_id": workflow_id, "status": status},
            channel="global",
        )

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "total_clients": len(self._client_channels),
            "channels": {ch: len(socks) for ch, socks in self._channels.items()},
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
manager = ConnectionManager()
