"""
Analytics Agent – NBA Enterprise AI Platform
Handles readiness scoring, KPI generation, trend analytics,
department benchmarking, accreditation risk scoring, and
executive summary generation.
"""

from __future__ import annotations

import asyncio
import math
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.agents.base_agent import (
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class CourseAttainmentRecord(BaseModel):
    course_code: str
    course_name: str
    department: str
    academic_year: str
    semester: str
    co_attainments: dict[str, float] = Field(
        default_factory=dict, description="CO code -> attainment %"
    )
    po_attainments: dict[str, float] = Field(
        default_factory=dict, description="PO code -> attainment %"
    )
    direct_attainment: float = Field(ge=0.0, le=100.0)
    indirect_attainment: float = Field(ge=0.0, le=100.0)
    overall_attainment: float = Field(ge=0.0, le=100.0)
    enrolled_students: int = Field(ge=0)
    assessed_students: int = Field(ge=0)

    @field_validator("assessed_students")
    @classmethod
    def assessed_le_enrolled(cls, v: int, info: Any) -> int:
        enrolled = info.data.get("enrolled_students", 0)
        if v > enrolled:
            raise ValueError("assessed_students cannot exceed enrolled_students")
        return v


class DepartmentProfile(BaseModel):
    department_code: str
    department_name: str
    program_name: str
    accreditation_cycle: str
    courses: list[CourseAttainmentRecord] = Field(default_factory=list)
    target_attainment: float = Field(default=60.0, ge=0.0, le=100.0)
    historical_attainments: list[float] = Field(
        default_factory=list, description="Ordered list of past overall attainments"
    )


class AnalyticsRequest(BaseModel):
    departments: list[DepartmentProfile]
    reference_year: str = Field(
        description="Academic year being analysed, e.g. '2023-24'"
    )
    include_trend: bool = True
    include_benchmarking: bool = True
    include_risk_scoring: bool = True
    include_executive_summary: bool = True
    benchmark_percentile_target: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
        description="Percentile target for benchmarking comparisons",
    )

    @model_validator(mode="after")
    def departments_not_empty(self) -> "AnalyticsRequest":
        if not self.departments:
            raise ValueError("At least one department must be provided")
        return self


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class ReadinessScore(BaseModel):
    department_code: str
    score: float = Field(ge=0.0, le=100.0)
    grade: str
    attainment_score: float
    documentation_score: float
    trend_score: float
    coverage_score: float
    rationale: str


class KPI(BaseModel):
    name: str
    value: float
    unit: str
    benchmark: float | None = None
    status: str  # "on_track" | "at_risk" | "critical"
    trend: str  # "improving" | "stable" | "declining"
    description: str


class TrendPoint(BaseModel):
    period: str
    value: float
    delta: float | None = None


class TrendAnalysis(BaseModel):
    department_code: str
    metric: str
    data_points: list[TrendPoint]
    slope: float
    direction: str  # "improving" | "stable" | "declining"
    volatility: float
    forecast_next: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class DepartmentBenchmark(BaseModel):
    department_code: str
    department_name: str
    overall_attainment: float
    rank: int
    total_departments: int
    percentile: float
    above_target: bool
    gap_to_top: float
    gap_to_target: float


class AccreditationRisk(BaseModel):
    department_code: str
    risk_level: str  # "low" | "medium" | "high" | "critical"
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_factors: list[str]
    mitigating_factors: list[str]
    recommended_actions: list[str]
    estimated_readiness_gap_months: int


class ExecutiveSummary(BaseModel):
    generated_at: datetime
    reference_year: str
    total_departments: int
    overall_platform_readiness: float
    highlights: list[str]
    concerns: list[str]
    strategic_recommendations: list[str]
    departments_above_target: int
    departments_at_risk: int
    average_attainment: float
    best_performing_department: str
    most_improved_department: str | None


