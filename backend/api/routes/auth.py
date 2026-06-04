"""
backend/api/routes/auth.py
──────────────────────────
Authentication routes: login, token refresh, logout, me.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.api.deps import CurrentUser
from backend.core.security.jwt import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    username: str
    role: str
    issued_at: datetime | None = None


# ── Fake user store (replace with DB call in production) ──────────────────────
_USERS: dict[str, dict] = {
    "admin": {"password": "admin123", "role": "admin"},
    "faculty": {"password": "faculty123", "role": "faculty"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain JWT access + refresh tokens",
)
async def login(body: LoginRequest) -> TokenResponse:
    user = _USERS.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    payload = {"sub": body.username, "role": user["role"]}
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new token pair",
)
async def refresh(body: RefreshRequest) -> TokenResponse:
    data = decode_token(body.refresh_token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    payload = {"sub": data.get("sub"), "role": data.get("role", "viewer")}
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Return the profile of the currently authenticated user",
)
async def me(user: CurrentUser) -> UserProfile:
    return UserProfile(username=user.sub, role=user.role)


@router.post(
    "/logout",
    summary="Invalidate session (client-side token discard)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(user: CurrentUser) -> None:
    """
    Stateless JWT implementation: instruct the client to discard its tokens.
    For production, add a token blocklist (Redis SET with TTL).
    """
    return None
