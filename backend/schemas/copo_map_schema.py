"""
NBA Enterprise AI Platform — CO-PO Mapping Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.copo_map import MappingMethod, CorrelationLevel
from utils.validators import validate_correlation_value


class COPOMapBase(BaseModel):
    co_id: uuid.UUID
    po_id: uuid.UUID
    program_id: uuid.UUID
    correlation_value: int = Field(default=0, ge=0, le=3)
    mapping_method: MappingMethod = MappingMethod.MANUAL
    justification: Optional[str] = None
    academic_year: Optional[str] = Field(None, max_length=10)

    @field_validator("correlation_value")
    @classmethod
    def validate_correlation(cls, v: int) -> int:
        is_valid, msg = validate_correlation_value(float(v))
        if not is_valid:
            raise ValueError(msg)
        return v


class COPOMapCreate(COPOMapBase):
    pass


class COPOMapUpdate(BaseModel):
    correlation_value: Optional[int] = Field(None, ge=0, le=3)
    mapping_method: Optional[MappingMethod] = None
    justification: Optional[str] = None

    @field_validator("correlation_value")
    @classmethod
    def validate_correlation(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            is_valid, msg = validate_correlation_value(float(v))
            if not is_valid:
                raise ValueError(msg)
        return v


class COPOMapApprove(BaseModel):
    approved_by: uuid.UUID
    approved: bool = True
    justification: Optional[str] = None


class COPOMapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    co_id: uuid.UUID
    po_id: uuid.UUID
    program_id: uuid.UUID
    correlation_value: int
    correlation_label: str
    mapping_method: MappingMethod
    justification: Optional[str]
    ai_confidence_score: Optional[float]
    ai_reasoning: Optional[str]
    is_approved: bool
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    version: int
    academic_year: Optional[str]
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------
# Matrix views
# ----------------------------------------------------------------

class COPOMatrixCell(BaseModel):
    co_code: str
    po_code: str
    correlation_value: int
    correlation_label: str
    is_approved: bool
    mapping_id: Optional[uuid.UUID]


class COPOMatrix(BaseModel):
    """Full CO-PO matrix for a course or program."""
    program_id: uuid.UUID
    academic_year: Optional[str]
    co_codes: List[str]
    po_codes: List[str]
    matrix: Dict[str, Dict[str, int]]
    """matrix[co_code][po_code] = correlation_value"""
    approval_status: Dict[str, Dict[str, bool]]
    """approval_status[co_code][po_code] = is_approved"""


class COPOMatrixImport(BaseModel):
    """Import a full CO-PO matrix from a dict structure."""
    program_id: uuid.UUID
    academic_year: Optional[str] = None
    mapping_method: MappingMethod = MappingMethod.IMPORTED
    matrix: Dict[str, Dict[str, int]]
    """Expected: {co_code: {po_code: correlation_value}}"""
    overwrite_existing: bool = False

    @field_validator("matrix")
    @classmethod
    def validate_matrix_values(cls, v: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
        for co_code, po_map in v.items():
            for po_code, correlation in po_map.items():
                is_valid, msg = validate_correlation_value(float(correlation))
                if not is_valid:
                    raise ValueError(f"[{co_code}][{po_code}]: {msg}")
        return v


class AIMapping­Suggestion(BaseModel):
    """AI-generated CO-PO mapping suggestion."""
    co_id: uuid.UUID
    co_code: str
    co_statement: str
    po_id: uuid.UUID
    po_code: str
    po_description: str
    suggested_correlation: int
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
