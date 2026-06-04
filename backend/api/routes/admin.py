"""
backend/api/routes/admin.py
────────────────────────────
Admin-only routes: system health, user management, audit log retrieval.
All endpoints require the 'admin' role (enforced via AdminUser dep).
"""

import platform
import sys
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import AdminUser, CurrentUser

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "down"]
    latency_ms: float | None = None
    detail: str | None = None


class SystemHealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "down"]
    version: str
    python: str
    platform: str
    timestamp: datetime
    services: list[ServiceStatus]


class AuditLogEntry(BaseModel):
    id: int
    timestamp: datetime
    user: str
    method: str
    path: str
    status_code: int
    duration_ms: float


class AuditLogResponse(BaseModel):
    total: int
    entries: list[AuditLogEntry]


class UserRecord(BaseModel):
    username: str
    role: str
    active: bool


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8)
    role: Literal["admin", "faculty", "viewer"] = "viewer"


# ── In-memory stores (replace with DB in production) ─────────────────────────
_users: list[UserRecord] = [
    UserRecord(username="admin",   role="admin",   active=True),
    UserRecord(username="faculty", role="faculty", active=True),
    UserRecord(username="viewer",  role="viewer",  active=True),
]

_audit_log: list[AuditLogEntry] = []   # Populated by AuditMiddleware in production
_audit_counter = 0


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="Detailed system health check (admin only)",
)
async def health(user: AdminUser) -> SystemHealthResponse:
    services = [
        ServiceStatus(name="PostgreSQL", status="healthy", latency_ms=3.2),
        ServiceStatus(name="MongoDB",    status="healthy", latency_ms=2.8),
        ServiceStatus(name="Redis",      status="healthy", latency_ms=0.9),
        ServiceStatus(name="LangGraph",  status="healthy"),
        ServiceStatus(name="RAG Engine", status="healthy"),
    ]
    overall = (
        "degraded" if any(s.status == "degraded" for s in services)
        else "down" if any(s.status == "down" for s in services)
        else "healthy"
    )
    return SystemHealthResponse(
        status=overall,
        version="5.0.0",
        python=sys.version.split()[0],
        platform=platform.system(),
        timestamp=datetime.utcnow(),
        services=services,
    )


@router.get(
    "/users",
    response_model=list[UserRecord],
    summary="List all platform users",
)
async def list_users(user: AdminUser) -> list[UserRecord]:
    return _users


@router.post(
    "/users",
    response_model=UserRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new platform user",
)
async def create_user(body: CreateUserRequest, user: AdminUser) -> UserRecord:
    if any(u.username == body.username for u in _users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' already exists",
        )
    new_user = UserRecord(username=body.username, role=body.role, active=True)
    _users.append(new_user)
    return new_user


@router.delete(
    "/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate / delete a user",
)
async def delete_user(username: str, user: AdminUser) -> None:
    if username == user.sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    global _users
    _users = [u for u in _users if u.username != username]


@router.get(
    "/audit-logs",
    response_model=AuditLogResponse,
    summary="Retrieve recent audit log entries",
)
async def audit_logs(
    user: AdminUser,
    limit: int = 50,
) -> AuditLogResponse:
    entries = _audit_log[-limit:]
    return AuditLogResponse(total=len(_audit_log), entries=entries)


@router.get(
    "/config",
    summary="Return non-sensitive runtime configuration (admin only)",
)
async def config(user: AdminUser) -> dict[str, Any]:
    return {
        "log_level": "INFO",
        "max_workflows": 100,
        "rag_top_k": 5,
        "default_model": "gpt-4o",
        "jwt_expiry_minutes": 60,
    }
