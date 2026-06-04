"""
NBA Enterprise AI Platform — Schemas Package
Centralised re-export of all Pydantic v2 schemas.
Import from here in API routes for clean import paths.
"""

# ----------------------------------------------------------------
# User schemas
# ----------------------------------------------------------------
from schemas.user_schema import (
    UserBase,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserAdminUpdate,
    UserPasswordChange,
    UserOut,
    UserSummary,
    UserProfile,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
)

# ----------------------------------------------------------------
# Department schemas
# ----------------------------------------------------------------
from schemas.department_schema import (
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentOut,
    DepartmentSummary,
)

# ----------------------------------------------------------------
# Program schemas
# ----------------------------------------------------------------
from schemas.program_schema import (
    ProgramBase,
    ProgramCreate,
    ProgramUpdate,
    ProgramOut,
    ProgramSummary,
)

# ----------------------------------------------------------------
# Course schemas
# ----------------------------------------------------------------
from schemas.course_schema import (
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseOut,
    CourseSummary,
)

# ----------------------------------------------------------------
# CO / PO schemas
# ----------------------------------------------------------------
from schemas.co_po_schema import (
    COBase,
    COCreate,
    COUpdate,
    COOut,
    COSummary,
    POBase,
    POCreate,
    POUpdate,
    POOut,
    POSummary,
    COBulkCreate,
    POBulkCreate,
)

# ----------------------------------------------------------------
# CO-PO Mapping schemas
# ----------------------------------------------------------------
from schemas.copo_map_schema import (
    COPOMapBase,
    COPOMapCreate,
    COPOMapUpdate,
    COPOMapApprove,
    COPOMapOut,
    COPOMatrixCell,
    COPOMatrix,
    COPOMatrixImport,
)

# ----------------------------------------------------------------
# Attainment schemas
# ----------------------------------------------------------------
from schemas.attainment_schema import (
    StudentMarksEntry,
    COAssessmentData,
    AttainmentComputeRequest,
    POAttainmentComputeRequest,
    AttainmentRecordBase,
    AttainmentRecordOut,
    AttainmentSummary,
    COAttainmentSummaryRow,
    CourseAttainmentReport,
    POAttainmentRow,
    ProgramAttainmentReport,
    AttainmentVerifyRequest,
    AttainmentApproveRequest,
)

# ----------------------------------------------------------------
# SAR schemas
# ----------------------------------------------------------------
from schemas.sar_schema import (
    SARBase,
    SARCreate,
    SARUpdate,
    SARSectionUpdate,
    SARGenerateRequest,
    SARApprovalRequest,
    SARSubmitRequest,
    SAROut,
    SARSummary,
    SARGapAnalysisItem,
    SARGapAnalysis,
)

# ----------------------------------------------------------------
# Workflow schemas
# ----------------------------------------------------------------
from schemas.workflow_schema import (
    WorkflowType,
    WorkflowStatus,
    WorkflowPriority,
    AgentName,
    WorkflowSessionCreate,
    WorkflowSessionOut,
    AgentStepOut,
    WorkflowTraceOut,
    COPOMappingWorkflowRequest,
    COPOMappingWorkflowResult,
    AttainmentWorkflowRequest,
    AttainmentWorkflowResult,
    SARGenerationWorkflowRequest,
    SARGenerationWorkflowResult,
    CIAnalysisWorkflowRequest,
    CIActionItem,
    CIAnalysisWorkflowResult,
    GapAnalysisWorkflowRequest,
    GapItem,
    GapAnalysisWorkflowResult,
    ReadinessScoringRequest,
    CriterionScore,
    ReadinessScoringResult,
    WorkflowResponse,
    WorkflowListItem,
    WorkflowCancelRequest,
    WorkflowRetryRequest,
)

