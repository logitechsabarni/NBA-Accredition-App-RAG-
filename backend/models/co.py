"""
NBA Enterprise AI Platform — Course Outcome (CO) ORM Model
COs are the measurable learning outcomes for each course.
They form the primary mapping unit in CO-PO correlation.
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.postgres import Base

if TYPE_CHECKING:
    from models.course import Course
    from models.copo_map import COPOMap
    from models.attainment_record import AttainmentRecord


class BloomsTaxonomyLevel(str, PyEnum):
    """Bloom's Taxonomy cognitive levels used in NBA CO design."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class COStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CO(Base):
    """
    Course Outcome — a measurable competency students should achieve.
    Each CO maps to one or more POs via the COPOMap table.
    """

    __tablename__ = "course_outcomes"

    __table_args__ = (
        UniqueConstraint("code", "course_id", name="uq_co_code_course"),
        Index("ix_cos_course_id", "course_id"),
        Index("ix_cos_code", "code"),
        Index("ix_cos_status", "status"),
        Index("ix_cos_blooms_level", "blooms_level"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Identity
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="CO code e.g. CO1, CO2 (unique per course)",
    )
    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full CO statement as defined in course file",
    )
    short_description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Abbreviated CO description for display",
    )

    # Classification
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="CO ordering within the course (1, 2, 3...)",
    )
    blooms_level: Mapped[Optional[BloomsTaxonomyLevel]] = mapped_column(
        Enum(BloomsTaxonomyLevel, name="blooms_taxonomy_enum", create_type=True),
        nullable=True,
        comment="Bloom's Taxonomy cognitive level",
    )
    status: Mapped[COStatus] = mapped_column(
        Enum(COStatus, name="co_status_enum", create_type=True),
        nullable=False,
        default=COStatus.ACTIVE,
    )

    # Assessment mapping (which exam components assess this CO)
    # Stored as JSONB: {"cia1": 0.3, "cia2": 0.3, "ese": 0.4}
    assessment_weightage: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Assessment component weights for this CO (must sum to 1.0)",
    )

    # Assessment component marks for this CO
    # Stored as JSONB array: [{"student_id": "...", "marks": 45.0, "max_marks": 60.0}]
    cia1_mapping: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="CIA-1 question mapping: which questions assess this CO",
    )
    cia2_mapping: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="CIA-2 question mapping",
    )
    ese_mapping: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="ESE question mapping",
    )

    # Attainment data
    cia_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Computed CIA attainment percentage for this CO",
    )
    ese_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Computed ESE attainment percentage for this CO",
    )
    direct_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Weighted direct attainment (CIA + ESE combined)",
    )
    indirect_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Indirect attainment from surveys",
    )
    final_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Final CO attainment (direct + indirect weighted)",
    )
    attainment_target_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="Target percentage of students expected to attain this CO",
    )
    is_attained: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="True if final_attainment_percent >= attainment_target_percent",
    )

    # AI-generated fields
    ai_suggested: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether this CO statement was AI-generated/suggested",
    )
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="AI model confidence score for suggested CO",
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
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="cos",
        lazy="select",
    )
    copo_maps: Mapped[List["COPOMap"]] = relationship(
        "COPOMap",
        back_populates="co",
        cascade="all, delete-orphan",
        lazy="select",
    )
    attainment_records: Mapped[List["AttainmentRecord"]] = relationship(
        "AttainmentRecord",
        back_populates="co",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def compute_is_attained(self) -> Optional[bool]:
        """Compute attainment status based on final percentage vs target."""
        if self.final_attainment_percent is None:
            return None
        return self.final_attainment_percent >= self.attainment_target_percent

    def __repr__(self) -> str:
        return f"<CO id={self.id} code={self.code!r} course_id={self.course_id}>"
