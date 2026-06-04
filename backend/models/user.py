"""
NBA Enterprise AI Platform — User ORM Model
SQLAlchemy 2.0 async-compatible model with full audit support.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.postgres import Base

if TYPE_CHECKING:
    from models.department import Department
    from models.audit_log import AuditLog


class UserRole(str, PyEnum):
    SUPER_ADMIN = "super_admin"
    INSTITUTION_ADMIN = "institution_admin"
    HOD = "hod"
    FACULTY = "faculty"
    NBA_COORDINATOR = "nba_coordinator"
    VIEWER = "viewer"


class UserStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """
    Core user entity for all platform actors.
    Supports multi-role, multi-institution design.
    """

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_department_id", "department_id"),
        Index("ix_users_is_active", "is_active"),
        {"schema": None},
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Unique user identifier",
    )

    # Identity
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Unique email address used for login",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Display username",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full name of the user",
    )
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Institution employee ID",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Contact phone number",
    )
    designation: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Job designation e.g. Associate Professor",
    )

    # Authentication
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether the user account is active",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether email has been verified",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Superuser flag — bypasses all permission checks",
    )

    # Role & Status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_type=True),
        nullable=False,
        default=UserRole.VIEWER,
        comment="Primary platform role",
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status_enum", create_type=True),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        comment="Account lifecycle status",
    )

    # Relationships — Foreign Keys
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated department (nullable for admins)",
    )

    # Token / Session management
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful login",
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last password change",
    )
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed refresh token for rotation-based auth",
    )

    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="URL to profile avatar image",
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Short user biography",
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last-updated timestamp (UTC)",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft-delete timestamp; NULL = not deleted",
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="users",
        lazy="select",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(tz=timezone.utc)
        self.is_active = False
        self.status = UserStatus.INACTIVE

    def record_login(self) -> None:
        self.last_login_at = datetime.now(tz=timezone.utc)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
