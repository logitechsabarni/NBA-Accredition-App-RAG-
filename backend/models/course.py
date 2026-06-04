"""
NBA Enterprise AI Platform — Course ORM Model
An academic course belonging to a program.
Courses contain COs and are the primary unit for attainment calculation.
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
    from models.co import CO
    from models.attainment_record import AttainmentRecord


class CourseType(str, PyEnum):
    THEORY = "theory"
    LAB = "lab"
    THEORY_LAB = "theory_lab"
    PROJECT = "project"
    SEMINAR = "seminar"
    ELECTIVE = "elective"
    MANDATORY = "mandatory"
    OPEN_ELECTIVE = "open_elective"


class CourseCategory(str, PyEnum):
    PROFESSIONAL_CORE = "professional_core"
    PROFESSIONAL_ELECTIVE = "professional_elective"
    BASIC_SCIENCE = "basic_science"
    ENGINEERING_SCIENCE = "engineering_science"
    HUMANITIES = "humanities"
    OPEN_ELECTIVE = "open_elective"
    PROJECT_BASED = "project_based"
    INTERNSHIP = "internship"


class Course(Base):
    """
    Academic course within a program.
    Stores assessment weightages, credits, and evaluation structure.
    """

    __tablename__ = "courses"

    __table_args__ = (
        UniqueConstraint("code", "program_id", "semester", name="uq_course_code_program_sem"),
        Index("ix_courses_program_id", "program_id"),
        Index("ix_courses_code", "code"),
        Index("ix_courses_semester", "semester"),
        Index("ix_courses_is_active", "is_active"),
        Index("ix_courses_faculty_id", "faculty_id"),
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
        comment="Full course name",
    )
    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Course code e.g. CS6001",
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(80),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Course description / syllabus overview",
    )

    # Structure
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    faculty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Faculty member teaching this course",
    )
    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Semester number (1-8 for B.Tech)",
    )
    academic_year: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="e.g. 2023-24",
    )
    batch_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Student batch entry year",
    )

    # Classification
    course_type: Mapped[CourseType] = mapped_column(
        Enum(CourseType, name="course_type_enum", create_type=True),
        nullable=False,
        default=CourseType.THEORY,
    )
    course_category: Mapped[CourseCategory] = mapped_column(
        Enum(CourseCategory, name="course_category_enum", create_type=True),
        nullable=False,
        default=CourseCategory.PROFESSIONAL_CORE,
    )

    # Credits & Contact hours
    credits: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=3.0,
        comment="Credit hours",
    )
    lecture_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Lecture hours per week",
    )
    tutorial_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Tutorial hours per week",
    )
    practical_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Practical/lab hours per week",
    )
    total_contact_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total contact hours per semester",
    )

    # Assessment Structure (marks)
    cia_max_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
        comment="CIA (Continuous Internal Assessment) maximum marks",
    )
    ese_max_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
        comment="ESE (End Semester Exam) maximum marks",
    )
    cia_weightage_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=40.0,
        comment="CIA weightage in final grade (percentage)",
    )
    ese_weightage_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="ESE weightage in final grade (percentage)",
    )
    passing_marks_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=40.0,
        comment="Minimum percentage required to pass",
    )

    # CO Attainment Targets
    co_attainment_target_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        comment="Target percentage of students to attain COs (default 60%)",
    )
    threshold_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=40.0,
        comment="Minimum marks percentage to consider a student as 'attained'",
    )

    # Assessment component breakdown
    assignment_weightage: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Assignment marks weightage",
    )
    quiz_weightage: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Quiz marks weightage",
    )
    mid_sem_1_weightage: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Mid-semester 1 marks weightage",
    )
    mid_sem_2_weightage: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Mid-semester 2 marks weightage",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    is_elective: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Student count
    enrolled_students: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of students enrolled in this course",
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
        back_populates="courses",
        lazy="select",
    )
    cos: Mapped[List["CO"]] = relationship(
        "CO",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="select",
    )
    attainment_records: Mapped[List["AttainmentRecord"]] = relationship(
        "AttainmentRecord",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<Course id={self.id} code={self.code!r} semester={self.semester}>"
