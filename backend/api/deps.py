"""
backend/api/deps.py
───────────────────
Dependency injection providers for FastAPI route handlers.

Usage:
    @router.get("/me")
    async def me(user: TokenPayload = Depends(get_current_user)):
        ...
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.security.jwt import SECRET_KEY, ALGORITHM, TokenPayload

_bearer = HTTPBearer(auto_error=True)


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> TokenPayload:
    """
    Validate the JWT bearer token present in the Authorization header and
    return the decoded payload as a ``TokenPayload`` instance.

    Raises:
        HTTPException 401  – token missing, malformed, or expired.
    """
    token = credentials.credentials
    try:
        raw = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**raw)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """Ensures the authenticated user holds the 'admin' role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


# ── Type aliases (convenience) ────────────────────────────────────────────────
CurrentUser  = Annotated[TokenPayload, Depends(get_current_user)]
AdminUser    = Annotated[TokenPayload, Depends(require_admin)]
