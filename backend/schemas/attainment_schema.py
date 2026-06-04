"""
NBA Enterprise AI Platform — Attainment Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.attainment_record import (
    AttainmentType,
    AttainmentMethod,
    AttainmentStatus,
)


# ----------------------------------------------------------------
# Marks Input
# ----------------------------------------------------------------

class StudentMarksEntry(BaseModel):
    """Individual student marks for a CO assessment."""
    student_id: str = Field(..., description="Student roll number or UUID")
    marks_obtained: float = Field(..., ge=0.0)
    max_marks: float = Field(..., gt=0.0)

    @field_validator("marks_obtained")
    @classmethod
    def marks_cannot_exceed_max(cls, v: float, info) -> float:
        max_m = info.data.get("max_marks")
        if max_m is not None and v > max_m:
            raise ValueError(f"marks_obtained ({v}) cannot exceed max_marks ({max_m})")
        return v


class COAssessmentData(BaseModel):
    """Marks data for one CO across all assessment components."""
    co_id: uuid.UUID
    co_code: str
    cia1_marks: Optional[List[StudentMarksEntry]] = None
    cia2_marks: Optional[List[StudentMarksEntry]] = None
    ese_marks: Optional[List[StudentMarksEntry]] = None
    assignment_marks: Optional[List[StudentMarksEntry]] = None
    quiz_marks: Optional[List[StudentMarksEntry]] = None
    survey_score: Optional[float] = Field(None, ge=0.0, le=100.0)


# ----------------------------------------------------------------
# Attainment Computation Request
# ----------------------------------------------------------------

class AttainmentComputeRequest(BaseModel):
    """Request to compute CO attainment for a course."""
    course_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    batch_year: Optional[int] = None
    co_data: List[COAssessmentData]
    direct_weight: float = Field(default=0.8, ge=0.0, le=1.0)
    indirect_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    threshold_percent: float = Field(default=40.0, ge=0.0, le=100.0)
    attainment_target_percent: float = Field(default=60.0, ge=0.0, le=100.0)
    overwrite_existing: bool = False

    @field_validator("indirect_weight")
    @classmethod
    def weights_must_sum_to_one(cls, v: float, info) -> float:
        direct = info.data.get("direct_weight", 0.8)
        if abs((direct + v) - 1.0) > 0.001:
            raise ValueError(
                f"direct_weight + indirect_weight must equal 1.0. Got {direct + v:.4f}"
            )
        return v


class POAttainmentComputeRequest(BaseModel):
    """Request to compute PO attainment from CO attainments."""
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    batch_year: Optional[int] = None
    method: str = Field(default="weighted_average", description="Aggregation method")
    overwrite_existing: bool = False


# ----------------------------------------------------------------
# Attainment Record Schemas
# ----------------------------------------------------------------

class AttainmentRecordBase(BaseModel):
    reference_id: uuid.UUID
    reference_code: str
    attainment_type: AttainmentType
    program_id: uuid.UUID
    course_id: Optional[uuid.UUID] = None
    co_id: Optional[uuid.UUID] = None
    academic_year: str
    batch_year: Optional[int] = None
    semester: Optional[int] = None
    total_students: Optional[int] = None
    students_attained: Optional[int] = None
    attainment_target_percent: float = Field(default=60.0, ge=0.0, le=100.0)
    threshold_marks_percent: float = Field(default=40.0, ge=0.0, le=100.0)
    calculation_method: AttainmentMethod = AttainmentMethod.FINAL_WEIGHTED
    direct_weight: float = Field(default=0.8, ge=0.0, le=1.0)
    indirect_weight: float = Field(default=0.2, ge=0.0, le=1.0)


class AttainmentRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference_id: uuid.UUID
    reference_code: str
    attainment_type: AttainmentType
    program_id: uuid.UUID
    course_id: Optional[uuid.UUID]
    co_id: Optional[uuid.UUID]
    academic_year: str
    batch_year: Optional[int]
    semester: Optional[int]
    total_students: Optional[int]
    students_attained: Optional[int]
    cia_attainment_percent: Optional[float]
    ese_attainment_percent: Optional[float]
    direct_attainment_percent: Optional[float]
    indirect_attainment_percent: Optional[float]
    final_attainment_percent: Optional[float]
    attainment_target_percent: float
    threshold_marks_percent: float
    is_attained: Optional[bool]
    gap_percent: Optional[float]
    calculation_method: AttainmentMethod
    direct_weight: float
    indirect_weight: float
    status: AttainmentStatus
    computed_at: Optional[datetime]
    computed_by: Optional[uuid.UUID]
    verified_by: Optional[uuid.UUID]
    verified_at: Optional[datetime]
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    remarks: Optional[str]
    previous_attainment_percent: Optional[float]
    improvement_percent: Optional[float]
    created_at: datetime
    updated_at: datetime


class AttainmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference_code: str
    attainment_type: AttainmentType
    final_attainment_percent: Optional[float]
    attainment_target_percent: float
    is_attained: Optional[bool]
    gap_percent: Optional[float]
    status: AttainmentStatus
    academic_year: str


# ----------------------------------------------------------------
# Aggregated / Report Views
# ----------------------------------------------------------------

class COAttainmentSummaryRow(BaseModel):
    co_code: str
    co_statement: str
    cia_attainment: Optional[float]
    ese_attainment: Optional[float]
    direct_attainment: Optional[float]
    indirect_attainment: Optional[float]
    final_attainment: Optional[float]
    target: float
    is_attained: Optional[bool]
    gap: Optional[float]


class CourseAttainmentReport(BaseModel):
    course_id: uuid.UUID
    course_code: str
    course_name: str
    academic_year: str
    total_students: int
    cos: List[COAttainmentSummaryRow]
    average_co_attainment: Optional[float]
    cos_attained_count: int
    cos_total_count: int


class POAttainmentRow(BaseModel):
    po_code: str
    po_name: str
    po_type: str
    attainment_percent: Optional[float]
    target_percent: float
    is_attained: Optional[bool]
    gap_percent: Optional[float]
    improvement_percent: Optional[float]
    contributing_cos: List[str]


class ProgramAttainmentReport(BaseModel):
    program_id: uuid.UUID
    program_code: str
    program_name: str
    academic_year: str
    pos: List[POAttainmentRow]
    pos_attained_count: int
    pos_total_count: int
    overall_attainment_percent: Optional[float]


class AttainmentVerifyRequest(BaseModel):
    attainment_record_ids: List[uuid.UUID]
    verified_by: uuid.UUID
    remarks: Optional[str] = None


class AttainmentApproveRequest(BaseModel):
    attainment_record_ids: List[uuid.UUID]
    approved_by: uuid.UUID
    approved: bool = True
    remarks: Optional[str] = None
