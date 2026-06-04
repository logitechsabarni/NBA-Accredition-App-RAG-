"""
NBA Enterprise AI Platform — Analytics Pydantic Schemas
Covers dashboards, trend analysis, benchmark comparisons,
accreditation readiness, and AI-powered insights.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------------------
# Enumerations
# ----------------------------------------------------------------

class AnalyticsPeriod(str, PyEnum):
    LAST_SEMESTER = "last_semester"
    CURRENT_YEAR = "current_year"
    LAST_2_YEARS = "last_2_years"
    LAST_3_YEARS = "last_3_years"
    LAST_5_YEARS = "last_5_years"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


class TrendDirection(str, PyEnum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class AlertSeverity(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ----------------------------------------------------------------
# Request Schemas
# ----------------------------------------------------------------

class AnalyticsRequest(BaseModel):
    program_id: uuid.UUID
    period: AnalyticsPeriod = AnalyticsPeriod.CURRENT_YEAR
    academic_years: Optional[List[str]] = None
    include_benchmarks: bool = False
    include_ai_insights: bool = True
    cache_ttl_seconds: int = Field(default=300, ge=0, le=86400)


class DashboardRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    include_co_details: bool = True
    include_po_details: bool = True
    include_sar_status: bool = True
    include_ci_summary: bool = True
    include_alerts: bool = True
    include_ai_insights: bool = True


class TrendAnalysisRequest(BaseModel):
    program_id: uuid.UUID
    metric: str = Field(
        ...,
        description="co_attainment, po_attainment, sar_score, readiness_score",
    )
    academic_years: List[str] = Field(..., min_length=2)
    co_codes: Optional[List[str]] = None
    po_codes: Optional[List[str]] = None
    include_forecast: bool = False
    forecast_periods: int = Field(default=1, ge=1, le=5)


class BenchmarkRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str = Field(..., max_length=10)
    benchmark_type: str = Field(
        default="institution",
        description="institution, national, nba_target",
    )
    metrics: List[str] = Field(
        default=["co_attainment", "po_attainment", "readiness_score"]
    )


# ----------------------------------------------------------------
# Data Point Models
# ----------------------------------------------------------------

class TimeSeriesPoint(BaseModel):
    period: str
    value: float
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TimeSeriesData(BaseModel):
    metric: str
    unit: str
    data_points: List[TimeSeriesPoint]
    trend_direction: TrendDirection
    trend_percent_change: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    average_value: Optional[float]


class BenchmarkComparison(BaseModel):
    metric: str
    program_value: Optional[float]
    benchmark_value: float
    benchmark_label: str
    variance: Optional[float]
    variance_percent: Optional[float]
    performance: str  # above, at, below


# ----------------------------------------------------------------
# CO Analytics
# ----------------------------------------------------------------

class COAttainmentAnalyticsRow(BaseModel):
    co_id: uuid.UUID
    co_code: str
    co_statement: str
    blooms_level: Optional[str]
    attainment_percent: Optional[float]
    target_percent: float
    is_attained: Optional[bool]
    gap_percent: Optional[float]
    trend: TrendDirection
    trend_data: Optional[List[TimeSeriesPoint]]


class CourseAttainmentAnalytics(BaseModel):
    course_id: uuid.UUID
    course_code: str
    course_name: str
    semester: int
    academic_year: str
    total_students: Optional[int]
    cos: List[COAttainmentAnalyticsRow]
    attained_cos_count: int
    total_cos_count: int
    attainment_rate_percent: float
    average_attainment_percent: Optional[float]


# ----------------------------------------------------------------
# PO Analytics
# ----------------------------------------------------------------

class POAttainmentAnalyticsRow(BaseModel):
    po_id: uuid.UUID
    po_code: str
    po_name: str
    po_type: str
    attainment_percent: Optional[float]
    target_percent: float
    is_attained: Optional[bool]
    gap_percent: Optional[float]
    contributing_cos: List[str]
    trend: TrendDirection
    trend_data: Optional[List[TimeSeriesPoint]]
    benchmark_comparison: Optional[BenchmarkComparison]


class ProgramPOAnalytics(BaseModel):
    program_id: uuid.UUID
    program_code: str
    program_name: str
    academic_year: str
    pos: List[POAttainmentAnalyticsRow]
    pos_attained_count: int
    pos_total_count: int
    pos_attainment_rate_percent: float
    pso_attainment_rate_percent: Optional[float]
    overall_po_attainment_avg: Optional[float]


# ----------------------------------------------------------------
# SAR Analytics
# ----------------------------------------------------------------

class SARCriterionAnalytics(BaseModel):
    criterion_number: int
    criterion_name: str
    max_marks: float
    obtained_marks: Optional[float]
    score_percent: Optional[float]
    trend: TrendDirection
    previous_score_percent: Optional[float]
    gap_to_target: Optional[float]


class SARAnalytics(BaseModel):
    sar_id: Optional[uuid.UUID]
    program_id: uuid.UUID
    academic_year: str
    overall_score: Optional[float]
    overall_score_percent: Optional[float]
    readiness_grade: Optional[str]
    is_ready: bool
    criteria: List[SARCriterionAnalytics]
    submission_status: Optional[str]
    last_updated: Optional[datetime]
    trend: TrendDirection
    previous_overall_score: Optional[float]


# ----------------------------------------------------------------
# CI Analytics
# ----------------------------------------------------------------

class CIMetricRow(BaseModel):
    metric_name: str
    current_value: Optional[float]
    previous_value: Optional[float]
    change_value: Optional[float]
    change_percent: Optional[float]
    trend: TrendDirection
    target: Optional[float]
    target_met: Optional[bool]


class CIAnalyticsSummary(BaseModel):
    program_id: uuid.UUID
    current_year: str
    comparison_year: Optional[str]
    co_ci_metrics: List[CIMetricRow]
    po_ci_metrics: List[CIMetricRow]
    sar_ci_metrics: List[CIMetricRow]
    overall_ci_score: Optional[float]
    ci_trend: TrendDirection
    action_items_pending: int
    action_items_completed: int
    action_items_overdue: int


# ----------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------

class AlertItem(BaseModel):
    alert_id: str
    severity: AlertSeverity
    category: str
    title: str
    message: str
    resource_type: str
    resource_id: Optional[uuid.UUID]
    resource_code: Optional[str]
    created_at: datetime
    action_url: Optional[str]
    dismissed: bool = False


class KPICard(BaseModel):
    kpi_id: str
    title: str
    value: Optional[float]
    unit: str
    target: Optional[float]
    target_met: Optional[bool]
    trend: TrendDirection
    trend_value: Optional[float]
    period: str
    color: str  # green, yellow, red, blue, gray
    icon: Optional[str]


class ProgramDashboard(BaseModel):
    program_id: uuid.UUID
    program_name: str
    program_code: str
    department_name: str
    academic_year: str
    generated_at: datetime

    # KPI Cards
    kpis: List[KPICard]

    # Summary metrics
    total_courses: int
    total_cos: int
    total_pos: int
    cos_attained: int
    cos_not_attained: int
    pos_attained: int
    pos_not_attained: int

    # Attainment summary
    avg_co_attainment: Optional[float]
    avg_po_attainment: Optional[float]
    co_attainment_rate_percent: float
    po_attainment_rate_percent: float

    # SAR
    sar_status: Optional[str]
    sar_readiness_score: Optional[float]
    sar_readiness_grade: Optional[str]

    # CI
    ci_score: Optional[float]
    ci_trend: TrendDirection

    # Alerts
    alerts: List[AlertItem]
    critical_alerts_count: int
    warning_alerts_count: int

    # AI Insights
    ai_insights: Optional[List[str]]
    ai_top_recommendation: Optional[str]


# ----------------------------------------------------------------
# Trend Analysis Response
# ----------------------------------------------------------------

class TrendAnalysisResponse(BaseModel):
    program_id: uuid.UUID
    metric: str
    period_label: str
    time_series: List[TimeSeriesData]
    trend_direction: TrendDirection
    trend_summary: str
    forecast: Optional[List[TimeSeriesPoint]]
    forecast_confidence: Optional[float]
    inflection_points: Optional[List[Dict[str, Any]]]
    generated_at: datetime


# ----------------------------------------------------------------
# Benchmarking Response
# ----------------------------------------------------------------

class BenchmarkReport(BaseModel):
    program_id: uuid.UUID
    academic_year: str
    benchmark_type: str
    comparisons: List[BenchmarkComparison]
    overall_performance: str  # above_average, average, below_average
    percentile_rank: Optional[float]
    strengths: List[str]
    improvement_areas: List[str]
    generated_at: datetime


# ----------------------------------------------------------------
# AI Insights
# ----------------------------------------------------------------

class AIInsightItem(BaseModel):
    insight_id: str
    category: str
    priority: str
    title: str
    description: str
    supporting_data: Optional[Dict[str, Any]]
    recommended_actions: List[str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    generated_by: str


class AIInsightsResponse(BaseModel):
    program_id: uuid.UUID
    academic_year: str
    insights: List[AIInsightItem]
    overall_health_score: Optional[float]
    risk_level: str  # low, medium, high, critical
    model_used: str
    tokens_used: Optional[int]
    generated_at: datetime


# ----------------------------------------------------------------
# Export
# ----------------------------------------------------------------

class AnalyticsExportRequest(BaseModel):
    program_id: uuid.UUID
    academic_year: str
    export_format: str = Field(
        default="xlsx",
        pattern="^(xlsx|csv|pdf|json)$",
    )
    include_sections: List[str] = Field(
        default=["co_attainment", "po_attainment", "sar_analytics", "ci_analytics"],
    )
    include_charts: bool = True


class AnalyticsExportResponse(BaseModel):
    file_path: str
    file_name: str
    export_format: str
    file_size_bytes: Optional[int]
    generated_at: datetime
    download_url: Optional[str]
    expires_at: Optional[datetime]


# ----------------------------------------------------------------
# System-level Analytics (Admin)
# ----------------------------------------------------------------

class InstitutionAnalyticsSummary(BaseModel):
    institution_id: uuid.UUID
    institution_name: str
    total_departments: int
    total_programs: int
    total_courses: int
    accredited_programs: int
    pending_programs: int
    avg_co_attainment: Optional[float]
    avg_po_attainment: Optional[float]
    avg_sar_readiness: Optional[float]
    active_workflows: int
    alerts_count: int
    generated_at: datetime
