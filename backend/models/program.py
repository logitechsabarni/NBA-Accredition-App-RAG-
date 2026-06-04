"""
NBA Enterprise AI Platform — Program ORM Model
An academic program (B.Tech, M.Tech, etc.) within a department.
Programs are the primary NBA accreditation unit.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
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
    from models.department import Department
    from models.course import Course
    from models.po import PO
    from models.sar_document import SARDocument


class ProgramLevel(str, PyEnum):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"
    DOCTORAL = "doctoral"
    DIPLOMA = "diploma"


class ProgramStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"
    ACCREDITATION_PENDING = "accreditation_pending"
    ACCREDITED = "accredited"


class Program(Base):
    """
    Academic program — the primary unit for NBA accreditation.
    Each program defines its own POs, courses, and attainment targets.
    """

    __tablename__ = "programs"

    __table_args__ = (
        UniqueConstraint("code", "department_id", name="uq_program_code_dept"),
        Index("ix_programs_department_id", "department_id"),
        Index("ix_programs_code", "code"),
        Index("ix_programs_status", "status"),
        Index("ix_programs_is_active", "is_active"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full program name e.g. B.Tech Computer Science and Engineering",
    )
    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Program code e.g. BTCSE, MTECE",
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Abbreviated program name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Program description / overview",
    )

    # Classification
    level: Mapped[ProgramLevel] = mapped_column(
        Enum(ProgramLevel, name="program_level_enum", create_type=True),
        nullable=False,
        default=ProgramLevel.UNDERGRADUATE,
        comment="Program academic level",
    )
    duration_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
        comment="Program duration in years",
    )
    total_semesters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8,
        comment="Total number of semesters",
    )
    credits_required: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum credits required for graduation",
    )

    # Foreign Key
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owning department",
    )

    # Accreditation
    status: Mapped[ProgramStatus] = mapped_column(
        Enum(ProgramStatus, name="program_status_enum", create_type=True),
        nullable=False,
        default=ProgramStatus.ACTIVE,
        comment="Current accreditation lifecycle status",
    )
    nba_tier: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="NBA accreditation tier (1 or 2)",
    )
    current_accreditation_cycle: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="e.g. 2022-25",
    )
    accreditation_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    accreditation_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sar_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last SAR submission",
    )

    # Targets
    co_attainment_target: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="CO attainment target percentage (typically 60%)",
    )
    po_attainment_target: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="PO attainment target percentage",
    )
    direct_attainment_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=80.0,
        comment="Weight of direct assessment in CO attainment (typically 80%)",
    )
    indirect_attainment_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=20.0,
        comment="Weight of indirect assessment (typically 20%)",
    )

    # Operational
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    intake_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Year from which this program configuration applies",
    )
    regulation_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Regulation year e.g. 2019, 2021",
    )

    # NBA-specific
    program_educational_objectives: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="PEOs as free text; structured versions in PO table",
    )
    vision: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Program vision statement",
    )
    mission: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Program mission statement",
    )

    # Audit
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
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="programs",
        lazy="select",
    )
    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="select",
    )
    pos: Mapped[List["PO"]] = relationship(
        "PO",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="select",
    )
    sar_documents: Mapped[List["SARDocument"]] = relationship(
        "SARDocument",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<Program id={self.id} code={self.code!r} name={self.name!r}>"
