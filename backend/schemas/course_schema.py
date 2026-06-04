"""
NBA Enterprise AI Platform — Course Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.course import CourseType, CourseCategory


class CourseBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=30)
    short_name: Optional[str] = Field(None, max_length=80)
    description: Optional[str] = None
    program_id: uuid.UUID
    faculty_id: Optional[uuid.UUID] = None
    semester: int = Field(..., ge=1, le=20)
    academic_year: Optional[str] = Field(None, max_length=10)
    batch_year: Optional[int] = None
    course_type: CourseType = CourseType.THEORY
    course_category: CourseCategory = CourseCategory.PROFESSIONAL_CORE
    credits: float = Field(default=3.0, ge=0.0, le=20.0)
    lecture_hours: Optional[int] = Field(None, ge=0)
    tutorial_hours: Optional[int] = Field(None, ge=0)
    practical_hours: Optional[int] = Field(None, ge=0)
    total_contact_hours: Optional[int] = Field(None, ge=0)
    cia_max_marks: float = Field(default=100.0, gt=0)
    ese_max_marks: float = Field(default=100.0, gt=0)
    cia_weightage_percent: float = Field(default=40.0, ge=0.0, le=100.0)
    ese_weightage_percent: float = Field(default=60.0, ge=0.0, le=100.0)
    passing_marks_percent: float = Field(default=40.0, ge=0.0, le=100.0)
    co_attainment_target_percent: float = Field(default=60.0, ge=0.0, le=100.0)
    threshold_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    is_elective: bool = False
    enrolled_students: Optional[int] = Field(None, ge=0)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("ese_weightage_percent")
    @classmethod
    def validate_assessment_weights(cls, v: float, info) -> float:
        cia = info.data.get("cia_weightage_percent", 40.0)
        if abs((cia + v) - 100.0) > 0.01:
            raise ValueError(
                f"cia_weightage_percent + ese_weightage_percent must equal 100. "
                f"Got {cia} + {v}"
            )
        return v


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    short_name: Optional[str] = Field(None, max_length=80)
    description: Optional[str] = None
    faculty_id: Optional[uuid.UUID] = None
    academic_year: Optional[str] = Field(None, max_length=10)
    batch_year: Optional[int] = None
    course_type: Optional[CourseType] = None
    course_category: Optional[CourseCategory] = None
    credits: Optional[float] = Field(None, ge=0.0, le=20.0)
    cia_max_marks: Optional[float] = Field(None, gt=0)
    ese_max_marks: Optional[float] = Field(None, gt=0)
    co_attainment_target_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    threshold_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    enrolled_students: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    short_name: Optional[str]
    description: Optional[str]
    program_id: uuid.UUID
    faculty_id: Optional[uuid.UUID]
    semester: int
    academic_year: Optional[str]
    batch_year: Optional[int]
    course_type: CourseType
    course_category: CourseCategory
    credits: float
    lecture_hours: Optional[int]
    tutorial_hours: Optional[int]
    practical_hours: Optional[int]
    total_contact_hours: Optional[int]
    cia_max_marks: float
    ese_max_marks: float
    cia_weightage_percent: float
    ese_weightage_percent: float
    passing_marks_percent: float
    co_attainment_target_percent: float
    threshold_percentage: float
    is_elective: bool
    is_active: bool
    enrolled_students: Optional[int]
    created_at: datetime
    updated_at: datetime


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    semester: int
    credits: float
    course_type: CourseType
    program_id: uuid.UUID
