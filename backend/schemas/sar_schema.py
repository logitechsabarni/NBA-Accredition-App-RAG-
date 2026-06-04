"""
NBA Enterprise AI Platform — SAR Document Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.sar_document import SARStatus, SARVersion


class SARBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=512)
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    accreditation_cycle: Optional[str] = Field(None, max_length=20)
    sar_version: SARVersion = SARVersion.TIER_2

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2,4}$", v):
            raise ValueError(
                f"academic_year must be in format YYYY-YY or YYYY-YYYY e.g. 2023-24. Got: {v}"
            )
        return v


class SARCreate(SARBase):
    pass


class SARUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=512)
    status: Optional[SARStatus] = None
    section_1_data: Optional[Dict[str, Any]] = None
    section_2_data: Optional[Dict[str, Any]] = None
    section_3_data: Optional[Dict[str, Any]] = None
    section_4_data: Optional[Dict[str, Any]] = None
    section_5_data: Optional[Dict[str, Any]] = None
    section_6_data: Optional[Dict[str, Any]] = None
    section_7_data: Optional[Dict[str, Any]] = None
    section_8_data: Optional[Dict[str, Any]] = None
    additional_sections: Optional[Dict[str, Any]] = None
    review_comments: Optional[str] = None


class SARSectionUpdate(BaseModel):
    """Update a specific SAR section."""
    section_number: int = Field(..., ge=1, le=8)
    section_data: Dict[str, Any]
    save_as_draft: bool = True


class SARGenerateRequest(BaseModel):
    """Request AI generation of SAR content."""
    sar_id: uuid.UUID
    sections_to_generate: Optional[List[int]] = Field(
        None,
        description="List of section numbers to generate (1-8). Null = all sections.",
    )
    model_preference: Optional[str] = Field(
        None,
        description="LLM model preference: openai, granite, auto",
    )
    include_attainment_data: bool = True
    include_ci_recommendations: bool = True
    additional_context: Optional[str] = None


class SARApprovalRequest(BaseModel):
    sar_id: uuid.UUID
    approved_by: uuid.UUID
    approved: bool = True
    comments: Optional[str] = None
    approval_stage: str = Field(
        ...,
        description="Approval stage: hod, principal",
    )

    @field_validator("approval_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in ("hod", "principal"):
            raise ValueError("approval_stage must be 'hod' or 'principal'")
        return v


class SARSubmitRequest(BaseModel):
    sar_id: uuid.UUID
    submission_reference: Optional[str] = None
    confirmation: bool = Field(
        ...,
        description="Must be True to confirm submission to NBA",
    )


class SAROut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    document_number: Optional[str]
    version_number: int
    program_id: uuid.UUID
    academic_year: str
    accreditation_cycle: Optional[str]
    sar_version: SARVersion
    status: SARStatus
    is_active: bool
    section_1_data: Optional[Dict[str, Any]]
    section_2_data: Optional[Dict[str, Any]]
    section_3_data: Optional[Dict[str, Any]]
    section_4_data: Optional[Dict[str, Any]]
    section_5_data: Optional[Dict[str, Any]]
    section_6_data: Optional[Dict[str, Any]]
    section_7_data: Optional[Dict[str, Any]]
    section_8_data: Optional[Dict[str, Any]]
    additional_sections: Optional[Dict[str, Any]]
    total_marks_available: Optional[float]
    marks_obtained: Optional[float]
    readiness_score_percent: Optional[float]
    gap_analysis_summary: Optional[Dict[str, Any]]
    ai_generated: bool
    ai_model_used: Optional[str]
    ai_generation_started_at: Optional[datetime]
    ai_generation_completed_at: Optional[datetime]
    ai_tokens_used: Optional[int]
    pdf_file_path: Optional[str]
    pdf_generated_at: Optional[datetime]
    word_file_path: Optional[str]
    submitted_at: Optional[datetime]
    submission_reference: Optional[str]
    hod_approved_by: Optional[uuid.UUID]
    hod_approved_at: Optional[datetime]
    principal_approved_by: Optional[uuid.UUID]
    principal_approved_at: Optional[datetime]
    review_comments: Optional[str]
    completion_percent: float
    created_at: datetime
    updated_at: datetime


class SARSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    program_id: uuid.UUID
    academic_year: str
    sar_version: SARVersion
    status: SARStatus
    readiness_score_percent: Optional[float]
    completion_percent: float
    ai_generated: bool
    submitted_at: Optional[datetime]
    created_at: datetime


class SARGapAnalysisItem(BaseModel):
    criterion_number: int
    criterion_name: str
    marks_available: float
    marks_obtained: Optional[float]
    gap: Optional[float]
    gap_percent: Optional[float]
    recommendations: List[str]
    priority: str  # high, medium, low


class SARGapAnalysis(BaseModel):
    sar_id: uuid.UUID
    program_id: uuid.UUID
    academic_year: str
    overall_readiness_score: Optional[float]
    criteria: List[SARGapAnalysisItem]
    top_gaps: List[str]
    strengths: List[str]
    immediate_actions: List[str]
    generated_at: datetime
