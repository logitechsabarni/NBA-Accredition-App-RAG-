"""
backend/api/routes/analytics.py
────────────────────────────────
Analytics routes — accreditation readiness, KPIs, attainment, benchmarking.
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.api.deps import CurrentUser

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ReadinessScore(BaseModel):
    overall: float = Field(..., ge=0, le=100, description="0-100 readiness score")
    risk_level: Literal["low", "medium", "high", "critical"]
    breakdown: dict[str, float]
    last_updated: str


class KPIData(BaseModel):
    kpi: str
    value: float
    unit: str
    trend: Literal["up", "down", "stable"]
    delta: float | None = None


class AttainmentSummary(BaseModel):
    department: str
    program: str
    direct_attainment: float
    indirect_attainment: float
    po_attainment: dict[str, float]
    threshold_met: bool


class BenchmarkRow(BaseModel):
    department: str
    score: float
    rank: int
    above_threshold: bool


class DashboardOverview(BaseModel):
    readiness: ReadinessScore
    kpis: list[KPIData]
    top_attainment: list[AttainmentSummary]
    benchmark: list[BenchmarkRow]


# ── Static fixtures (replace with real DB queries) ────────────────────────────

_READINESS = ReadinessScore(
    overall=84.7,
    risk_level="medium",
    breakdown={
        "CO-PO Mapping":    91.0,
        "Attainment":       83.5,
        "SAR Completeness": 78.0,
        "CI Actions":       86.0,
    },
    last_updated="2025-06-01T10:30:00Z",
)

_KPIS: list[KPIData] = [
    KPIData(kpi="Average Direct Attainment", value=72.4,  unit="%",  trend="up",   delta=2.1),
    KPIData(kpi="Average Indirect Attainment", value=68.9, unit="%", trend="stable", delta=0.0),
    KPIData(kpi="PO Achievement Rate",        value=81.2,  unit="%",  trend="up",   delta=3.5),
    KPIData(kpi="Active CI Actions",          value=14,    unit="count", trend="down", delta=-3),
    KPIData(kpi="SAR Sections Approved",      value=6,     unit="count", trend="up",   delta=1),
]

_ATTAINMENT: list[AttainmentSummary] = [
    AttainmentSummary(
        department="CSE", program="B.Tech CSE",
        direct_attainment=74.2, indirect_attainment=71.0,
        po_attainment={"PO1": 80, "PO2": 75, "PO3": 68},
        threshold_met=True,
    ),
    AttainmentSummary(
        department="ECE", program="B.Tech ECE",
        direct_attainment=69.8, indirect_attainment=65.5,
        po_attainment={"PO1": 72, "PO2": 70, "PO3": 60},
        threshold_met=False,
    ),
    AttainmentSummary(
        department="MECH", program="B.Tech MECH",
        direct_attainment=71.1, indirect_attainment=68.0,
        po_attainment={"PO1": 76, "PO2": 72, "PO3": 65},
        threshold_met=True,
    ),
]

_BENCHMARKS: list[BenchmarkRow] = [
    BenchmarkRow(department="CSE",  score=82.1, rank=1, above_threshold=True),
    BenchmarkRow(department="MECH", score=78.4, rank=2, above_threshold=True),
    BenchmarkRow(department="ECE",  score=74.9, rank=3, above_threshold=True),
    BenchmarkRow(department="CIVIL", score=61.2, rank=4, above_threshold=False),
]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=DashboardOverview,
    summary="Full analytics dashboard overview",
)
async def dashboard(user: CurrentUser) -> DashboardOverview:
    return DashboardOverview(
        readiness=_READINESS,
        kpis=_KPIS,
        top_attainment=_ATTAINMENT,
        benchmark=_BENCHMARKS,
    )


@router.get(
    "/readiness",
    response_model=ReadinessScore,
    summary="Accreditation readiness score with breakdown",
)
async def readiness(user: CurrentUser) -> ReadinessScore:
    return _READINESS


@router.get(
    "/kpis",
    response_model=list[KPIData],
    summary="Key performance indicators",
)
async def kpis(user: CurrentUser) -> list[KPIData]:
    return _KPIS


@router.get(
    "/attainment",
    response_model=list[AttainmentSummary],
    summary="CO / PO attainment summary per department",
)
async def attainment(
    user: CurrentUser,
    department: str | None = Query(default=None, description="Filter by department name"),
) -> list[AttainmentSummary]:
    data = _ATTAINMENT
    if department:
        data = [d for d in data if d.department.lower() == department.lower()]
    return data


@router.get(
    "/benchmark",
    response_model=list[BenchmarkRow],
    summary="Department benchmarking ranked by score",
)
async def benchmark(user: CurrentUser) -> list[BenchmarkRow]:
    return sorted(_BENCHMARKS, key=lambda x: x.rank)