# ----------------------------------------------------------------
# Analytics schemas
# ----------------------------------------------------------------
from schemas.analytics_schema import (
    AnalyticsPeriod,
    TrendDirection,
    AlertSeverity,
    AnalyticsRequest,
    DashboardRequest,
    TrendAnalysisRequest,
    BenchmarkRequest,
    TimeSeriesPoint,
    TimeSeriesData,
    BenchmarkComparison,
    COAttainmentAnalyticsRow,
    CourseAttainmentAnalytics,
    POAttainmentAnalyticsRow,
    ProgramPOAnalytics,
    SARCriterionAnalytics,
    SARAnalytics,
    CIMetricRow,
    CIAnalyticsSummary,
    AlertItem,
    KPICard,
    ProgramDashboard,
    TrendAnalysisResponse,
    BenchmarkReport,
    AIInsightItem,
    AIInsightsResponse,
    AnalyticsExportRequest,
    AnalyticsExportResponse,
    InstitutionAnalyticsSummary,
)

__all__ = [
    # User
    "UserBase", "UserCreate", "UserRegister", "UserUpdate", "UserAdminUpdate",
    "UserPasswordChange", "UserOut", "UserSummary", "UserProfile",
    "LoginRequest", "TokenResponse", "RefreshTokenRequest",
    # Department
    "DepartmentBase", "DepartmentCreate", "DepartmentUpdate",
    "DepartmentOut", "DepartmentSummary",
    # Program
    "ProgramBase", "ProgramCreate", "ProgramUpdate", "ProgramOut", "ProgramSummary",
    # Course
    "CourseBase", "CourseCreate", "CourseUpdate", "CourseOut", "CourseSummary",
    # CO/PO
    "COBase", "COCreate", "COUpdate", "COOut", "COSummary",
    "POBase", "POCreate", "POUpdate", "POOut", "POSummary",
    "COBulkCreate", "POBulkCreate",
    # CO-PO Map
    "COPOMapBase", "COPOMapCreate", "COPOMapUpdate", "COPOMapApprove",
    "COPOMapOut", "COPOMatrixCell", "COPOMatrix", "COPOMatrixImport",
    # Attainment
    "StudentMarksEntry", "COAssessmentData", "AttainmentComputeRequest",
    "POAttainmentComputeRequest", "AttainmentRecordBase", "AttainmentRecordOut",
    "AttainmentSummary", "COAttainmentSummaryRow", "CourseAttainmentReport",
    "POAttainmentRow", "ProgramAttainmentReport",
    "AttainmentVerifyRequest", "AttainmentApproveRequest",
    # SAR
    "SARBase", "SARCreate", "SARUpdate", "SARSectionUpdate",
    "SARGenerateRequest", "SARApprovalRequest", "SARSubmitRequest",
    "SAROut", "SARSummary", "SARGapAnalysisItem", "SARGapAnalysis",
    # Workflow
    "WorkflowType", "WorkflowStatus", "WorkflowPriority", "AgentName",
    "WorkflowSessionCreate", "WorkflowSessionOut",
    "AgentStepOut", "WorkflowTraceOut",
    "COPOMappingWorkflowRequest", "COPOMappingWorkflowResult",
    "AttainmentWorkflowRequest", "AttainmentWorkflowResult",
    "SARGenerationWorkflowRequest", "SARGenerationWorkflowResult",
    "CIAnalysisWorkflowRequest", "CIActionItem", "CIAnalysisWorkflowResult",
    "GapAnalysisWorkflowRequest", "GapItem", "GapAnalysisWorkflowResult",
    "ReadinessScoringRequest", "CriterionScore", "ReadinessScoringResult",
    "WorkflowResponse", "WorkflowListItem",
    "WorkflowCancelRequest", "WorkflowRetryRequest",
    # Analytics
    "AnalyticsPeriod", "TrendDirection", "AlertSeverity",
    "AnalyticsRequest", "DashboardRequest", "TrendAnalysisRequest", "BenchmarkRequest",
    "TimeSeriesPoint", "TimeSeriesData", "BenchmarkComparison",
    "COAttainmentAnalyticsRow", "CourseAttainmentAnalytics",
    "POAttainmentAnalyticsRow", "ProgramPOAnalytics",
    "SARCriterionAnalytics", "SARAnalytics",
    "CIMetricRow", "CIAnalyticsSummary",
    "AlertItem", "KPICard", "ProgramDashboard",
    "TrendAnalysisResponse", "BenchmarkReport",
    "AIInsightItem", "AIInsightsResponse",
    "AnalyticsExportRequest", "AnalyticsExportResponse",
    "InstitutionAnalyticsSummary",
]
