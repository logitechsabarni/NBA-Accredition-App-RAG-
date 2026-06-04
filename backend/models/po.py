"""
NBA Enterprise AI Platform — Program Outcome (PO) ORM Model
POs are the graduate attributes defined by NBA for each program.
NBA mandates 12 POs (PO1-PO12) + program-specific PSOs.
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
    from models.program import Program
    from models.copo_map import COPOMap


class POType(str, PyEnum):
    """
    PO: Standard NBA Program Outcome (PO1-PO12)
    PSO: Program Specific Outcome (program-defined, typically PSO1-PSO3)
    """
    PO = "po"
    PSO = "pso"


class POStatus(str, PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# NBA standard PO definitions (for seeding)
NBA_STANDARD_POS = [
    ("PO1", "Engineering Knowledge", "Apply knowledge of mathematics, science, engineering fundamentals, and engineering specialization to the solution of complex engineering problems."),
    ("PO2", "Problem Analysis", "Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions using first principles of mathematics, natural sciences, and engineering sciences."),
    ("PO3", "Design/Development of Solutions", "Design solutions for complex engineering problems and design system components or processes that meet the specified needs with appropriate consideration for the public health and safety, and the cultural, societal, and environmental considerations."),
    ("PO4", "Conduct Investigations of Complex Problems", "Use research-based knowledge and research methods including design of experiments, analysis and interpretation of data, and synthesis of the information to provide valid conclusions."),
    ("PO5", "Modern Tool Usage", "Create, select, and apply appropriate techniques, resources, and modern engineering and IT tools including prediction and modeling to complex engineering activities with an understanding of the limitations."),
    ("PO6", "The Engineer and Society", "Apply reasoning informed by the contextual knowledge to assess societal, health, safety, legal and cultural issues and the consequent responsibilities relevant to the professional engineering practice."),
    ("PO7", "Environment and Sustainability", "Understand the impact of the professional engineering solutions in societal and environmental contexts, and demonstrate the knowledge of, and need for sustainable development."),
    ("PO8", "Ethics", "Apply ethical principles and commit to professional ethics and responsibilities and norms of the engineering practice."),
    ("PO9", "Individual and Team Work", "Function effectively as an individual, and as a member or leader in diverse teams, and in multidisciplinary settings."),
    ("PO10", "Communication", "Communicate effectively on complex engineering activities with the engineering community and with society at large, such as, being able to comprehend and write effective reports and design documentation, make effective presentations, and give and receive clear instructions."),
    ("PO11", "Project Management and Finance", "Demonstrate knowledge and understanding of the engineering and management principles and apply these to one's own work, as a member and leader in a team, to manage projects and in multidisciplinary environments."),
    ("PO12", "Life-long Learning", "Recognize the need for, and have the preparation and ability to engage in independent and life-long learning in the broadest context of technological change."),
]


class PO(Base):
    """
    Program Outcome — graduate attribute for a program.
    Includes both NBA-mandated POs (PO1-PO12) and PSOs.
    """

    __tablename__ = "program_outcomes"

    __table_args__ = (
        UniqueConstraint("code", "program_id", name="uq_po_code_program"),
        Index("ix_pos_program_id", "program_id"),
        Index("ix_pos_code", "code"),
        Index("ix_pos_po_type", "po_type"),
        Index("ix_pos_is_active", "is_active"),
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
        String(10),
        nullable=False,
        comment="PO/PSO code e.g. PO1, PO12, PSO1",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short PO name e.g. Engineering Knowledge",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full PO statement as per NBA curriculum",
    )
    short_description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Abbreviated description for display",
    )

    # Classification
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_type: Mapped[POType] = mapped_column(
        Enum(POType, name="po_type_enum", create_type=True),
        nullable=False,
        default=POType.PO,
        comment="PO (standard NBA) or PSO (program-specific)",
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Ordering number (1-12 for POs, 1-3 for PSOs)",
    )
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, name="po_status_enum", create_type=True),
        nullable=False,
        default=POStatus.ACTIVE,
    )
    is_nba_standard: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="True for NBA-mandated PO1-PO12, False for PSOs",
    )

    # Attainment data
    attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Computed PO attainment percentage for the program",
    )
    attainment_target_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="Target PO attainment percentage",
    )
    is_attained: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="True if attainment_percent >= attainment_target_percent",
    )
    gap_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Gap = attainment_target_percent - attainment_percent (negative = exceeded target)",
    )

    # CI tracking
    previous_attainment_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Attainment from previous cycle for trend analysis",
    )
    improvement_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Improvement over previous cycle",
    )

    # Operational
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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
        back_populates="pos",
        lazy="select",
    )
    copo_maps: Mapped[List["COPOMap"]] = relationship(
        "COPOMap",
        back_populates="po",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def compute_attainment_status(self) -> None:
        """Update derived attainment fields in-place."""
        if self.attainment_percent is not None:
            self.is_attained = self.attainment_percent >= self.attainment_target_percent
            self.gap_percent = self.attainment_target_percent - self.attainment_percent
            if self.previous_attainment_percent is not None:
                self.improvement_percent = self.attainment_percent - self.previous_attainment_percent

    def __repr__(self) -> str:
        return f"<PO id={self.id} code={self.code!r} program_id={self.program_id}>"
