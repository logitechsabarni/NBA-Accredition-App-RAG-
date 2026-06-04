"""
NBA Enterprise AI Platform — Program Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.program import ProgramLevel, ProgramStatus


class ProgramBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=30)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    department_id: uuid.UUID
    level: ProgramLevel = ProgramLevel.UNDERGRADUATE
    duration_years: int = Field(default=4, ge=1, le=10)
    total_semesters: int = Field(default=8, ge=1, le=20)
    credits_required: Optional[int] = Field(None, ge=0)
    nba_tier: Optional[int] = Field(None, ge=1, le=2)
    current_accreditation_cycle: Optional[str] = Field(None, max_length=20)
    accreditation_start_date: Optional[datetime] = None
    accreditation_end_date: Optional[datetime] = None
    co_attainment_target: float = Field(default=60.0, ge=0.0, le=100.0)
    po_attainment_target: float = Field(default=60.0, ge=0.0, le=100.0)
    direct_attainment_weight: float = Field(default=80.0, ge=0.0, le=100.0)
    indirect_attainment_weight: float = Field(default=20.0, ge=0.0, le=100.0)
    intake_year: Optional[int] = None
    regulation_year: Optional[int] = None
    program_educational_objectives: Optional[str] = None
    vision: Optional[str] = None
    mission: Optional[str] = None

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("indirect_attainment_weight")
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        direct = info.data.get("direct_attainment_weight", 80.0)
        if abs((direct + v) - 100.0) > 0.01:
            raise ValueError(
                f"direct_attainment_weight + indirect_attainment_weight must equal 100. "
                f"Got {direct} + {v} = {direct + v}"
            )
        return v


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    status: Optional[ProgramStatus] = None
    nba_tier: Optional[int] = Field(None, ge=1, le=2)
    current_accreditation_cycle: Optional[str] = Field(None, max_length=20)
    accreditation_start_date: Optional[datetime] = None
    accreditation_end_date: Optional[datetime] = None
    co_attainment_target: Optional[float] = Field(None, ge=0.0, le=100.0)
    po_attainment_target: Optional[float] = Field(None, ge=0.0, le=100.0)
    direct_attainment_weight: Optional[float] = Field(None, ge=0.0, le=100.0)
    indirect_attainment_weight: Optional[float] = Field(None, ge=0.0, le=100.0)
    vision: Optional[str] = None
    mission: Optional[str] = None
    program_educational_objectives: Optional[str] = None
    is_active: Optional[bool] = None


class ProgramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    short_name: Optional[str]
    description: Optional[str]
    department_id: uuid.UUID
    level: ProgramLevel
    duration_years: int
    total_semesters: int
    credits_required: Optional[int]
    status: ProgramStatus
    nba_tier: Optional[int]
    current_accreditation_cycle: Optional[str]
    accreditation_start_date: Optional[datetime]
    accreditation_end_date: Optional[datetime]
    last_sar_submitted_at: Optional[datetime]
    co_attainment_target: float
    po_attainment_target: float
    direct_attainment_weight: float
    indirect_attainment_weight: float
    intake_year: Optional[int]
    regulation_year: Optional[int]
    program_educational_objectives: Optional[str]
    vision: Optional[str]
    mission: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProgramSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    level: ProgramLevel
    status: ProgramStatus
    department_id: uuid.UUID
