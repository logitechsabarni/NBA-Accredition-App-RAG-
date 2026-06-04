"""
NBA Enterprise AI Platform — SAR Document ORM Model
Self-Assessment Report — the primary NBA submission document.
Tracks the complete lifecycle of SAR generation and submission.
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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.postgres import Base

if TYPE_CHECKING:
    from models.program import Program


class SARStatus(str, PyEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    AI_GENERATING = "ai_generating"
    REVIEW = "review"
    REVISION_REQUESTED = "revision_requested"
    HOD_APPROVED = "hod_approved"
    PRINCIPAL_APPROVED = "principal_approved"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class SARVersion(str, PyEnum):
    """NBA SAR version/tier."""
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"


class SARDocument(Base):
    """
    Self-Assessment Report document.
    Each SAR covers one program for one accreditation cycle.
    """

    __tablename__ = "sar_documents"

    __table_args__ = (
        Index("ix_sar_program_id", "program_id"),
        Index("ix_sar_status", "status"),
        Index("ix_sar_academic_year", "academic_year"),
        Index("ix_sar_is_active", "is_active"),
        Index("ix_sar_created_by", "created_by"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Identity
    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="SAR document title",
    )
    document_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Unique document number assigned on submission",
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Document version number (incremented on revision)",
    )

    # Program & Cycle
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Academic year this SAR covers e.g. 2023-24",
    )
    accreditation_cycle: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="NBA accreditation cycle e.g. 2022-25",
    )
    sar_version: Mapped[SARVersion] = mapped_column(
        Enum(SARVersion, name="sar_version_enum", create_type=True),
        nullable=False,
        default=SARVersion.TIER_2,
        comment="NBA accreditation tier",
    )

    # Status
    status: Mapped[SARStatus] = mapped_column(
        Enum(SARStatus, name="sar_status_enum", create_type=True),
        nullable=False,
        default=SARStatus.DRAFT,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # SAR Content — stored as structured JSONB sections
    # Each section corresponds to a SAR criterion
    section_1_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 1: Vision, Mission, PEOs",
    )
    section_2_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 2: Program Curriculum and Teaching-Learning Processes",
    )
    section_3_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 3: Course Outcomes and Program Outcomes",
    )
    section_4_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 4: Students Performance",
    )
    section_5_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 5: Faculty Information and Contributions",
    )
    section_6_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 6: Facilities and Technical Support",
    )
    section_7_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 7: Continuous Improvement",
    )
    section_8_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Criterion 8: First Year Academics",
    )
    additional_sections: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Any supplementary sections",
    )

    # NBA Score Tracking
    total_marks_available: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Total marks available in this SAR tier",
    )
    marks_obtained: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Total marks obtained across all criteria",
    )
    readiness_score_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Overall NBA readiness score percentage",
    )
    gap_analysis_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="AI-generated gap analysis by criterion",
    )

    # AI Generation metadata
    ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether SAR content was AI-assisted",
    )
    ai_model_used: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="AI model used for generation e.g. gpt-4o, granite-13b",
    )
    ai_generation_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ai_generation_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ai_tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total LLM tokens consumed during generation",
    )

    # File storage
    pdf_file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Path to generated PDF file",
    )
    pdf_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    word_file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Path to generated Word document",
    )
    supporting_documents: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of attached supporting documents with paths",
    )

    # Submission & Review workflow
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of submission to NBA",
    )
    submission_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="NBA submission reference number",
    )
    hod_approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    hod_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    principal_approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    principal_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    review_comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reviewer comments for revision",
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
    program: Mapped["Program"] = relationship(
        "Program",
        back_populates="sar_documents",
        lazy="select",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def completion_percent(self) -> float:
        """Estimate section completion based on populated JSONB sections."""
        sections = [
            self.section_1_data,
            self.section_2_data,
            self.section_3_data,
            self.section_4_data,
            self.section_5_data,
            self.section_6_data,
            self.section_7_data,
            self.section_8_data,
        ]
        filled = sum(1 for s in sections if s is not None)
        return round((filled / len(sections)) * 100, 2)

    def __repr__(self) -> str:
        return (
            f"<SARDocument id={self.id} program_id={self.program_id} "
            f"status={self.status} year={self.academic_year}>"
        )
