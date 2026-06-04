"""
NBA Enterprise AI Platform — CO and PO Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.co import BloomsTaxonomyLevel, COStatus
from models.po import POType, POStatus
from utils.validators import validate_co_code, validate_po_code


# ====================================================================
# COURSE OUTCOME (CO) SCHEMAS
# ====================================================================

class COBase(BaseModel):
    code: str = Field(..., max_length=20)
    statement: str = Field(..., min_length=10)
    short_description: Optional[str] = Field(None, max_length=255)
    course_id: uuid.UUID
    sequence_number: int = Field(default=1, ge=1)
    blooms_level: Optional[BloomsTaxonomyLevel] = None
    attainment_target_percent: float = Field(default=60.0, ge=0.0, le=100.0)
    assessment_weightage: Optional[Dict[str, float]] = None
    cia1_mapping: Optional[Dict[str, Any]] = None
    cia2_mapping: Optional[Dict[str, Any]] = None
    ese_mapping: Optional[Dict[str, Any]] = None

    @field_validator("code")
    @classmethod
    def validate_co_code_format(cls, v: str) -> str:
        v = v.strip().upper()
        is_valid, msg = validate_co_code(v)
        if not is_valid:
            raise ValueError(msg)
        return v

    @field_validator("assessment_weightage")
    @classmethod
    def validate_assessment_weightage(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(
                    f"assessment_weightage values must sum to 1.0. Got {total:.4f}"
                )
        return v


class COCreate(COBase):
    pass


class COUpdate(BaseModel):
    statement: Optional[str] = Field(None, min_length=10)
    short_description: Optional[str] = Field(None, max_length=255)
    sequence_number: Optional[int] = Field(None, ge=1)
    blooms_level: Optional[BloomsTaxonomyLevel] = None
    status: Optional[COStatus] = None
    attainment_target_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    assessment_weightage: Optional[Dict[str, float]] = None
    cia1_mapping: Optional[Dict[str, Any]] = None
    cia2_mapping: Optional[Dict[str, Any]] = None
    ese_mapping: Optional[Dict[str, Any]] = None


class COOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    statement: str
    short_description: Optional[str]
    course_id: uuid.UUID
    sequence_number: int
    blooms_level: Optional[BloomsTaxonomyLevel]
    status: COStatus
    attainment_target_percent: float
    assessment_weightage: Optional[Dict[str, float]]
    cia_attainment_percent: Optional[float]
    ese_attainment_percent: Optional[float]
    direct_attainment_percent: Optional[float]
    indirect_attainment_percent: Optional[float]
    final_attainment_percent: Optional[float]
    is_attained: Optional[bool]
    ai_suggested: bool
    ai_confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime


class COSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    statement: str
    course_id: uuid.UUID
    blooms_level: Optional[BloomsTaxonomyLevel]
    final_attainment_percent: Optional[float]
    is_attained: Optional[bool]


# ====================================================================
# PROGRAM OUTCOME (PO) SCHEMAS
# ====================================================================

class POBase(BaseModel):
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=255)
    description: str = Field(..., min_length=10)
    short_description: Optional[str] = Field(None, max_length=255)
    program_id: uuid.UUID
    po_type: POType = POType.PO
    sequence_number: int = Field(..., ge=1)
    is_nba_standard: bool = True
    attainment_target_percent: float = Field(default=60.0, ge=0.0, le=100.0)

    @field_validator("code")
    @classmethod
    def validate_po_code_format(cls, v: str) -> str:
        v = v.strip().upper()
        is_valid, msg = validate_po_code(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class POCreate(POBase):
    pass


class POUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    short_description: Optional[str] = Field(None, max_length=255)
    status: Optional[POStatus] = None
    attainment_target_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    is_active: Optional[bool] = None


class POOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str
    short_description: Optional[str]
    program_id: uuid.UUID
    po_type: POType
    sequence_number: int
    status: POStatus
    is_nba_standard: bool
    attainment_percent: Optional[float]
    attainment_target_percent: float
    is_attained: Optional[bool]
    gap_percent: Optional[float]
    previous_attainment_percent: Optional[float]
    improvement_percent: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class POSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    po_type: POType
    attainment_percent: Optional[float]
    is_attained: Optional[bool]
    gap_percent: Optional[float]


# ====================================================================
# Bulk operations
# ====================================================================

class COBulkCreate(BaseModel):
    """Create multiple COs for a course in one request."""
    course_id: uuid.UUID
    cos: list[COBase]

    @field_validator("cos")
    @classmethod
    def validate_unique_codes(cls, v: list) -> list:
        codes = [co.code for co in v]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate CO codes in bulk create request")
        return v


class POBulkCreate(BaseModel):
    """Seed standard NBA POs for a program."""
    program_id: uuid.UUID
    use_nba_standard: bool = True
    pos: Optional[list[POBase]] = None
