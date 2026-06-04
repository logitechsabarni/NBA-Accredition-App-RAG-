"""
backend/api/routes/chat.py
──────────────────────────
Chat / Agent interaction routes.
Supports single-turn queries and multi-turn conversation history.
"""

import time
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import CurrentUser

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8192)
    model: str = Field(default="gpt-4o", description="LLM model identifier")
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID for multi-turn context",
    )
    history: list[Message] = Field(
        default_factory=list,
        description="Prior messages for multi-turn context (newest last)",
    )
    agent: Literal["copo", "attainment", "sar", "ci", "analytics", "validation", "auto"] = "auto"


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    agent_used: str
    model: str
    latency_ms: float
    tokens_used: int | None = None


class ConversationSummary(BaseModel):
    conversation_id: str
    message_count: int
    last_message: str


# ── In-memory conversation store (swap for Redis/DB in production) ─────────────
_conversations: dict[str, list[Message]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _route_agent(message: str, requested: str) -> str:
    """Simple keyword-based agent routing when agent='auto'."""
    if requested != "auto":
        return requested
    msg = message.lower()
    if any(k in msg for k in ["co", "po", "mapping", "correlation"]):
        return "copo"
    if any(k in msg for k in ["attainment", "score", "direct", "indirect"]):
        return "attainment"
    if any(k in msg for k in ["sar", "accreditation", "report", "narrative"]):
        return "sar"
    if any(k in msg for k in ["gap", "improvement", "corrective", "ci"]):
        return "ci"
    if any(k in msg for k in ["analytics", "kpi", "trend", "benchmark"]):
        return "analytics"
    if any(k in msg for k in ["validate", "compliance", "rule", "schema"]):
        return "validation"
    return "analytics"


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send a message to an NBA AI agent",
)
async def chat(body: ChatRequest, user: CurrentUser) -> ChatResponse:
    t0 = time.monotonic()

    conv_id = body.conversation_id or str(uuid.uuid4())
    history = _conversations.get(conv_id, [])

    # Append new user message
    new_msg = Message(role="user", content=body.message)
    history = history + body.history + [new_msg]

    agent = _route_agent(body.message, body.agent)

    # ── Stub: replace with real LLM/LangGraph call ─────────────────────────
    reply = (
        f"[{agent.upper()} agent] Acknowledged your query: "{body.message[:80]}…" "
        f"(model={body.model}, user={user.sub})"
    )
    # ── End stub ───────────────────────────────────────────────────────────

    assistant_msg = Message(role="assistant", content=reply)
    history.append(assistant_msg)
    _conversations[conv_id] = history[-40:]  # keep last 40 messages

    latency = (time.monotonic() - t0) * 1000

    return ChatResponse(
        conversation_id=conv_id,
        response=reply,
        agent_used=agent,
        model=body.model,
        latency_ms=round(latency, 2),
    )


@router.get(
    "/conversations",
    response_model=list[ConversationSummary],
    summary="List all active conversation sessions for current user",
)
async def list_conversations(user: CurrentUser) -> list[ConversationSummary]:
    summaries = []
    for cid, msgs in _conversations.items():
        last = msgs[-1].content[:120] if msgs else ""
        summaries.append(
            ConversationSummary(
                conversation_id=cid,
                message_count=len(msgs),
                last_message=last,
            )
        )
    return summaries


@router.get(
    "/conversations/{conversation_id}",
    response_model=list[Message],
    summary="Retrieve full message history for a conversation",
)
async def get_conversation(conversation_id: str, user: CurrentUser) -> list[Message]:
    history = _conversations.get(conversation_id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )
    return history


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation session",
)
async def delete_conversation(conversation_id: str, user: CurrentUser) -> None:
    _conversations.pop(conversation_id, None)
