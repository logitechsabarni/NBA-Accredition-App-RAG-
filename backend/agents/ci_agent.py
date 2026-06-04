"""
CI Agent – Continuous Improvement planning and tracking for NBA accreditation.

Responsibilities:
  - Gap identification from attainment data and compliance metrics
  - Continuous improvement recommendations
  - Corrective action planning
  - Follow-up tracking suggestions
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from pydantic import BaseModel, Field, field_validator

from backend.agents.base_agent import (
    AgentCapability,
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    ExecutionContext,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class GapSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    OBSERVATION = "observation"


class ActionCategory(str, Enum):
    CURRICULUM = "curriculum"
    PEDAGOGY = "pedagogy"
    ASSESSMENT = "assessment"
    INFRASTRUCTURE = "infrastructure"
    FACULTY_DEVELOPMENT = "faculty_development"
    STUDENT_SUPPORT = "student_support"
    INDUSTRY_ALIGNMENT = "industry_alignment"
    RESEARCH = "research"
    GOVERNANCE = "governance"


class ActionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class ActionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewCycle(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMESTER = "semester"
    ANNUAL = "annual"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class IdentifiedGap(BaseModel):
    gap_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: GapSeverity
    category: ActionCategory
    affected_outcomes: List[str] = Field(default_factory=list)
    root_cause: str
    evidence: str
    impact_description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str  # e.g., "attainment_analysis", "sar_review", "audit"
    nba_criteria_reference: Optional[str] = None


class CorrectiveAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gap_id: str
    title: str
    description: str
    category: ActionCategory
    priority: ActionPriority
    status: ActionStatus = ActionStatus.PLANNED
    responsible_person: str
    responsible_designation: str
    target_date: datetime
    estimated_cost_inr: Optional[float] = None
    expected_outcome: str
    success_metric: str
    success_threshold: str
    review_cycle: ReviewCycle
    next_review_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)

    @field_validator("target_date", mode="before")
    @classmethod
    def validate_target_date(cls, v: Any) -> Any:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class FollowUpTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_id: str
    title: str
    description: str
    due_date: datetime
    assignee: str
    reminder_days_before: int = 7
    completion_evidence_required: str
    auto_escalate_days: int = 3


class CIPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department: str
    program_name: str
    academic_year: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    gaps: List[IdentifiedGap] = Field(default_factory=list)
    corrective_actions: List[CorrectiveAction] = Field(default_factory=list)
    follow_up_tasks: List[FollowUpTask] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    executive_summary: str = ""
    critical_gap_count: int = 0
    major_gap_count: int = 0
    minor_gap_count: int = 0
    estimated_resolution_months: int = 0
    overall_ci_maturity_score: float = Field(default=0.0, ge=0.0, le=100.0)


# ---------------------------------------------------------------------------
# Input / Output schemas
# ---------------------------------------------------------------------------


class CIAgentInput(BaseModel):
    department: str
    program_name: str
    academic_year: str
    attainment_data: Dict[str, Any]
    program_outcomes: List[Dict[str, Any]]
    course_outcomes: List[Dict[str, Any]]
    previous_ci_actions: List[Dict[str, Any]] = Field(default_factory=list)
    sar_gaps: List[str] = Field(default_factory=list)
    faculty_data: List[Dict[str, Any]] = Field(default_factory=list)
    infrastructure_data: Dict[str, Any] = Field(default_factory=dict)
    student_performance_data: Dict[str, Any] = Field(default_factory=dict)
    attainment_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    nba_criteria_weights: Dict[str, float] = Field(default_factory=dict)


class CIAgentOutput(BaseModel):
    ci_plan: CIPlan
    gap_summary: Dict[str, int]
    action_summary: Dict[str, int]
    high_priority_actions: List[CorrectiveAction]
    recommendations: List[str]
    ci_maturity_score: float
    next_review_date: datetime


# ---------------------------------------------------------------------------
# Internal gap analysis engine
# ---------------------------------------------------------------------------


class _GapAnalyzer:
    """Identifies gaps from multiple data sources."""

    def __init__(self, inp: CIAgentInput) -> None:
        self.inp = inp
        self._now = datetime.now(timezone.utc)

    def analyze_attainment_gaps(self) -> List[IdentifiedGap]:
        gaps: List[IdentifiedGap] = []
        attainment = self.inp.attainment_data
        po_wise: Dict[str, float] = attainment.get("po_wise_attainment", {})
        threshold = self.inp.attainment_threshold

        for po_key, value in po_wise.items():
            if value < threshold:
                deficit = threshold - value
                severity = (
                    GapSeverity.CRITICAL if deficit > 20
                    else GapSeverity.MAJOR if deficit > 10
                    else GapSeverity.MINOR
                )
                po_desc = next(
                    (
                        p.get("description", po_key)
                        for p in self.inp.program_outcomes
                        if str(p.get("id", "")) == str(po_key) or p.get("code") == po_key
                    ),
                    po_key,
                )
                gaps.append(
                    IdentifiedGap(
                        title=f"Low Attainment – {po_key}",
                        description=(
                            f"Program Outcome {po_key} ({po_desc}) has attainment of "
                            f"{value:.1f}%, which is {deficit:.1f}% below the "
                            f"threshold of {threshold}%."
                        ),
                        severity=severity,
                        category=ActionCategory.ASSESSMENT,
                        affected_outcomes=[po_key],
                        root_cause=(
                            "Insufficient alignment between course delivery, assessment "
                            "instruments, and the targeted Program Outcome."
                        ),
                        evidence=f"Direct attainment = {value:.1f}%; Threshold = {threshold}%",
                        impact_description=(
                            f"Students graduating from this program may lack competency in {po_desc}."
                        ),
                        source="attainment_analysis",
                        nba_criteria_reference="Criteria 3",
                    )
                )

        direct_avg = attainment.get("direct_attainment_average", 100.0)
        indirect_avg = attainment.get("indirect_attainment_average", 100.0)
        if abs(direct_avg - indirect_avg) > 15.0:
            gaps.append(
                IdentifiedGap(
                    title="Significant Direct-Indirect Attainment Discrepancy",
                    description=(
                        f"Direct attainment ({direct_avg:.1f}%) and indirect attainment "
                        f"({indirect_avg:.1f}%) differ by more than 15 percentage points, "
                        "indicating misalignment in assessment triangulation."
                    ),
                    severity=GapSeverity.MAJOR,
                    category=ActionCategory.ASSESSMENT,
                    affected_outcomes=list(po_wise.keys()),
                    root_cause="Assessment instruments may not be capturing true learning outcomes",
                    evidence=f"Direct avg={direct_avg:.1f}%, Indirect avg={indirect_avg:.1f}%",
                    impact_description="Unreliable attainment data reduces credibility of SAR.",
                    source="attainment_analysis",
                    nba_criteria_reference="Criteria 3",
                )
            )
        return gaps

    def analyze_faculty_gaps(self) -> List[IdentifiedGap]:
        gaps: List[IdentifiedGap] = []
        faculty = self.inp.faculty_data
        if not faculty:
            return gaps

        total = len(faculty)
        phd_count = sum(1 for f in faculty if f.get("qualification") == "PhD")
        phd_ratio = phd_count / total if total else 0

        if phd_ratio < 0.5:
            gaps.append(
                IdentifiedGap(
                    title="Insufficient PhD-Qualified Faculty",
                    description=(
                        f"Only {phd_count} of {total} faculty ({phd_ratio*100:.1f}%) hold "
                        "doctoral qualifications. NBA Tier-I requires ≥50%."
                    ),
                    severity=GapSeverity.CRITICAL if phd_ratio < 0.3 else GapSeverity.MAJOR,
                    category=ActionCategory.FACULTY_DEVELOPMENT,
                    affected_outcomes=[],
                    root_cause="Recruitment policy not prioritising doctoral qualifications",
                    evidence=f"PhD faculty = {phd_count}/{total} ({phd_ratio*100:.1f}%)",
                    impact_description="Non-compliance with NBA faculty qualification norm",
                    source="faculty_analysis",
                    nba_criteria_reference="Criteria 5",
                )
            )

        low_pub_faculty = [f for f in faculty if f.get("publications_count", 0) < 2]
        if len(low_pub_faculty) > total * 0.4:
            gaps.append(
                IdentifiedGap(
                    title="Low Faculty Research Output",
                    description=(
                        f"{len(low_pub_faculty)} faculty members have fewer than 2 publications "
                        "in indexed journals, indicating low research activity."
                    ),
                    severity=GapSeverity.MAJOR,
                    category=ActionCategory.RESEARCH,
                    affected_outcomes=[],
                    root_cause="Insufficient research incentives or time allocation",
                    evidence=f"{len(low_pub_faculty)}/{total} faculty with <2 publications",
                    impact_description="Reduces department research reputation and NBA score",
                    source="faculty_analysis",
                    nba_criteria_reference="Criteria 5",
                )
            )
        return gaps

    def analyze_infrastructure_gaps(self) -> List[IdentifiedGap]:
        gaps: List[IdentifiedGap] = []
        infra = self.inp.infrastructure_data
        lab_count = infra.get("laboratory_count", 0)
        software_count = infra.get("licensed_software_count", 0)

        if lab_count < 3:
            gaps.append(
                IdentifiedGap(
                    title="Insufficient Laboratory Facilities",
                    description=f"Only {lab_count} laboratory/ies available; minimum 3 recommended for the program.",
                    severity=GapSeverity.MAJOR,
                    category=ActionCategory.INFRASTRUCTURE,
                    affected_outcomes=[],
                    root_cause="Capital budget constraints or delayed procurement",
                    evidence=f"lab_count={lab_count}",
                    impact_description="Students lack hands-on practical exposure",
                    source="infrastructure_analysis",
                    nba_criteria_reference="Criteria 6",
                )
            )
        if software_count < 5:
            gaps.append(
                IdentifiedGap(
                    title="Limited Licensed Software",
                    description=f"Only {software_count} licensed software packages available.",
                    severity=GapSeverity.MINOR,
                    category=ActionCategory.INFRASTRUCTURE,
                    affected_outcomes=[],
                    root_cause="Software budget constraints",
                    evidence=f"licensed_software_count={software_count}",
                    impact_description="Restricts student exposure to industry-standard tools",
                    source="infrastructure_analysis",
                    nba_criteria_reference="Criteria 6",
                )
            )
        return gaps

    def analyze_student_performance_gaps(self) -> List[IdentifiedGap]:
        gaps: List[IdentifiedGap] = []
        sp = self.inp.student_performance_data
        pass_rate = sp.get("average_pass_rate", 100.0)
        placement_rate = sp.get("placement_rate", 100.0)

        if pass_rate < 70.0:
            gaps.append(
                IdentifiedGap(
                    title="Low Average Pass Rate",
                    description=f"Average pass rate of {pass_rate:.1f}% is below the 70% benchmark.",
                    severity=GapSeverity.CRITICAL if pass_rate < 55 else GapSeverity.MAJOR,
                    category=ActionCategory.STUDENT_SUPPORT,
                    affected_outcomes=[],
                    root_cause="Insufficient student support mechanisms and remedial teaching",
                    evidence=f"average_pass_rate={pass_rate:.1f}%",
                    impact_description="Poor academic performance indicates curriculum delivery issues",
                    source="student_performance_analysis",
                    nba_criteria_reference="Criteria 4",
                )
            )
        if placement_rate < 50.0:
            gaps.append(
                IdentifiedGap(
                    title="Low Placement Rate",
                    description=f"Placement rate of {placement_rate:.1f}% is below the 50% target.",
                    severity=GapSeverity.MAJOR,
                    category=ActionCategory.INDUSTRY_ALIGNMENT,
                    affected_outcomes=[],
                    root_cause="Insufficient industry interaction and employability skill training",
                    evidence=f"placement_rate={placement_rate:.1f}%",
                    impact_description="Low placement indicates gap between curriculum and industry needs",
                    source="student_performance_analysis",
                    nba_criteria_reference="Criteria 4",
                )
            )
        return gaps

    def analyze_sar_gaps(self) -> List[IdentifiedGap]:
        gaps: List[IdentifiedGap] = []
        for raw_gap in self.inp.sar_gaps:
            if not raw_gap:
                continue
            category = ActionCategory.GOVERNANCE
            if "curriculum" in raw_gap.lower():
                category = ActionCategory.CURRICULUM
            elif "faculty" in raw_gap.lower() or "phd" in raw_gap.lower():
                category = ActionCategory.FACULTY_DEVELOPMENT
            elif "lab" in raw_gap.lower() or "infrastructure" in raw_gap.lower():
                category = ActionCategory.INFRASTRUCTURE
            elif "attainment" in raw_gap.lower() or "co" in raw_gap.lower() or "po" in raw_gap.lower():
                category = ActionCategory.ASSESSMENT
            gaps.append(
                IdentifiedGap(
                    title=f"SAR-Identified Gap: {raw_gap[:60]}",
                    description=raw_gap,
                    severity=GapSeverity.MAJOR,
                    category=category,
                    affected_outcomes=[],
                    root_cause="Identified during SAR review process",
                    evidence="SAR review documentation",
                    impact_description="Potential non-compliance with NBA accreditation criteria",
                    source="sar_review",
                    nba_criteria_reference="Multiple Criteria",
                )
            )
        return gaps

    def collect_all_gaps(self) -> List[IdentifiedGap]:
        all_gaps: List[IdentifiedGap] = []
        all_gaps.extend(self.analyze_attainment_gaps())
        all_gaps.extend(self.analyze_faculty_gaps())
        all_gaps.extend(self.analyze_infrastructure_gaps())
        all_gaps.extend(self.analyze_student_performance_gaps())
        all_gaps.extend(self.analyze_sar_gaps())
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.MAJOR: 1,
            GapSeverity.MINOR: 2,
            GapSeverity.OBSERVATION: 3,
        }
        return sorted(all_gaps, key=lambda g: severity_order[g.severity])


# ---------------------------------------------------------------------------
# Internal action planner
# ---------------------------------------------------------------------------


class _ActionPlanner:
    """Generates corrective actions and follow-up tasks from identified gaps."""

    _SEVERITY_WEEKS: Dict[GapSeverity, int] = {
        GapSeverity.CRITICAL: 12,
        GapSeverity.MAJOR: 24,
        GapSeverity.MINOR: 36,
        GapSeverity.OBSERVATION: 52,
    }

    _SEVERITY_PRIORITY: Dict[GapSeverity, ActionPriority] = {
        GapSeverity.CRITICAL: ActionPriority.HIGH,
        GapSeverity.MAJOR: ActionPriority.HIGH,
        GapSeverity.MINOR: ActionPriority.MEDIUM,
        GapSeverity.OBSERVATION: ActionPriority.LOW,
    }

    _CATEGORY_RESPONSIBLE: Dict[ActionCategory, Tuple[str, str]] = {
        ActionCategory.CURRICULUM: ("Program Coordinator", "Associate Professor"),
        ActionCategory.PEDAGOGY: ("Teaching Learning Committee Chair", "Professor"),
        ActionCategory.ASSESSMENT: ("NBA Coordinator", "Associate Professor"),
        ActionCategory.INFRASTRUCTURE: ("Department HOD", "Head of Department"),
        ActionCategory.FACULTY_DEVELOPMENT: ("Dean Academics", "Dean"),
        ActionCategory.STUDENT_SUPPORT: ("Student Welfare Officer", "Assistant Professor"),
        ActionCategory.INDUSTRY_ALIGNMENT: ("Training & Placement Officer", "Officer"),
        ActionCategory.RESEARCH: ("Research Committee Head", "Professor"),
        ActionCategory.GOVERNANCE: ("Department HOD", "Head of Department"),
    }

    def __init__(self) -> None:
        self._now = datetime.now(timezone.utc)

    def _action_description(self, gap: IdentifiedGap) -> str:
        templates: Dict[ActionCategory, str] = {
            ActionCategory.ASSESSMENT: (
                f"Review and revise assessment instruments for outcomes linked to gap: '{gap.title}'. "
                "Increase frequency of formative assessments, introduce rubric-based evaluation, "
                "and ensure bloom's taxonomy alignment across all assessment levels."
            ),
            ActionCategory.CURRICULUM: (
                f"Initiate curriculum revision to address: '{gap.title}'. "
                "Convene Board of Studies to review and update course content, add industry-relevant "
                "topics, and ensure CO-PO mapping is strengthened."
            ),
            ActionCategory.FACULTY_DEVELOPMENT: (
                f"Design and implement faculty development programme to address: '{gap.title}'. "
                "Sponsor faculty for PhD enrolment, arrange FDPs, workshops, and research grants."
            ),
            ActionCategory.INFRASTRUCTURE: (
                f"Procure and install required infrastructure to address: '{gap.title}'. "
                "Prepare procurement schedule, obtain budget approval, and commission the facility."
            ),
            ActionCategory.STUDENT_SUPPORT: (
                f"Implement targeted student support interventions to address: '{gap.title}'. "
                "Introduce remedial classes, peer tutoring, and mentoring programmes for slow learners."
            ),
            ActionCategory.INDUSTRY_ALIGNMENT: (
                f"Strengthen industry linkages to address: '{gap.title}'. "
                "Organise industry visits, invite guest lecturers, and design internship programmes."
            ),
            ActionCategory.RESEARCH: (
                f"Promote research activity to address: '{gap.title}'. "
                "Set publication targets, provide seed grants, and recognise research contributions."
            ),
            ActionCategory.PEDAGOGY: (
                f"Adopt innovative teaching methods to address: '{gap.title}'. "
                "Train faculty on active learning, flipped classroom, and project-based learning."
            ),
            ActionCategory.GOVERNANCE: (
                f"Strengthen governance processes to address: '{gap.title}'. "
                "Review policies, update documentation, and establish monitoring mechanisms."
            ),
        }
        return templates.get(gap.category, f"Address gap: {gap.title}")

    def build_action(self, gap: IdentifiedGap) -> CorrectiveAction:
        weeks = self._SEVERITY_WEEKS[gap.severity]
        target_date = self._now + timedelta(weeks=weeks)
        responsible_person, responsible_designation = self._CATEGORY_RESPONSIBLE.get(
            gap.category, ("Department HOD", "Head of Department")
        )
        priority = self._SEVERITY_PRIORITY[gap.severity]
        review_cycle = (
            ReviewCycle.MONTHLY if gap.severity in (GapSeverity.CRITICAL, GapSeverity.MAJOR)
            else ReviewCycle.QUARTERLY
        )
        return CorrectiveAction(
            gap_id=gap.gap_id,
            title=f"CA: {gap.title}",
            description=self._action_description(gap),
            category=gap.category,
            priority=priority,
            responsible_person=responsible_person,
            responsible_designation=responsible_designation,
            target_date=target_date,
            expected_outcome=f"Resolution of gap: {gap.title}",
            success_metric=f"Measurable improvement in {gap.category.value} indicators",
            success_threshold="≥ 10% improvement or gap closure within target date",
            review_cycle=review_cycle,
            next_review_date=self._now + timedelta(
                weeks=4 if review_cycle == ReviewCycle.MONTHLY else 13
            ),
            tags=[gap.category.value, gap.severity.value, "nba", "ci"],
        )

    def build_follow_up(self, action: CorrectiveAction) -> List[FollowUpTask]:
        tasks: List[FollowUpTask] = []
        tasks.append(
            FollowUpTask(
                action_id=action.action_id,
                title=f"Initiate: {action.title}",
                description=f"Begin implementation of corrective action: {action.description[:100]}",
                due_date=datetime.now(timezone.utc) + timedelta(weeks=2),
                assignee=action.responsible_person,
                reminder_days_before=3,
                completion_evidence_required="Meeting minutes or implementation note",
                auto_escalate_days=5,
            )
        )
        tasks.append(
            FollowUpTask(
                action_id=action.action_id,
                title=f"Mid-point Review: {action.title}",
                description=f"Review progress at mid-point of corrective action timeline.",
                due_date=action.target_date - timedelta(weeks=4),
                assignee=action.responsible_person,
                reminder_days_before=7,
                completion_evidence_required="Progress report with evidence",
                auto_escalate_days=3,
            )
        )
        tasks.append(
            FollowUpTask(
                action_id=action.action_id,
                title=f"Closure Verification: {action.title}",
                description="Verify gap closure with measurable evidence and update CI register.",
                due_date=action.target_date,
                assignee=action.responsible_person,
                reminder_days_before=14,
                completion_evidence_required="Closure report with before/after metrics",
                auto_escalate_days=3,
            )
        )
        return tasks

    def plan(self, gaps: List[IdentifiedGap]) -> Tuple[List[CorrectiveAction], List[FollowUpTask]]:
        actions: List[CorrectiveAction] = []
        follow_ups: List[FollowUpTask] = []
        for gap in gaps:
            action = self.build_action(gap)
            actions.append(action)
            follow_ups.extend(self.build_follow_up(action))
        return actions, follow_ups


# ---------------------------------------------------------------------------
# Recommendation generator
# ---------------------------------------------------------------------------


def _generate_recommendations(
    gaps: List[IdentifiedGap],
    actions: List[CorrectiveAction],
    inp: CIAgentInput,
) -> List[str]:
    recs: List[str] = []

    critical_count = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL)
    if critical_count > 0:
        recs.append(
            f"URGENT: {critical_count} critical gap(s) identified. Immediate action required "
            "by the Department HOD and NBA Coordinator within 30 days."
        )

    attainment_actions = [a for a in actions if a.category == ActionCategory.ASSESSMENT]
    if attainment_actions:
        recs.append(
            "Implement an outcome-based assessment reform: revise question papers to target "
            "higher cognitive levels (Bloom's L3–L6) for underperforming Program Outcomes."
        )

    faculty_actions = [a for a in actions if a.category == ActionCategory.FACULTY_DEVELOPMENT]
    if faculty_actions:
        recs.append(
            "Establish a Faculty Development Roadmap with quarterly FDPs, PhD sponsorship "
            "policy, and publication incentive scheme to improve research output."
        )

    infra_actions = [a for a in actions if a.category == ActionCategory.INFRASTRUCTURE]
    if infra_actions:
        recs.append(
            "Prepare a 3-year infrastructure capital plan aligned with program growth, "
            "targeting equipment upgrades, software procurement, and laboratory modernisation."
        )

    recs.append(
        "Establish a CI Monitoring Dashboard: track all corrective actions, review evidence "
        "monthly, and report progress to the NBA Steering Committee quarterly."
    )

    if inp.previous_ci_actions:
        prev_completed = sum(
            1 for a in inp.previous_ci_actions if a.get("status") == "completed"
        )
        prev_total = len(inp.previous_ci_actions)
        if prev_total and prev_completed / prev_total < 0.6:
            recs.append(
                f"Previous CI cycle had only {prev_completed}/{prev_total} actions completed. "
                "Strengthen accountability: assign action owners, set escalation triggers, "
                "and conduct fortnightly review meetings."
            )

    recs.append(
        "Conduct a stakeholder perception survey (students, alumni, employers) annually "
        "to identify evolving skill gaps and update PEOs/POs accordingly."
    )
    return recs


def _compute_ci_maturity(
    gaps: List[IdentifiedGap],
    previous_actions: List[Dict[str, Any]],
) -> float:
    base_score = 100.0
    severity_penalty = {
        GapSeverity.CRITICAL: 15.0,
        GapSeverity.MAJOR: 7.0,
        GapSeverity.MINOR: 3.0,
        GapSeverity.OBSERVATION: 1.0,
    }
    for gap in gaps:
        base_score -= severity_penalty.get(gap.severity, 0)

    if previous_actions:
        completion_rate = (
            sum(1 for a in previous_actions if a.get("status") == "completed")
            / len(previous_actions)
        )
        base_score += completion_rate * 15.0

    return round(max(0.0, min(100.0, base_score)), 2)


def _build_executive_summary(
    gaps: List[IdentifiedGap],
    actions: List[CorrectiveAction],
    maturity: float,
    inp: CIAgentInput,
) -> str:
    critical = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL)
    major = sum(1 for g in gaps if g.severity == GapSeverity.MAJOR)
    minor = sum(1 for g in gaps if g.severity == GapSeverity.MINOR)
    high_priority = sum(1 for a in actions if a.priority == ActionPriority.HIGH)
    return (
        f"This Continuous Improvement Plan for '{inp.program_name}', Department of "
        f"{inp.department}, covers the academic year {inp.academic_year}. "
        f"A total of {len(gaps)} gaps have been identified: {critical} critical, "
        f"{major} major, and {minor} minor. "
        f"{len(actions)} corrective actions have been planned, of which {high_priority} "
        f"are high priority. The CI Maturity Score stands at {maturity:.1f}/100. "
        "All actions have been assigned responsible personnel, target dates, success "
        "metrics, and follow-up tasks for systematic monitoring."
    )


# ---------------------------------------------------------------------------
# CI Agent
# ---------------------------------------------------------------------------


class CIAgent(BaseAgent):
    """
    Continuous Improvement (CI) Agent for NBA accreditation.

    Identifies gaps from attainment, faculty, infrastructure, and SAR data,
    then generates a structured corrective action plan with follow-up tasks.
    """

    def __init__(self) -> None:
        metadata = AgentMetadata(
            agent_id="ci-agent-v1",
            name="CI Agent",
            version="1.0.0",
            description=(
                "Identifies program gaps and generates structured corrective action plans "
                "with follow-up tracking for NBA continuous improvement compliance."
            ),
            capabilities=[
                AgentCapability.ANALYSIS,
                AgentCapability.PLANNING,
                AgentCapability.RECOMMENDATION,
                AgentCapability.REPORTING,
            ],
            author="NBA Enterprise AI Platform",
            tags=["ci", "continuous-improvement", "nba", "gap-analysis", "action-plan"],
        )
        super().__init__(metadata=metadata)

    # ------------------------------------------------------------------
    # Validation hooks
    # ------------------------------------------------------------------

    async def _validate_input(self, request: AgentRequest) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        p = request.payload
        if not p.get("department"):
            errors.append("department is required")
        if not p.get("program_name"):
            errors.append("program_name is required")
        if not p.get("academic_year"):
            errors.append("academic_year is required")
        attainment = p.get("attainment_data")
        if not attainment or not isinstance(attainment, dict):
            errors.append("attainment_data must be a non-empty dict")
        return len(errors) == 0, errors

    async def _validate_output(self, result: Any) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not isinstance(result, CIAgentOutput):
            errors.append("Output must be CIAgentOutput")
            return False, errors
        if result.ci_maturity_score < 0 or result.ci_maturity_score > 100:
            errors.append("ci_maturity_score out of range")
        return len(errors) == 0, errors

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    async def _execute_internal(
        self,
        request: AgentRequest,
        context: ExecutionContext,
    ) -> AgentResponse:
        log = logger.bind(
            agent_id=self.metadata.agent_id,
            request_id=request.request_id,
            department=request.payload.get("department"),
        )
        log.info("ci_agent.execute.start")

        try:
            inp = CIAgentInput(**request.payload)
        except Exception as exc:
            log.error("ci_agent.input_parse_error", error=str(exc))
            return self._error_response(request=request, message=f"Input validation failed: {exc}")

        # Gap analysis
        analyzer = _GapAnalyzer(inp)
        gaps = analyzer.collect_all_gaps()
        log.info("ci_agent.gaps_identified", count=len(gaps))

        # Action planning
        planner = _ActionPlanner()
        actions, follow_ups = planner.plan(gaps)
        log.info("ci_agent.actions_planned", action_count=len(actions), follow_up_count=len(follow_ups))

        # Recommendations and maturity
        recommendations = _generate_recommendations(gaps, actions, inp)
        maturity = _compute_ci_maturity(gaps, inp.previous_ci_actions)
        executive_summary = _build_executive_summary(gaps, actions, maturity, inp)

        # Compute resolution timeline
        max_weeks = max(
            (
                _ActionPlanner._SEVERITY_WEEKS[g.severity]
                for g in gaps
            ),
            default=0,
        )

        ci_plan = CIPlan(
            department=inp.department,
            program_name=inp.program_name,
            academic_year=inp.academic_year,
            gaps=gaps,
            corrective_actions=actions,
            follow_up_tasks=follow_ups,
            recommendations=recommendations,
            executive_summary=executive_summary,
            critical_gap_count=sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL),
            major_gap_count=sum(1 for g in gaps if g.severity == GapSeverity.MAJOR),
            minor_gap_count=sum(1 for g in gaps if g.severity == GapSeverity.MINOR),
            estimated_resolution_months=round(max_weeks / 4.33),
            overall_ci_maturity_score=maturity,
        )

        gap_summary = {
            "total": len(gaps),
            "critical": ci_plan.critical_gap_count,
            "major": ci_plan.major_gap_count,
            "minor": ci_plan.minor_gap_count,
            "observation": sum(1 for g in gaps if g.severity == GapSeverity.OBSERVATION),
        }

        action_summary = {
            "total": len(actions),
            "high_priority": sum(1 for a in actions if a.priority == ActionPriority.HIGH),
            "medium_priority": sum(1 for a in actions if a.priority == ActionPriority.MEDIUM),
            "low_priority": sum(1 for a in actions if a.priority == ActionPriority.LOW),
            "follow_up_tasks": len(follow_ups),
        }

        high_priority_actions = [a for a in actions if a.priority == ActionPriority.HIGH]

        now = datetime.now(timezone.utc)
        next_review = now + timedelta(weeks=4)

        output = CIAgentOutput(
            ci_plan=ci_plan,
            gap_summary=gap_summary,
            action_summary=action_summary,
            high_priority_actions=high_priority_actions,
            recommendations=recommendations,
            ci_maturity_score=maturity,
            next_review_date=next_review,
        )

        log.info(
            "ci_agent.execute.complete",
            gap_count=len(gaps),
            action_count=len(actions),
            maturity_score=maturity,
            critical_gaps=ci_plan.critical_gap_count,
        )

        return AgentResponse(
            request_id=request.request_id,
            agent_id=self.metadata.agent_id,
            status=AgentStatus.SUCCESS,
            result=output.model_dump(),
            metadata={
                "gap_summary": gap_summary,
                "action_summary": action_summary,
                "ci_maturity_score": maturity,
                "estimated_resolution_months": ci_plan.estimated_resolution_months,
                "next_review_date": next_review.isoformat(),
            },
        )
