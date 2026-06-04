"""
NBA Enterprise AI Platform — Workflow Pydantic Schemas
Covers all agentic workflow request/response contracts for
CO-PO mapping, attainment computation, SAR generation,
CI tracking, gap analysis, and readiness scoring workflows.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ----------------------------------------------------------------
# Workflow Enumerations
# ----------------------------------------------------------------

class WorkflowType(str, PyEnum):
    COPO_MAPPING = "copo_mapping"
    ATTAINMENT_COMPUTATION = "attainment_computation"
    SAR_GENERATION = "sar_generation"
    CI_ANALYSIS = "ci_analysis"
    GAP_ANALYSIS = "gap_analysis"
    READINESS_SCORING = "readiness_scoring"
    VALIDATION = "validation"
    ANALYTICS = "analytics"
    BULK_IMPORT = "bulk_import"


class WorkflowStatus(str, PyEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class WorkflowPriority(str, PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentName(str, PyEnum):
    COPO_AGENT = "copo_agent"
    ATTAINMENT_AGENT = "attainment_agent"
    SAR_AGENT = "sar_agent"
    CI_AGENT = "ci_agent"
    ANALYTICS_AGENT = "analytics_agent"
    VALIDATION_AGENT = "validation_agent"


# ----------------------------------------------------------------
# Workflow Session
# ----------------------------------------------------------------

class WorkflowSessionCreate(BaseModel):
    workflow_type: WorkflowType
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    initiated_by: uuid.UUID
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=128)


class WorkflowSessionOut(BaseModel):
    session_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    program_id: uuid.UUID
    academic_year: str
    initiated_by: uuid.UUID
    priority: WorkflowPriority
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    progress_percent: Optional[float]
    current_step: Optional[str]
    total_steps: Optional[int]
    completed_steps: Optional[int]
    result_summary: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_code: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


# ----------------------------------------------------------------
# Agent Step / Trace
# ----------------------------------------------------------------

class AgentStepOut(BaseModel):
    step_id: str
    step_name: str
    agent_name: AgentName
    status: WorkflowStatus
    input_summary: Optional[str]
    output_summary: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[float]
    tokens_used: Optional[int]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]


class WorkflowTraceOut(BaseModel):
    session_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    steps: List[AgentStepOut]
    total_tokens_used: Optional[int]
    total_duration_seconds: Optional[float]
    created_at: datetime


# ----------------------------------------------------------------
# CO-PO Mapping Workflow
# ----------------------------------------------------------------

class COPOMappingWorkflowRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    course_ids: Optional[List[uuid.UUID]] = Field(
        None,
        description="Specific courses to map. Null = all courses in program.",
    )
    use_ai_suggestion: bool = True
    ai_model: Optional[str] = Field(None, description="openai, granite, or auto")
    auto_approve_threshold: Optional[float] = Field(
        None,
        ge=0.8,
        le=1.0,
        description="Auto-approve mappings with AI confidence >= threshold",
    )
    overwrite_existing: bool = False
    notify_faculty: bool = False
    priority: WorkflowPriority = WorkflowPriority.NORMAL


class COPOMappingWorkflowResult(BaseModel):
    session_id: str
    program_id: uuid.UUID
    courses_processed: int
    cos_mapped: int
    pos_covered: int
    mappings_created: int
    mappings_updated: int
    mappings_auto_approved: int
    mappings_pending_approval: int
    average_ai_confidence: Optional[float]
    warnings: List[str]
    errors: List[str]
    completed_at: datetime


# ----------------------------------------------------------------
# Attainment Computation Workflow
# ----------------------------------------------------------------

class AttainmentWorkflowRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    batch_year: Optional[int] = None
    compute_co: bool = True
    compute_po: bool = True
    course_ids: Optional[List[uuid.UUID]] = None
    direct_weight: float = Field(default=0.8, ge=0.0, le=1.0)
    indirect_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    threshold_percent: float = Field(default=40.0, ge=0.0, le=100.0)
    overwrite_existing: bool = False
    auto_approve: bool = False
    generate_report: bool = True
    priority: WorkflowPriority = WorkflowPriority.NORMAL

    @field_validator("indirect_weight")
    @classmethod
    def weights_sum_to_one(cls, v: float, info) -> float:
        dw = info.data.get("direct_weight", 0.8)
        if abs((dw + v) - 1.0) > 0.001:
            raise ValueError(f"direct_weight + indirect_weight must equal 1.0. Got {dw + v:.4f}")
        return v


class AttainmentWorkflowResult(BaseModel):
    session_id: str
    program_id: uuid.UUID
    academic_year: str
    courses_processed: int
    co_records_computed: int
    po_records_computed: int
    cos_attained: int
    cos_not_attained: int
    pos_attained: int
    pos_not_attained: int
    overall_co_attainment_avg: Optional[float]
    overall_po_attainment_avg: Optional[float]
    report_available: bool
    warnings: List[str]
    errors: List[str]
    completed_at: datetime


# ----------------------------------------------------------------
# SAR Generation Workflow
# ----------------------------------------------------------------

class SARGenerationWorkflowRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    sar_id: Optional[uuid.UUID] = Field(
        None,
        description="Existing SAR to update. Null = create new SAR.",
    )
    sar_version: str = Field(default="tier_2", pattern="^(tier_1|tier_2)$")
    sections_to_generate: Optional[List[int]] = Field(
        None,
        description="Section numbers 1-8. Null = all.",
    )
    ai_model: Optional[str] = Field(None, description="openai, granite, or auto")
    include_attainment_data: bool = True
    include_ci_recommendations: bool = True
    include_gap_analysis: bool = True
    additional_context: Optional[str] = None
    priority: WorkflowPriority = WorkflowPriority.HIGH

    @field_validator("sections_to_generate")
    @classmethod
    def validate_section_numbers(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            invalid = [s for s in v if s < 1 or s > 8]
            if invalid:
                raise ValueError(f"Invalid section numbers (must be 1-8): {invalid}")
            return sorted(set(v))
        return v


class SARGenerationWorkflowResult(BaseModel):
    session_id: str
    sar_id: uuid.UUID
    program_id: uuid.UUID
    academic_year: str
    sections_generated: List[int]
    sections_failed: List[int]
    tokens_used: int
    model_used: str
    readiness_score: Optional[float]
    gap_analysis_complete: bool
    pdf_generated: bool
    pdf_path: Optional[str]
    warnings: List[str]
    errors: List[str]
    completed_at: datetime


# ----------------------------------------------------------------
# CI Analysis Workflow
# ----------------------------------------------------------------

class CIAnalysisWorkflowRequest(BaseModel):
    program_id: uuid.UUID
    current_academic_year: str = Field(..., max_length=10)
    comparison_academic_year: Optional[str] = Field(None, max_length=10)
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Specific areas to focus CI on: co_attainment, po_attainment, sar_criteria",
    )
    generate_action_plan: bool = True
    ai_recommendations: bool = True
    priority: WorkflowPriority = WorkflowPriority.NORMAL


class CIActionItem(BaseModel):
    area: str
    issue: str
    recommended_action: str
    priority: str  # high, medium, low
    responsible_role: str
    target_completion: Optional[str]
    expected_impact: str
    effort_level: str  # low, medium, high


class CIAnalysisWorkflowResult(BaseModel):
    session_id: str
    program_id: uuid.UUID
    current_year: str
    comparison_year: Optional[str]
    co_improvement_summary: Dict[str, Any]
    po_improvement_summary: Dict[str, Any]
    areas_improved: List[str]
    areas_declined: List[str]
    areas_unchanged: List[str]
    action_items: List[CIActionItem]
    overall_trend: str  # improving, stable, declining
    ci_score: Optional[float]
    warnings: List[str]
    completed_at: datetime


# ----------------------------------------------------------------
# Gap Analysis Workflow
# ----------------------------------------------------------------

class GapAnalysisWorkflowRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    sar_id: Optional[uuid.UUID] = None
    include_co_gaps: bool = True
    include_po_gaps: bool = True
    include_sar_criterion_gaps: bool = True
    generate_recommendations: bool = True
    priority: WorkflowPriority = WorkflowPriority.NORMAL


class GapItem(BaseModel):
    category: str
    code: str
    description: str
    current_value: Optional[float]
    target_value: float
    gap_value: float
    gap_percent: float
    severity: str  # critical, high, medium, low
    recommendations: List[str]


class GapAnalysisWorkflowResult(BaseModel):
    session_id: str
    program_id: uuid.UUID
    academic_year: str
    total_gaps: int
    critical_gaps: int
    high_gaps: int
    medium_gaps: int
    low_gaps: int
    co_gaps: List[GapItem]
    po_gaps: List[GapItem]
    sar_gaps: List[GapItem]
    readiness_score: Optional[float]
    readiness_grade: str  # A, B, C, D, F
    top_priority_actions: List[str]
    completed_at: datetime


# ----------------------------------------------------------------
# Readiness Scoring Workflow
# ----------------------------------------------------------------

class ReadinessScoringRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    sar_id: Optional[uuid.UUID] = None
    detailed_breakdown: bool = True
    compare_with_previous: bool = True
    priority: WorkflowPriority = WorkflowPriority.NORMAL


class CriterionScore(BaseModel):
    criterion_number: int
    criterion_name: str
    max_marks: float
    obtained_marks: Optional[float]
    score_percent: Optional[float]
    status: str  # strong, adequate, weak, missing
    sub_scores: Optional[Dict[str, float]]


class ReadinessScoringResult(BaseModel):
    session_id: str
    program_id: uuid.UUID
    academic_year: str
    overall_score: float
    overall_score_percent: float
    readiness_grade: str
    is_accreditation_ready: bool
    criteria_scores: List[CriterionScore]
    strong_areas: List[str]
    weak_areas: List[str]
    critical_missing: List[str]
    previous_score: Optional[float]
    score_trend: Optional[str]
    estimated_preparation_time_weeks: Optional[int]
    completed_at: datetime


# ----------------------------------------------------------------
# Generic Workflow Response
# ----------------------------------------------------------------

class WorkflowResponse(BaseModel):
    session_id: str
    status: WorkflowStatus
    message: str
    workflow_type: WorkflowType
    estimated_duration_seconds: Optional[int]
    result: Optional[
        Union[
            COPOMappingWorkflowResult,
            AttainmentWorkflowResult,
            SARGenerationWorkflowResult,
            CIAnalysisWorkflowResult,
            GapAnalysisWorkflowResult,
            ReadinessScoringResult,
            Dict[str, Any],
        ]
    ] = None


class WorkflowListItem(BaseModel):
    session_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    program_id: uuid.UUID
    academic_year: str
    priority: WorkflowPriority
    progress_percent: Optional[float]
    current_step: Optional[str]
    initiated_by: uuid.UUID
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class WorkflowCancelRequest(BaseModel):
    session_id: str
    reason: Optional[str] = None
    cancelled_by: uuid.UUID


class WorkflowRetryRequest(BaseModel):
    session_id: str
    retried_by: uuid.UUID
    override_parameters: Optional[Dict[str, Any]] = None
