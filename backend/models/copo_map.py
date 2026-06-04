"""
NBA Enterprise AI Platform — CO-PO Mapping ORM Model
Stores the correlation value between each CO and each PO.
NBA correlation scale: 0 (none), 1 (low), 2 (medium), 3 (high).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
    from models.co import CO
    from models.po import PO


class MappingMethod(str, PyEnum):
    """How the CO-PO mapping correlation was determined."""
    MANUAL = "manual"
    AI_SUGGESTED = "ai_suggested"
    AI_APPROVED = "ai_approved"
    IMPORTED = "imported"


class CorrelationLevel(int, PyEnum):
    """NBA-standard CO-PO correlation levels."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class COPOMap(Base):
    """
    CO-PO Mapping — stores correlation between a CO and a PO.

    Each record represents: CO_X → PO_Y = correlation_value (0-3).
    The full CO-PO matrix is reconstructed by joining all records
    for a given course or program.
    """

    __tablename__ = "copo_maps"

    __table_args__ = (
        UniqueConstraint("co_id", "po_id", name="uq_copo_map_co_po"),
        CheckConstraint(
            "correlation_value IN (0, 1, 2, 3)",
            name="chk_copo_correlation_value",
        ),
        Index("ix_copo_maps_co_id", "co_id"),
        Index("ix_copo_maps_po_id", "po_id"),
        Index("ix_copo_maps_correlation_value", "correlation_value"),
        Index("ix_copo_maps_mapping_method", "mapping_method"),
        Index("ix_copo_maps_program_id", "program_id"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Core mapping
    co_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        comment="Source Course Outcome",
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        comment="Target Program Outcome",
    )

    # Denormalised program reference for efficient queries
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Program this mapping belongs to (denormalised)",
    )

    # Correlation
    correlation_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="NBA correlation: 0=none, 1=low, 2=medium, 3=high",
    )

    # Mapping metadata
    mapping_method: Mapped[MappingMethod] = mapped_column(
        Enum(MappingMethod, name="mapping_method_enum", create_type=True),
        nullable=False,
        default=MappingMethod.MANUAL,
        comment="How this mapping was created",
    )
    justification: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Justification/rationale for the correlation value",
    )
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="AI confidence score (0.0-1.0) if AI-suggested",
    )
    ai_reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated reasoning for the suggested correlation",
    )

    # Approval workflow
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether this mapping has been approved by faculty/HOD",
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User UUID who approved this mapping",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of approval",
    )

    # Versioning — for CI tracking
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Mapping version for change tracking",
    )
    academic_year: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Academic year this mapping applies to e.g. 2023-24",
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
    co: Mapped["CO"] = relationship(
        "CO",
        back_populates="copo_maps",
        lazy="select",
    )
    po: Mapped["PO"] = relationship(
        "PO",
        back_populates="copo_maps",
        lazy="select",
    )

    @property
    def correlation_label(self) -> str:
        labels = {0: "None", 1: "Low", 2: "Medium", 3: "High"}
        return labels.get(self.correlation_value, "Unknown")

    def __repr__(self) -> str:
        return (
            f"<COPOMap co_id={self.co_id} po_id={self.po_id} "
            f"correlation={self.correlation_value}>"
        )
