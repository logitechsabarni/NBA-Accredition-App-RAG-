"""
NBA Enterprise AI Platform — Attainment Record ORM Model
Stores computed attainment results for COs and POs per academic cycle.
This is the primary audit-ready record of NBA attainment calculations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

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
    from models.co import CO
    from models.program import Program


class AttainmentType(str, PyEnum):
    """What is being measured in this record."""
    CO = "co"
    PO = "po"
    PSO = "pso"


class AttainmentMethod(str, PyEnum):
    """Calculation method used."""
    DIRECT_CIA = "direct_cia"
    DIRECT_ESE = "direct_ese"
    DIRECT_COMBINED = "direct_combined"
    INDIRECT_SURVEY = "indirect_survey"
    FINAL_WEIGHTED = "final_weighted"
    PO_AGGREGATED = "po_aggregated"


class AttainmentStatus(str, PyEnum):
    DRAFT = "draft"
    COMPUTED = "computed"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"


class AttainmentRecord(Base):
    """
    Immutable attainment record for a CO or PO in a given academic cycle.
    Stores all intermediate and final computation data for audit.
    """

    __tablename__ = "attainment_records"

    __table_args__ = (
        UniqueConstraint(
            "reference_id", "attainment_type", "academic_year", "batch_year",
            name="uq_attainment_ref_type_year"
        ),
        Index("ix_attainment_reference_id", "reference_id"),
        Index("ix_attainment_program_id", "program_id"),
        Index("ix_attainment_course_id", "course_id"),
        Index("ix_attainment_co_id", "co_id"),
        Index("ix_attainment_type", "attainment_type"),
        Index("ix_attainment_academic_year", "academic_year"),
        Index("ix_attainment_status", "status"),
        Index("ix_attainment_is_attained", "is_attained"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Reference — the CO or PO this record describes
    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="UUID of the CO or PO being measured",
    )
    reference_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Denormalised code e.g. CO1, PO3 for fast display",
    )
    attainment_type: Mapped[AttainmentType] = mapped_column(
        Enum(AttainmentType, name="attainment_type_enum", create_type=True),
        nullable=False,
        comment="Whether this is a CO or PO attainment record",
    )

    # Context
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        comment="Relevant for CO attainment records",
    )
    co_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to CO if attainment_type = CO",
    )

    # Academic cycle
    academic_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Academic year e.g. 2023-24",
    )
    batch_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Student batch entry year",
    )
    semester: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Semester number for course-level attainment",
    )

    # Student population
    total_students: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total students in the assessment cohort",
    )
    students_attained: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of students who attained the CO/PO",
    )

    # Assessment marks data (stored as JSONB for flexibility)
    cia1_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="CIA-1 marks per student: {student_id: marks}",
    )
    cia2_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="CIA-2 marks per student",
    )
    ese_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="ESE marks per student",
    )
    assignment_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Assignment marks per student",
    )
    survey_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Indirect survey responses",
    )

    # Computed attainment values
    cia_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="CIA component attainment percentage",
    )
    ese_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="ESE component attainment percentage",
    )
    direct_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Weighted direct attainment (CIA + ESE)",
    )
    indirect_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Indirect attainment from surveys",
    )
    final_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Final attainment = direct_weight*direct + indirect_weight*indirect",
    )

    # Target and result
    attainment_target_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="Target attainment percentage for this cycle",
    )
    threshold_marks_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=40.0,
        comment="Minimum marks% to count a student as 'attained'",
    )
    is_attained: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="True if final_attainment_percent >= attainment_target_percent",
    )
    gap_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Gap to target (negative means target exceeded)",
    )

    # Calculation metadata
    calculation_method: Mapped[AttainmentMethod] = mapped_column(
        Enum(AttainmentMethod, name="attainment_method_enum", create_type=True),
        nullable=False,
        default=AttainmentMethod.FINAL_WEIGHTED,
    )
    direct_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.8,
        comment="Weight applied to direct assessment (0.0-1.0)",
    )
    indirect_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.2,
        comment="Weight applied to indirect assessment",
    )
    calculation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Any notes or exceptions in the calculation",
    )

    # Verification & Approval
    status: Mapped[AttainmentStatus] = mapped_column(
        Enum(AttainmentStatus, name="attainment_status_enum", create_type=True),
        nullable=False,
        default=AttainmentStatus.DRAFT,
    )
    computed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when attainment was computed",
    )
    computed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User or agent that ran the computation",
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Approver remarks",
    )

    # CI comparison
    previous_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Previous cycle attainment for CI comparison",
    )
    improvement_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Change vs previous cycle (positive = improved)",
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Relationships
    program: Mapped["Program"] = relationship(
        "Program",
        lazy="select",
        foreign_keys=[program_id],
    )
    course: Mapped[Optional["Course"]] = relationship(
        "Course",
        back_populates="attainment_records",
        lazy="select",
    )
    co: Mapped[Optional["CO"]] = relationship(
        "CO",
        back_populates="attainment_records",
        lazy="select",
    )

    def compute_attainment_status(self) -> None:
        """Derive is_attained and gap_percent from current values."""
        if self.final_attainment_percent is not None:
            self.is_attained = self.final_attainment_percent >= self.attainment_target_percent
            self.gap_percent = self.attainment_target_percent - self.final_attainment_percent
        if (
            self.final_attainment_percent is not None
            and self.previous_attainment_percent is not None
        ):
            self.improvement_percent = (
                self.final_attainment_percent - self.previous_attainment_percent
            )

    def __repr__(self) -> str:
        return (
            f"<AttainmentRecord id={self.id} type={self.attainment_type} "
            f"code={self.reference_code!r} year={self.academic_year}>"
        )
