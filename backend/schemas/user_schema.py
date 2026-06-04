"""
NBA Enterprise AI Platform — User Pydantic Schemas
Request/response validation for user-related API endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models.user import UserRole, UserStatus


# ----------------------------------------------------------------
# Base
# ----------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    employee_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=150)
    role: UserRole = UserRole.VIEWER
    department_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ----------------------------------------------------------------
# Create / Register
# ----------------------------------------------------------------

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    is_superuser: bool = False

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserRegister(BaseModel):
    """Public self-registration schema (limited fields)."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    department_id: Optional[uuid.UUID] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# ----------------------------------------------------------------
# Update
# ----------------------------------------------------------------

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    employee_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=150)
    department_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserAdminUpdate(UserUpdate):
    """Admin-only update fields."""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ----------------------------------------------------------------
# Response
# ----------------------------------------------------------------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: str
    employee_id: Optional[str]
    phone: Optional[str]
    designation: Optional[str]
    role: UserRole
    status: UserStatus
    department_id: Optional[uuid.UUID]
    is_active: bool
    is_verified: bool
    is_superuser: bool
    avatar_url: Optional[str]
    bio: Optional[str]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserSummary(BaseModel):
    """Minimal user info for nested responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole


class UserProfile(UserOut):
    """Extended profile — shown on /me endpoint."""
    pass


# ----------------------------------------------------------------
# Auth Schemas
# ----------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str
