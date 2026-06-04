"""
backend/api/websocket/routes.py
────────────────────────────────
WebSocket endpoints.

Endpoints:
  /ws/connect             — General purpose real-time channel (global + user channel)
  /ws/workflow/{id}       — Subscribe to a specific workflow's live updates
  /ws/admin               — Admin-only broadcast stream

Client → Server messages (JSON):
  { "action": "subscribe",   "channel": "workflow:abc123" }
  { "action": "unsubscribe", "channel": "workflow:abc123" }
  { "action": "ping" }
"""

import uuid
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from backend.api.websocket.manager import manager, make_event

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _handle_client_message(
    ws: WebSocket, client_id: str, raw: Any
) -> None:
    """Process a JSON message sent by the client."""
    if not isinstance(raw, dict):
        return

    action = raw.get("action")

    if action == "ping":
        await ws.send_json(make_event("pong", {}, sender="server"))

    elif action == "subscribe":
        channel = raw.get("channel", "")
        manager.subscribe(client_id, channel, ws)
        await ws.send_json(
            make_event("subscribed", {"channel": channel}, sender="server")
        )

    elif action == "unsubscribe":
        channel = raw.get("channel", "")
        manager.unsubscribe(client_id, channel)
        await ws.send_json(
            make_event("unsubscribed", {"channel": channel}, sender="server")
        )

    elif action == "broadcast":
        # Clients can emit to the global channel (useful for chat/demo)
        data = raw.get("data", {})
        await manager.broadcast("client_message", data, channel="global")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.websocket("/connect")
async def ws_connect(
    websocket: WebSocket,
    token: str = Query(default="", description="JWT bearer token (query param)"),
) -> None:
    """
    General-purpose WebSocket endpoint.
    Clients are automatically subscribed to:
      - ``global``        — platform-wide broadcasts
      - ``user:<token>``  — personalised channel (use real user ID in production)
    """
    client_id = str(uuid.uuid4())
    # In production: verify JWT `token` and derive real user_id
    user_channel = f"user:{token[:8] or client_id[:8]}"

    await manager.connect(websocket, client_id, channels=["global", user_channel])
    await websocket.send_json(
        make_event("connected", {"client_id": client_id, "channel": user_channel})
    )

    try:
        while True:
            raw = await websocket.receive_json()
            await _handle_client_message(websocket, client_id, raw)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        manager.disconnect(client_id)


@router.websocket("/workflow/{workflow_id}")
async def ws_workflow(workflow_id: str, websocket: WebSocket) -> None:
    """
    Subscribe to live status updates for a specific workflow run.
    Messages include status transitions: queued → running → completed / failed.
    """
    client_id = str(uuid.uuid4())
    channel = f"workflow:{workflow_id}"

    await manager.connect(websocket, client_id, channels=[channel])
    await websocket.send_json(
        make_event("subscribed", {"workflow_id": workflow_id, "channel": channel})
    )

    try:
        while True:
            raw = await websocket.receive_json()
            await _handle_client_message(websocket, client_id, raw)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        manager.disconnect(client_id)


@router.websocket("/admin")
async def ws_admin(websocket: WebSocket) -> None:
    """
    Admin-only real-time stream for system events, audit tails, agent logs.
    In production this endpoint must validate an admin JWT before accepting.
    """
    client_id = f"admin-{uuid.uuid4()}"
    await manager.connect(websocket, client_id, channels=["global", "admin"])
    await websocket.send_json(
        make_event("connected", {"client_id": client_id, "role": "admin"})
    )

    try:
        while True:
            raw = await websocket.receive_json()
            await _handle_client_message(websocket, client_id, raw)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        manager.disconnect(client_id)


@router.websocket("/stats")
async def ws_stats(websocket: WebSocket) -> None:
    """Push current connection stats to the caller and disconnect."""
    await websocket.accept()
    await websocket.send_json(make_event("stats", manager.stats()))
    await websocket.close()
