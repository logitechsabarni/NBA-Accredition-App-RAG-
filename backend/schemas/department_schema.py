"""
NBA Enterprise AI Platform — Department Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=20)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    institution_id: uuid.UUID
    institution_name: str = Field(..., max_length=255)
    hod_name: Optional[str] = Field(None, max_length=255)
    hod_email: Optional[str] = None
    hod_user_id: Optional[uuid.UUID] = None
    nba_accredited: bool = False
    nba_accreditation_year: Optional[int] = None
    nba_valid_until: Optional[datetime] = None
    naac_grade: Optional[str] = Field(None, max_length=5)
    established_year: Optional[int] = None
    intake_capacity: Optional[int] = None
    office_phone: Optional[str] = Field(None, max_length=20)
    office_email: Optional[str] = None

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.strip().upper()


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    hod_name: Optional[str] = Field(None, max_length=255)
    hod_email: Optional[str] = None
    hod_user_id: Optional[uuid.UUID] = None
    nba_accredited: Optional[bool] = None
    nba_accreditation_year: Optional[int] = None
    nba_valid_until: Optional[datetime] = None
    naac_grade: Optional[str] = Field(None, max_length=5)
    intake_capacity: Optional[int] = None
    office_phone: Optional[str] = Field(None, max_length=20)
    office_email: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    short_name: Optional[str]
    description: Optional[str]
    institution_id: uuid.UUID
    institution_name: str
    hod_name: Optional[str]
    hod_email: Optional[str]
    hod_user_id: Optional[uuid.UUID]
    nba_accredited: bool
    nba_accreditation_year: Optional[int]
    nba_valid_until: Optional[datetime]
    naac_grade: Optional[str]
    established_year: Optional[int]
    intake_capacity: Optional[int]
    is_active: bool
    office_phone: Optional[str]
    office_email: Optional[str]
    created_at: datetime
    updated_at: datetime


class DepartmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    institution_name: str
    nba_accredited: bool
