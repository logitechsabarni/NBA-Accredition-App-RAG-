"""
NBA Enterprise AI Platform — Security Utilities
JWT token creation/validation, password hashing, and
helper functions for authentication middleware.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


# ----------------------------------------------------------------
# Password utilities
# ----------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ----------------------------------------------------------------
# JWT utilities
# ----------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    expire = _utcnow() + timedelta(
        minutes=settings.jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": _utcnow(),
        "exp": expire,
        "jti": str(uuid4()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.jwt.JWT_SECRET_KEY,
        algorithm=settings.jwt.JWT_ALGORITHM,
    )


def create_refresh_token(subject: str) -> str:
    expire = _utcnow() + timedelta(days=settings.jwt.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": _utcnow(),
        "exp": expire,
        "jti": str(uuid4()),
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        settings.jwt.JWT_SECRET_KEY,
        algorithm=settings.jwt.JWT_ALGORITHM,
    )


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises JWTError on failure.
    """
    return jwt.decode(
        token,
        settings.jwt.JWT_SECRET_KEY,
        algorithms=[settings.jwt.JWT_ALGORITHM],
    )


def get_subject_from_token(token: str) -> Optional[str]:
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    try:
        decode_token(token)
        return False
    except JWTError:
        return True
