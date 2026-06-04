"""
NBA Enterprise AI Platform — Department ORM Model
Represents an academic department within an institution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.postgres import Base

if TYPE_CHECKING:
    from models.user import User
    from models.program import Program


class Department(Base):
    """
    Academic department entity.
    A department owns programs, which own courses.
    """

    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint("code", "institution_id", name="uq_dept_code_institution"),
        Index("ix_departments_code", "code"),
        Index("ix_departments_institution_id", "institution_id"),
        Index("ix_departments_is_active", "is_active"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Unique department identifier",
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full department name e.g. Computer Science and Engineering",
    )
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Short department code e.g. CSE, ECE, MECH",
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Abbreviated name for display",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Department description",
    )

    # Institution (multi-tenancy)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Owning institution UUID (tenant isolation key)",
    )
    institution_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Denormalised institution name for quick display",
    )

    # Leadership
    hod_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the Head of Department",
    )
    hod_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email of the Head of Department",
    )
    hod_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to User record of current HOD",
    )

    # Accreditation
    nba_accredited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether department currently holds NBA accreditation",
    )
    nba_accreditation_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Year of last NBA accreditation grant",
    )
    nba_valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="NBA accreditation expiry date",
    )
    naac_grade: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="NAAC grade of the institution e.g. A++, A+",
    )

    # Operational
    established_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Year the department was established",
    )
    intake_capacity: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Approved student intake per batch",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Soft-active flag",
    )

    # Contact
    office_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    office_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft-delete timestamp",
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User UUID who created this record",
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User UUID who last updated this record",
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="department",
        lazy="select",
        foreign_keys="User.department_id",
    )
    programs: Mapped[List["Program"]] = relationship(
        "Program",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<Department id={self.id} code={self.code!r} name={self.name!r}>"