class AnalyticsResult(BaseModel):
    readiness_scores: list[ReadinessScore]
    kpis: list[KPI]
    trends: list[TrendAnalysis]
    benchmarks: list[DepartmentBenchmark]
    risks: list[AccreditationRisk]
    executive_summary: ExecutiveSummary | None


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------

_METADATA = AgentMetadata(
    name="AnalyticsAgent",
    version="1.0.0",
    description=(
        "Computes accreditation readiness scores, KPIs, trend analytics, "
        "department benchmarking, risk scoring, and executive summaries for "
        "NBA accreditation workflows."
    ),
    capabilities=[
        "readiness_scoring",
        "kpi_generation",
        "trend_analytics",
        "department_benchmarking",
        "risk_scoring",
        "executive_summary",
    ],
    max_retries=2,
    timeout_seconds=120,
)


class AnalyticsAgent(BaseAgent):
    """
    Produces comprehensive analytics for the NBA accreditation platform.

    All methods are async-safe and designed to integrate with LangGraph
    node pipelines as well as direct FastAPI endpoints.
    """

    def __init__(self) -> None:
        super().__init__(metadata=_METADATA)

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def execute(self, request: AgentRequest) -> AgentResponse:
        log = logger.bind(
            agent=self.metadata.name,
            request_id=str(request.request_id),
            correlation_id=str(request.correlation_id),
        )
        log.info("analytics_agent.execute.start")

        try:
            payload = self._parse_payload(request.payload, AnalyticsRequest)
            result = await self._run_analytics(payload, log)

            response = AgentResponse(
                request_id=request.request_id,
                agent_name=self.metadata.name,
                status=AgentStatus.SUCCESS,
                result=result.model_dump(mode="json"),
                metadata={"reference_year": payload.reference_year},
            )
            log.info(
                "analytics_agent.execute.complete",
                departments=len(payload.departments),
            )
            return response

        except Exception as exc:
            log.error("analytics_agent.execute.error", error=str(exc), exc_info=True)
            return self._error_response(request, exc)

    # ------------------------------------------------------------------
    # Core orchestration
    # ------------------------------------------------------------------

    async def _run_analytics(
        self, payload: AnalyticsRequest, log: Any
    ) -> AnalyticsResult:
        tasks: list[Any] = [
            self._compute_readiness_scores(payload),
            self._compute_kpis(payload),
        ]
        if payload.include_trend:
            tasks.append(self._compute_trends(payload))
        else:
            tasks.append(asyncio.sleep(0))  # placeholder

        if payload.include_benchmarking:
            tasks.append(self._compute_benchmarks(payload))
        else:
            tasks.append(asyncio.sleep(0))

        if payload.include_risk_scoring:
            tasks.append(self._compute_risks(payload))
        else:
            tasks.append(asyncio.sleep(0))

        results = await asyncio.gather(*tasks)
        readiness_scores: list[ReadinessScore] = results[0]
        kpis: list[KPI] = results[1]
        trends: list[TrendAnalysis] = results[2] if payload.include_trend else []
        benchmarks: list[DepartmentBenchmark] = (
            results[3] if payload.include_benchmarking else []
        )
        risks: list[AccreditationRisk] = (
            results[4] if payload.include_risk_scoring else []
        )

        executive_summary: ExecutiveSummary | None = None
        if payload.include_executive_summary:
            executive_summary = await self._generate_executive_summary(
                payload, readiness_scores, kpis, risks
            )

        return AnalyticsResult(
            readiness_scores=readiness_scores,
            kpis=kpis,
            trends=trends,
            benchmarks=benchmarks,
            risks=risks,
            executive_summary=executive_summary,
        )

    # ------------------------------------------------------------------
    # Readiness scoring
    # ------------------------------------------------------------------

    async def _compute_readiness_scores(
        self, payload: AnalyticsRequest
    ) -> list[ReadinessScore]:
        scores: list[ReadinessScore] = []
        for dept in payload.departments:
            score = await self._score_department(dept)
            scores.append(score)
        return scores

    async def _score_department(self, dept: DepartmentProfile) -> ReadinessScore:
        if not dept.courses:
            return ReadinessScore(
                department_code=dept.department_code,
                score=0.0,
                grade="F",
                attainment_score=0.0,
                documentation_score=0.0,
                trend_score=0.0,
                coverage_score=0.0,
                rationale="No course data available.",
            )

        # Attainment sub-score (0-40 pts)
        avg_attainment = statistics.mean(c.overall_attainment for c in dept.courses)
        attainment_score = min(40.0, (avg_attainment / 100.0) * 40.0)

        # Documentation sub-score (0-20 pts): proxy via CO/PO coverage
        docs_ratios = []
        for c in dept.courses:
            total_pos = max(len(c.po_attainments), 1)
            covered_pos = sum(1 for v in c.po_attainments.values() if v > 0)
            docs_ratios.append(covered_pos / total_pos)
        documentation_score = min(20.0, statistics.mean(docs_ratios) * 20.0)

        # Trend sub-score (0-20 pts)
        trend_score = 10.0  # neutral default
        if len(dept.historical_attainments) >= 2:
            deltas = [
                dept.historical_attainments[i] - dept.historical_attainments[i - 1]
                for i in range(1, len(dept.historical_attainments))
            ]
            avg_delta = statistics.mean(deltas)
            if avg_delta >= 2.0:
                trend_score = 20.0
            elif avg_delta >= 0.0:
                trend_score = 15.0
            elif avg_delta >= -2.0:
                trend_score = 8.0
            else:
                trend_score = 2.0

        # Coverage sub-score (0-20 pts): student assessment coverage
        coverage_ratios = []
        for c in dept.courses:
            if c.enrolled_students > 0:
                coverage_ratios.append(c.assessed_students / c.enrolled_students)
        coverage_score = (
            min(20.0, statistics.mean(coverage_ratios) * 20.0)
            if coverage_ratios
            else 0.0
        )

        total = attainment_score + documentation_score + trend_score + coverage_score
        grade = self._score_to_grade(total)

        rationale = (
            f"Avg attainment {avg_attainment:.1f}% contributed {attainment_score:.1f}/40 pts. "
            f"PO documentation coverage contributed {documentation_score:.1f}/20 pts. "
            f"Historical trend contributed {trend_score:.1f}/20 pts. "
            f"Student assessment coverage contributed {coverage_score:.1f}/20 pts."
        )

        return ReadinessScore(
            department_code=dept.department_code,
            score=round(total, 2),
            grade=grade,
            attainment_score=round(attainment_score, 2),
            documentation_score=round(documentation_score, 2),
            trend_score=round(trend_score, 2),
            coverage_score=round(coverage_score, 2),
            rationale=rationale,
        )

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    # ------------------------------------------------------------------
    # KPI generation
    # ------------------------------------------------------------------

    async def _compute_kpis(self, payload: AnalyticsRequest) -> list[KPI]:
        all_attainments = [
            c.overall_attainment
            for dept in payload.departments
            for c in dept.courses
        ]
        all_direct = [
            c.direct_attainment
            for dept in payload.departments
            for c in dept.courses
        ]
        all_indirect = [
            c.indirect_attainment
            for dept in payload.departments
            for c in dept.courses
        ]

        kpis: list[KPI] = []

        if all_attainments:
            avg_overall = statistics.mean(all_attainments)
            kpis.append(
                KPI(
                    name="Average Overall Attainment",
                    value=round(avg_overall, 2),
                    unit="%",
                    benchmark=60.0,
                    status=self._kpi_status(avg_overall, 60.0, 50.0),
                    trend=self._compute_global_trend(payload),
                    description="Mean overall attainment across all courses and departments.",
                )
            )

        if all_direct:
            avg_direct = statistics.mean(all_direct)
            kpis.append(
                KPI(
                    name="Average Direct Attainment",
                    value=round(avg_direct, 2),
                    unit="%",
                    benchmark=60.0,
                    status=self._kpi_status(avg_direct, 60.0, 50.0),
                    trend="stable",
                    description="Mean direct attainment (exam-based) across all courses.",
                )
            )

        if all_indirect:
            avg_indirect = statistics.mean(all_indirect)
            kpis.append(
                KPI(
                    name="Average Indirect Attainment",
                    value=round(avg_indirect, 2),
                    unit="%",
                    benchmark=60.0,
                    status=self._kpi_status(avg_indirect, 60.0, 50.0),
                    trend="stable",
                    description="Mean indirect attainment (survey-based) across all courses.",
                )
            )

        # Departments above target
        target = 60.0
        above_target = sum(
            1
            for dept in payload.departments
            if dept.courses
            and statistics.mean(c.overall_attainment for c in dept.courses) >= target
        )
        pct_above = (
            (above_target / len(payload.departments)) * 100
            if payload.departments
            else 0.0
        )
        kpis.append(
            KPI(
                name="Departments Above Target",
                value=round(pct_above, 1),
                unit="%",
                benchmark=80.0,
                status=self._kpi_status(pct_above, 80.0, 60.0),
                trend="stable",
                description=f"{above_target}/{len(payload.departments)} departments exceed the {target}% attainment target.",
            )
        )

        # Student coverage KPI
        total_enrolled = sum(
            c.enrolled_students
            for dept in payload.departments
            for c in dept.courses
        )
        total_assessed = sum(
            c.assessed_students
            for dept in payload.departments
            for c in dept.courses
        )
        coverage_pct = (
            (total_assessed / total_enrolled * 100) if total_enrolled > 0 else 0.0
        )
        kpis.append(
            KPI(
                name="Student Assessment Coverage",
                value=round(coverage_pct, 2),
                unit="%",
                benchmark=95.0,
                status=self._kpi_status(coverage_pct, 95.0, 80.0),
                trend="stable",
                description=f"{total_assessed}/{total_enrolled} enrolled students have assessment data.",
            )
        )

        # PO coverage KPI
        po_coverage_values = []
        for dept in payload.departments:
            for course in dept.courses:
                if course.po_attainments:
                    covered = sum(1 for v in course.po_attainments.values() if v > 0)
                    po_coverage_values.append(covered / len(course.po_attainments) * 100)
        if po_coverage_values:
            avg_po_coverage = statistics.mean(po_coverage_values)
            kpis.append(
                KPI(
                    name="Average PO Coverage",
                    value=round(avg_po_coverage, 2),
                    unit="%",
                    benchmark=90.0,
                    status=self._kpi_status(avg_po_coverage, 90.0, 70.0),
                    trend="stable",
                    description="Percentage of programme outcomes with active attainment data.",
                )
            )

        return kpis

    @staticmethod
    def _kpi_status(value: float, good_threshold: float, warn_threshold: float) -> str:
        if value >= good_threshold:
            return "on_track"
        if value >= warn_threshold:
            return "at_risk"
        return "critical"

    def _compute_global_trend(self, payload: AnalyticsRequest) -> str:
        all_histories = [
            dept.historical_attainments
            for dept in payload.departments
            if len(dept.historical_attainments) >= 2
        ]
        if not all_histories:
            return "stable"
        avg_deltas = []
        for hist in all_histories:
            deltas = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
            avg_deltas.append(statistics.mean(deltas))
        overall_delta = statistics.mean(avg_deltas)
        if overall_delta >= 1.0:
            return "improving"
        if overall_delta <= -1.0:
            return "declining"
        return "stable"

    # ------------------------------------------------------------------
    # Trend analytics
    # ------------------------------------------------------------------

    async def _compute_trends(
        self, payload: AnalyticsRequest
    ) -> list[TrendAnalysis]:
        trends: list[TrendAnalysis] = []
        for dept in payload.departments:
            if len(dept.historical_attainments) < 2:
                continue
            trend = self._analyse_series(
                department_code=dept.department_code,
                metric="overall_attainment",
                values=dept.historical_attainments,
            )
            trends.append(trend)
        return trends

    @staticmethod
    def _analyse_series(
        department_code: str, metric: str, values: list[float]
    ) -> TrendAnalysis:
        n = len(values)
        periods = [str(i + 1) for i in range(n)]

        data_points: list[TrendPoint] = []
        for idx, val in enumerate(values):
            delta = val - values[idx - 1] if idx > 0 else None
            data_points.append(TrendPoint(period=periods[idx], value=val, delta=delta))

        # Linear regression slope
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0.0

        # Volatility (std dev)
        volatility = statistics.stdev(values) if n >= 2 else 0.0

        # Direction
        if slope >= 0.5:
            direction = "improving"
        elif slope <= -0.5:
            direction = "declining"
        else:
            direction = "stable"

        # Simple linear forecast
        forecast_next = values[-1] + slope

        # Confidence based on R²
        ss_res = sum((v - (y_mean + slope * (i - x_mean))) ** 2 for i, v in enumerate(values))
        ss_tot = sum((v - y_mean) ** 2 for v in values)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        confidence = max(0.0, min(1.0, r_squared))

        return TrendAnalysis(
            department_code=department_code,
            metric=metric,
            data_points=data_points,
            slope=round(slope, 4),
            direction=direction,
            volatility=round(volatility, 4),
            forecast_next=round(forecast_next, 2),
            confidence=round(confidence, 4),
        )

    # ------------------------------------------------------------------
    # Benchmarking
    # ------------------------------------------------------------------

    async def _compute_benchmarks(
        self, payload: AnalyticsRequest
    ) -> list[DepartmentBenchmark]:
        dept_attainments: list[tuple[DepartmentProfile, float]] = []
        for dept in payload.departments:
            if dept.courses:
                avg = statistics.mean(c.overall_attainment for c in dept.courses)
            else:
                avg = 0.0
            dept_attainments.append((dept, avg))

        sorted_depts = sorted(dept_attainments, key=lambda x: x[1], reverse=True)
        total = len(sorted_depts)
        top_attainment = sorted_depts[0][1] if sorted_depts else 0.0

        benchmarks: list[DepartmentBenchmark] = []
        for rank, (dept, avg) in enumerate(sorted_depts, start=1):
            percentile = ((total - rank) / (total - 1) * 100) if total > 1 else 100.0
            benchmarks.append(
                DepartmentBenchmark(
                    department_code=dept.department_code,
                    department_name=dept.department_name,
                    overall_attainment=round(avg, 2),
                    rank=rank,
                    total_departments=total,
                    percentile=round(percentile, 1),
                    above_target=avg >= dept.target_attainment,
                    gap_to_top=round(top_attainment - avg, 2),
                    gap_to_target=round(max(0.0, dept.target_attainment - avg), 2),
                )
            )

        return benchmarks

    # ------------------------------------------------------------------
    # Risk scoring
    # ------------------------------------------------------------------

    async def _compute_risks(
        self, payload: AnalyticsRequest
    ) -> list[AccreditationRisk]:
        risks: list[AccreditationRisk] = []
        for dept in payload.departments:
            risk = await self._score_risk(dept)
            risks.append(risk)
        return risks

    async def _score_risk(self, dept: DepartmentProfile) -> AccreditationRisk:
        risk_factors: list[str] = []
        mitigating_factors: list[str] = []
        risk_score = 0.0

        if not dept.courses:
            return AccreditationRisk(
                department_code=dept.department_code,
                risk_level="critical",
                risk_score=100.0,
                risk_factors=["No course data submitted"],
                mitigating_factors=[],
                recommended_actions=["Submit all course attainment data immediately"],
                estimated_readiness_gap_months=12,
            )

        avg_attainment = statistics.mean(c.overall_attainment for c in dept.courses)

        # Attainment risk
        if avg_attainment < 50.0:
            risk_score += 35.0
            risk_factors.append(
                f"Average attainment {avg_attainment:.1f}% is critically below the 60% target"
            )
        elif avg_attainment < 60.0:
            risk_score += 20.0
            risk_factors.append(
                f"Average attainment {avg_attainment:.1f}% is below the 60% target"
            )
        else:
            mitigating_factors.append(
                f"Average attainment {avg_attainment:.1f}% meets or exceeds target"
            )

        # Trend risk
        if len(dept.historical_attainments) >= 2:
            recent_delta = (
                dept.historical_attainments[-1] - dept.historical_attainments[-2]
            )
            if recent_delta < -3.0:
                risk_score += 25.0
                risk_factors.append(
                    f"Attainment declining sharply (Δ = {recent_delta:.1f}%)"
                )
            elif recent_delta < 0.0:
                risk_score += 10.0
                risk_factors.append(f"Attainment trending downward (Δ = {recent_delta:.1f}%)")
            else:
                mitigating_factors.append(
                    f"Attainment stable or improving (Δ = {recent_delta:.1f}%)"
                )
        else:
            risk_score += 10.0
            risk_factors.append("Insufficient historical data for trend analysis")

        # Coverage risk
        coverage_ratios = [
            c.assessed_students / c.enrolled_students
            for c in dept.courses
            if c.enrolled_students > 0
        ]
        if coverage_ratios:
            avg_coverage = statistics.mean(coverage_ratios)
            if avg_coverage < 0.80:
                risk_score += 20.0
                risk_factors.append(
                    f"Student assessment coverage {avg_coverage*100:.1f}% is below 80%"
                )
            else:
                mitigating_factors.append(
                    f"Student assessment coverage {avg_coverage*100:.1f}% is acceptable"
                )

        # PO documentation risk
        po_docs_ratios = []
        for c in dept.courses:
            if c.po_attainments:
                covered = sum(1 for v in c.po_attainments.values() if v > 0)
                po_docs_ratios.append(covered / len(c.po_attainments))
        if po_docs_ratios:
            avg_po_doc = statistics.mean(po_docs_ratios)
            if avg_po_doc < 0.70:
                risk_score += 20.0
                risk_factors.append(
                    f"PO documentation coverage {avg_po_doc*100:.1f}% is below 70%"
                )
            else:
                mitigating_factors.append(
                    f"PO documentation coverage {avg_po_doc*100:.1f}% is adequate"
                )

        risk_score = min(100.0, risk_score)

        if risk_score >= 70:
            risk_level = "critical"
            gap_months = 12
        elif risk_score >= 45:
            risk_level = "high"
            gap_months = 6
        elif risk_score >= 20:
            risk_level = "medium"
            gap_months = 3
        else:
            risk_level = "low"
            gap_months = 0

        recommended_actions = self._generate_risk_actions(
            risk_factors, avg_attainment, dept
        )

        return AccreditationRisk(
            department_code=dept.department_code,
            risk_level=risk_level,
            risk_score=round(risk_score, 2),
            risk_factors=risk_factors,
            mitigating_factors=mitigating_factors,
            recommended_actions=recommended_actions,
            estimated_readiness_gap_months=gap_months,
        )

    @staticmethod
    def _generate_risk_actions(
        risk_factors: list[str], avg_attainment: float, dept: DepartmentProfile
    ) -> list[str]:
        actions: list[str] = []
        if avg_attainment < 60.0:
            actions.append(
                "Implement targeted remediation programmes for under-performing COs"
            )
            actions.append(
                "Conduct root-cause analysis on low-attainment courses and revise pedagogical strategies"
            )
        if any("historical" in f.lower() for f in risk_factors):
            actions.append(
                "Archive and digitise historical attainment records for at least three prior cycles"
            )
        if any("coverage" in f.lower() for f in risk_factors):
            actions.append(
                "Enforce mandatory participation in all assessment instruments to improve coverage"
            )
        if any("po documentation" in f.lower() for f in risk_factors):
            actions.append(
                "Assign faculty coordinators to ensure full PO attainment documentation per course"
            )
        if not actions:
            actions.append(
                "Maintain current performance and document best practices for SAR evidence"
            )
        return actions

    # ------------------------------------------------------------------
    # Executive summary
    # ------------------------------------------------------------------

    async def _generate_executive_summary(
        self,
        payload: AnalyticsRequest,
        readiness_scores: list[ReadinessScore],
        kpis: list[KPI],
        risks: list[AccreditationRisk],
    ) -> ExecutiveSummary:
        total = len(payload.departments)
        target = 60.0

        dept_attainments: dict[str, float] = {}
        for dept in payload.departments:
            if dept.courses:
                dept_attainments[dept.department_code] = statistics.mean(
                    c.overall_attainment for c in dept.courses
                )

        avg_attainment = (
            statistics.mean(dept_attainments.values()) if dept_attainments else 0.0
        )
        above_target = sum(1 for v in dept_attainments.values() if v >= target)
        at_risk = sum(
            1 for r in risks if r.risk_level in ("high", "critical")
        )

        overall_readiness = (
            statistics.mean(s.score for s in readiness_scores) if readiness_scores else 0.0
        )

        best_dept = (
            max(dept_attainments, key=dept_attainments.get)  # type: ignore[arg-type]
            if dept_attainments
            else "N/A"
        )

        # Most improved: largest positive delta in historical data
        most_improved: str | None = None
        best_delta = -math.inf
        for dept in payload.departments:
            if len(dept.historical_attainments) >= 2:
                delta = (
                    dept.historical_attainments[-1] - dept.historical_attainments[-2]
                )
                if delta > best_delta:
                    best_delta = delta
                    most_improved = dept.department_code

        highlights: list[str] = []
        concerns: list[str] = []
        recommendations: list[str] = []

        if above_target == total:
            highlights.append(
                f"All {total} departments meet the {target}% attainment target."
            )
        elif above_target > 0:
            highlights.append(
                f"{above_target} of {total} departments meet the {target}% attainment target."
            )

        if overall_readiness >= 75.0:
            highlights.append(
                f"Platform-wide readiness score of {overall_readiness:.1f}% indicates strong accreditation preparedness."
            )

        if at_risk > 0:
            concerns.append(
                f"{at_risk} department(s) are at high or critical accreditation risk and require immediate intervention."
            )

        critical_risks = [r for r in risks if r.risk_level == "critical"]
        for r in critical_risks:
            concerns.append(
                f"Department {r.department_code} has critical risk factors: {'; '.join(r.risk_factors[:2])}."
            )

        if avg_attainment < target:
            concerns.append(
                f"Platform average attainment of {avg_attainment:.1f}% is below the {target}% benchmark."
            )
            recommendations.append(
                "Establish a cross-departmental attainment improvement task force with quarterly reviews."
            )

        if at_risk > 0:
            recommendations.append(
                "Prioritise CI action plans for high-risk departments before the next accreditation visit."
            )

        recommendations.append(
            "Standardise CO-PO mapping methodology across all departments to ensure consistency in attainment calculations."
        )
        recommendations.append(
            "Schedule faculty development workshops focused on OBE implementation and assessment design."
        )

        return ExecutiveSummary(
            generated_at=datetime.now(timezone.utc),
            reference_year=payload.reference_year,
            total_departments=total,
            overall_platform_readiness=round(overall_readiness, 2),
            highlights=highlights,
            concerns=concerns,
            strategic_recommendations=recommendations,
            departments_above_target=above_target,
            departments_at_risk=at_risk,
            average_attainment=round(avg_attainment, 2),
            best_performing_department=best_dept,
            most_improved_department=most_improved,
        )
