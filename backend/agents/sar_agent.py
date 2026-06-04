"""
SAR Agent – Self-Assessment Report generation for NBA accreditation.

Responsibilities:
  - SAR section generation (Criteria 1-8)
  - Evidence recommendation
  - Accreditation narrative generation
  - PDF-ready structured output
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

import structlog
from pydantic import BaseModel, Field, model_validator

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


class SARCriteria(str, Enum):
    CRITERIA_1 = "criteria_1_vision_mission"
    CRITERIA_2 = "criteria_2_program_curriculum"
    CRITERIA_3 = "criteria_3_course_outcomes"
    CRITERIA_4 = "criteria_4_students_performance"
    CRITERIA_5 = "criteria_5_faculty"
    CRITERIA_6 = "criteria_6_facilities"
    CRITERIA_7 = "criteria_7_continuous_improvement"
    CRITERIA_8 = "criteria_8_first_year_program"


class EvidenceType(str, Enum):
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    DOCUMENTARY = "documentary"
    SURVEY = "survey"
    ASSESSMENT = "assessment"
    INDUSTRY_FEEDBACK = "industry_feedback"


class NarrativeTone(str, Enum):
    FORMAL = "formal"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType
    title: str
    description: str
    source: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    criteria_mapping: List[SARCriteria]
    document_reference: Optional[str] = None
    year: Optional[int] = None
    quantitative_value: Optional[float] = None
    unit: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SARSection(BaseModel):
    section_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criteria: SARCriteria
    title: str
    narrative: str
    sub_sections: List[Dict[str, str]] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_score: float = Field(ge=0.0, le=100.0)
    gaps: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    page_break_after: bool = True


class SARDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    institution_name: str
    program_name: str
    department: str
    accreditation_year: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sections: List[SARSection] = Field(default_factory=list)
    executive_summary: str = ""
    overall_compliance_score: float = Field(default=0.0, ge=0.0, le=100.0)
    total_evidence_items: int = 0
    critical_gaps: List[str] = Field(default_factory=list)
    pdf_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def compute_derived_fields(self) -> "SARDocument":
        if self.sections:
            scores = [s.compliance_score for s in self.sections]
            self.overall_compliance_score = round(sum(scores) / len(scores), 2)
            self.total_evidence_items = sum(len(s.evidence_items) for s in self.sections)
            self.critical_gaps = [
                gap
                for section in self.sections
                for gap in section.gaps
            ]
        return self


# ---------------------------------------------------------------------------
# Input / Output schemas
# ---------------------------------------------------------------------------


class SARGenerationInput(BaseModel):
    institution_name: str
    program_name: str
    department: str
    accreditation_year: int
    program_outcomes: List[Dict[str, Any]]
    course_outcomes: List[Dict[str, Any]]
    attainment_data: Dict[str, Any]
    faculty_data: List[Dict[str, Any]]
    infrastructure_data: Dict[str, Any]
    student_performance_data: Dict[str, Any]
    ci_actions: List[Dict[str, Any]] = Field(default_factory=list)
    narrative_tone: NarrativeTone = NarrativeTone.FORMAL
    include_criteria: Optional[List[SARCriteria]] = None
    previous_sar_gaps: List[str] = Field(default_factory=list)


class SARGenerationOutput(BaseModel):
    sar_document: SARDocument
    evidence_recommendations: List[EvidenceItem]
    missing_evidence: List[str]
    readiness_percentage: float
    generation_warnings: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class _SARBuilder:
    """Internal builder encapsulating section construction logic."""

    def __init__(self, inp: SARGenerationInput) -> None:
        self.inp = inp
        self.tone = inp.narrative_tone
        self._criteria_to_build: List[SARCriteria] = (
            inp.include_criteria if inp.include_criteria else list(SARCriteria)
        )

    # ------------------------------------------------------------------
    # Narrative helpers
    # ------------------------------------------------------------------

    def _formal_intro(self, subject: str) -> str:
        return (
            f"This section presents a comprehensive overview of {subject} "
            f"at {self.inp.institution_name}, Department of {self.inp.department}, "
            f"for the program '{self.inp.program_name}' as part of the "
            f"NBA Accreditation Self-Assessment Report for the year "
            f"{self.inp.accreditation_year}."
        )

    def _po_summary(self) -> str:
        pos = self.inp.program_outcomes
        if not pos:
            return "Program outcomes have not been defined."
        po_lines = "; ".join(
            f"PO{i+1}: {po.get('description', 'N/A')}"
            for i, po in enumerate(pos[:5])
        )
        return (
            f"The program has articulated {len(pos)} Program Outcomes. "
            f"Key outcomes include: {po_lines}. "
            "These outcomes are aligned with the NBA graduate attributes and "
            "Washington Accord signatory requirements."
        )

    def _attainment_narrative(self) -> str:
        data = self.inp.attainment_data
        direct_avg = data.get("direct_attainment_average", 0.0)
        indirect_avg = data.get("indirect_attainment_average", 0.0)
        threshold = data.get("attainment_threshold", 60.0)
        achieved = data.get("pos_achieved_count", 0)
        total_pos = len(self.inp.program_outcomes)
        return (
            f"Direct attainment analysis yields an average of {direct_avg:.1f}% "
            f"across all assessed Program Outcomes, while indirect attainment "
            f"averages {indirect_avg:.1f}%. The institution-defined threshold is "
            f"{threshold}%. Out of {total_pos} Program Outcomes, {achieved} have "
            "met or exceeded the threshold, demonstrating satisfactory performance "
            "in the majority of graduate competencies."
        )

    def _faculty_narrative(self) -> str:
        faculty = self.inp.faculty_data
        total = len(faculty)
        phd_count = sum(1 for f in faculty if f.get("qualification") == "PhD")
        avg_exp = (
            sum(f.get("experience_years", 0) for f in faculty) / total
            if total
            else 0
        )
        return (
            f"The department comprises {total} faculty members, of whom "
            f"{phd_count} hold doctoral qualifications, representing "
            f"{(phd_count/total*100 if total else 0):.1f}% of the faculty. "
            f"The average teaching experience is {avg_exp:.1f} years. "
            "Faculty qualifications meet the NBA stipulated norms for accreditation."
        )

    def _infrastructure_narrative(self) -> str:
        infra = self.inp.infrastructure_data
        lab_count = infra.get("laboratory_count", 0)
        software_count = infra.get("licensed_software_count", 0)
        library_volumes = infra.get("library_volumes", 0)
        return (
            f"The department is equipped with {lab_count} state-of-the-art "
            f"laboratories, {software_count} licensed software packages, and "
            f"access to a library with {library_volumes:,} volumes and digital "
            "resources. The infrastructure fully supports the curriculum and "
            "outcome-based education delivery."
        )

    def _student_performance_narrative(self) -> str:
        sp = self.inp.student_performance_data
        pass_rate = sp.get("average_pass_rate", 0.0)
        placement_rate = sp.get("placement_rate", 0.0)
        higher_studies = sp.get("higher_studies_percentage", 0.0)
        return (
            f"Student performance metrics indicate an average pass rate of "
            f"{pass_rate:.1f}% over the assessment period. Placement statistics "
            f"reflect a {placement_rate:.1f}% placement rate, with an additional "
            f"{higher_studies:.1f}% of graduates pursuing higher education. "
            "These metrics demonstrate strong student achievement and alignment "
            "with program educational objectives."
        )

    def _ci_narrative(self) -> str:
        actions = self.inp.ci_actions
        if not actions:
            return (
                "Continuous improvement mechanisms are in place and are being "
                "systematically documented and monitored."
            )
        completed = sum(1 for a in actions if a.get("status") == "completed")
        in_progress = sum(1 for a in actions if a.get("status") == "in_progress")
        return (
            f"The department has undertaken {len(actions)} continuous improvement "
            f"actions during the assessment period. Of these, {completed} have been "
            f"completed and {in_progress} are currently in progress. Actions address "
            "identified gaps in attainment, pedagogy, infrastructure, and industry "
            "alignment, demonstrating a commitment to systematic program improvement."
        )

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_criteria_1(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('Vision, Mission, and Program Educational Objectives (PEOs)')} "
            f"The institution's vision and mission statements are clearly articulated and "
            f"communicated to all stakeholders. The program's PEOs are derived from the "
            f"institutional mission and reflect the expectations of industry, academia, and "
            f"society. {self._po_summary()}"
        )
        evidence: List[EvidenceItem] = [
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Institution Vision and Mission Document",
                description="Official document stating institutional vision and mission",
                source="Institution Website / Academic Calendar",
                relevance_score=1.0,
                criteria_mapping=[SARCriteria.CRITERIA_1],
                document_reference="DOC-VM-001",
            ),
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Program Educational Objectives Document",
                description="Formally approved PEOs aligned with stakeholder inputs",
                source="Department Academic Council",
                relevance_score=0.95,
                criteria_mapping=[SARCriteria.CRITERIA_1],
                document_reference="DOC-PEO-001",
            ),
            EvidenceItem(
                evidence_type=EvidenceType.SURVEY,
                title="Stakeholder Survey – PEO Relevance",
                description="Survey responses from alumni, employers, and faculty on PEO adequacy",
                source="Annual Stakeholder Survey",
                relevance_score=0.88,
                criteria_mapping=[SARCriteria.CRITERIA_1],
            ),
        ]
        gaps: List[str] = []
        if not self.inp.program_outcomes:
            gaps.append("Program Educational Objectives not mapped to Program Outcomes")
        if self.inp.previous_sar_gaps:
            gaps += [g for g in self.inp.previous_sar_gaps if "vision" in g.lower() or "mission" in g.lower()]
        return SARSection(
            criteria=SARCriteria.CRITERIA_1,
            title="Vision, Mission and Program Educational Objectives",
            narrative=narrative,
            evidence_items=evidence,
            compliance_score=85.0 if not gaps else 70.0,
            gaps=gaps,
            strengths=[
                "Clearly articulated vision and mission",
                "PEOs reviewed periodically with stakeholder inputs",
            ],
        )

    def _build_criteria_2(self) -> SARSection:
        co_count = len(self.inp.course_outcomes)
        po_count = len(self.inp.program_outcomes)
        narrative = (
            f"{self._formal_intro('Program Curriculum and Teaching-Learning Processes')} "
            f"The curriculum has been designed to achieve {po_count} Program Outcomes through "
            f"{co_count} Course Outcomes distributed across all courses. The curriculum "
            "demonstrates a systematic mapping between course content, delivery methods, "
            "and expected learning outcomes consistent with NBA Tier-I requirements."
        )
        tables: List[Dict[str, Any]] = [
            {
                "table_id": "T2-1",
                "title": "Curriculum Structure Summary",
                "headers": ["Category", "Credits", "Percentage"],
                "rows": [
                    ["Theory Courses", "60", "50%"],
                    ["Laboratory Courses", "24", "20%"],
                    ["Project / Seminar", "18", "15%"],
                    ["Electives", "18", "15%"],
                ],
            }
        ]
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Approved Course Scheme and Syllabus",
                description="University-approved scheme of courses with syllabi",
                source="University Academic Section",
                relevance_score=1.0,
                criteria_mapping=[SARCriteria.CRITERIA_2],
                document_reference="DOC-SYL-001",
            ),
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="CO-PO Mapping Matrix",
                description="Correlation matrix mapping all Course Outcomes to Program Outcomes",
                source="Department",
                relevance_score=0.97,
                criteria_mapping=[SARCriteria.CRITERIA_2, SARCriteria.CRITERIA_3],
                document_reference="DOC-COPO-001",
            ),
        ]
        gaps: List[str] = []
        if co_count == 0:
            gaps.append("No Course Outcomes defined – CO-PO mapping cannot be established")
        return SARSection(
            criteria=SARCriteria.CRITERIA_2,
            title="Program Curriculum and Teaching-Learning Processes",
            narrative=narrative,
            evidence_items=evidence,
            tables=tables,
            compliance_score=82.0 if not gaps else 55.0,
            gaps=gaps,
            strengths=[
                "Outcome-based curriculum design",
                "Regular curriculum revision cycle",
            ],
        )

    def _build_criteria_3(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('Course Outcomes and Program Outcomes')} "
            f"{self._attainment_narrative()} "
            "The attainment is computed using a combination of direct assessment "
            "instruments (internal tests, end-semester examinations, assignments, "
            "and laboratory evaluations) and indirect instruments (exit surveys "
            "and alumni feedback)."
        )
        attainment = self.inp.attainment_data
        po_wise = attainment.get("po_wise_attainment", {})
        rows = [
            [f"PO{k}", f"{v:.1f}%", "✓" if v >= attainment.get("attainment_threshold", 60.0) else "✗"]
            for k, v in po_wise.items()
        ]
        tables = [
            {
                "table_id": "T3-1",
                "title": "PO Attainment Summary",
                "headers": ["Program Outcome", "Attainment (%)", "Target Met"],
                "rows": rows,
            }
        ]
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.ASSESSMENT,
                title="Direct Attainment Computation Sheets",
                description="Course-wise attainment computed from assessment marks",
                source="Department Examination Cell",
                relevance_score=1.0,
                criteria_mapping=[SARCriteria.CRITERIA_3],
            ),
            EvidenceItem(
                evidence_type=EvidenceType.SURVEY,
                title="Graduate Exit Survey",
                description="Indirect attainment through senior student exit surveys",
                source="Student Survey System",
                relevance_score=0.85,
                criteria_mapping=[SARCriteria.CRITERIA_3],
            ),
        ]
        compliance = min(
            100.0,
            attainment.get("direct_attainment_average", 60.0) * 1.1,
        )
        return SARSection(
            criteria=SARCriteria.CRITERIA_3,
            title="Course Outcomes and Program Outcomes",
            narrative=narrative,
            evidence_items=evidence,
            tables=tables,
            compliance_score=round(compliance, 2),
            gaps=[
                po
                for po, val in po_wise.items()
                if val < attainment.get("attainment_threshold", 60.0)
            ],
            strengths=["Systematic attainment computation", "Triangulated direct and indirect methods"],
        )

    def _build_criteria_4(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('Students Performance')} "
            f"{self._student_performance_narrative()}"
        )
        sp = self.inp.student_performance_data
        tables = [
            {
                "table_id": "T4-1",
                "title": "Student Performance Indicators",
                "headers": ["Metric", "Value"],
                "rows": [
                    ["Average Pass Rate", f"{sp.get('average_pass_rate', 0):.1f}%"],
                    ["Placement Rate", f"{sp.get('placement_rate', 0):.1f}%"],
                    ["Higher Studies", f"{sp.get('higher_studies_percentage', 0):.1f}%"],
                    ["Lateral Entry Students", str(sp.get("lateral_entry_count", 0))],
                    ["Scholarships Awarded", str(sp.get("scholarship_count", 0))],
                ],
            }
        ]
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.QUANTITATIVE,
                title="University Examination Results",
                description="Semester-wise pass rates for the last three years",
                source="University Examination Portal",
                relevance_score=1.0,
                criteria_mapping=[SARCriteria.CRITERIA_4],
                quantitative_value=sp.get("average_pass_rate", 0.0),
                unit="%",
            ),
            EvidenceItem(
                evidence_type=EvidenceType.QUANTITATIVE,
                title="Placement and Higher Studies Report",
                description="Annual placement statistics from Training & Placement Cell",
                source="T&P Cell",
                relevance_score=0.92,
                criteria_mapping=[SARCriteria.CRITERIA_4],
            ),
        ]
        compliance = min(100.0, sp.get("average_pass_rate", 60.0) * 1.05)
        return SARSection(
            criteria=SARCriteria.CRITERIA_4,
            title="Students Performance",
            narrative=narrative,
            evidence_items=evidence,
            tables=tables,
            compliance_score=round(compliance, 2),
            gaps=[],
            strengths=["Strong placement record", "Consistent pass rate trend"],
        )

    def _build_criteria_5(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('Faculty Information and Contributions')} "
            f"{self._faculty_narrative()}"
        )
        faculty = self.inp.faculty_data
        rows = [
            [
                f.get("name", "N/A"),
                f.get("designation", "N/A"),
                f.get("qualification", "N/A"),
                str(f.get("experience_years", 0)),
                str(f.get("publications_count", 0)),
            ]
            for f in faculty[:15]
        ]
        tables = [
            {
                "table_id": "T5-1",
                "title": "Faculty Details",
                "headers": ["Name", "Designation", "Qualification", "Experience (Yrs)", "Publications"],
                "rows": rows,
            }
        ]
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Faculty Credentials and Appointment Orders",
                description="Official appointment documents and qualification certificates",
                source="HR Department",
                relevance_score=1.0,
                criteria_mapping=[SARCriteria.CRITERIA_5],
            ),
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Faculty Research Publication List",
                description="Consolidated list of faculty publications in indexed journals",
                source="Department Research Cell",
                relevance_score=0.88,
                criteria_mapping=[SARCriteria.CRITERIA_5],
            ),
        ]
        total = len(faculty)
        phd = sum(1 for f in faculty if f.get("qualification") == "PhD")
        compliance = 70.0 + (phd / total * 30.0 if total else 0)
        return SARSection(
            criteria=SARCriteria.CRITERIA_5,
            title="Faculty Information and Contributions",
            narrative=narrative,
            evidence_items=evidence,
            tables=tables,
            compliance_score=round(min(100.0, compliance), 2),
            gaps=["PhD qualification below 50%" if total and phd / total < 0.5 else None],  # type: ignore[list-item]
            strengths=["Experienced faculty", "Active research contributions"],
        )

    def _build_criteria_6(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('Facilities and Technical Support')} "
            f"{self._infrastructure_narrative()}"
        )
        infra = self.inp.infrastructure_data
        tables = [
            {
                "table_id": "T6-1",
                "title": "Infrastructure Summary",
                "headers": ["Facility", "Count/Details"],
                "rows": [
                    ["Laboratories", str(infra.get("laboratory_count", 0))],
                    ["Licensed Software", str(infra.get("licensed_software_count", 0))],
                    ["Library Volumes", f"{infra.get('library_volumes', 0):,}"],
                    ["Computing Nodes", str(infra.get("computing_nodes", 0))],
                    ["Internet Bandwidth (Mbps)", str(infra.get("internet_bandwidth_mbps", 0))],
                ],
            }
        ]
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Laboratory Inventory Report",
                description="Detailed equipment inventory with purchase dates and values",
                source="Department Store",
                relevance_score=0.95,
                criteria_mapping=[SARCriteria.CRITERIA_6],
            ),
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="Software License Certificates",
                description="Valid software license copies for all licensed tools",
                source="IT Department",
                relevance_score=0.90,
                criteria_mapping=[SARCriteria.CRITERIA_6],
            ),
        ]
        lab_count = infra.get("laboratory_count", 0)
        compliance = min(100.0, 60.0 + lab_count * 3.0)
        return SARSection(
            criteria=SARCriteria.CRITERIA_6,
            title="Facilities and Technical Support",
            narrative=narrative,
            evidence_items=evidence,
            tables=tables,
            compliance_score=round(compliance, 2),
            gaps=[],
            strengths=["Well-equipped laboratories", "Adequate computing infrastructure"],
        )

    def _build_criteria_7(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('Continuous Improvement')} "
            f"{self._ci_narrative()}"
        )
        actions = self.inp.ci_actions
        rows = [
            [
                a.get("action_id", "N/A"),
                a.get("description", "N/A")[:60],
                a.get("status", "N/A"),
                a.get("target_date", "N/A"),
            ]
            for a in actions[:10]
        ]
        tables = [
            {
                "table_id": "T7-1",
                "title": "Continuous Improvement Actions",
                "headers": ["Action ID", "Description", "Status", "Target Date"],
                "rows": rows,
            }
        ]
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.DOCUMENTARY,
                title="CI Action Tracking Report",
                description="Documented CI actions with evidence of implementation",
                source="Quality Assurance Cell",
                relevance_score=0.95,
                criteria_mapping=[SARCriteria.CRITERIA_7],
            ),
        ]
        completed_ratio = (
            sum(1 for a in actions if a.get("status") == "completed") / len(actions)
            if actions
            else 0.5
        )
        compliance = round(60.0 + completed_ratio * 40.0, 2)
        return SARSection(
            criteria=SARCriteria.CRITERIA_7,
            title="Continuous Improvement",
            narrative=narrative,
            evidence_items=evidence,
            tables=tables,
            compliance_score=compliance,
            gaps=["Low CI action completion rate" if completed_ratio < 0.5 else None],  # type: ignore[list-item]
            strengths=["Structured CI process", "Gap-based action planning"],
        )

    def _build_criteria_8(self) -> SARSection:
        narrative = (
            f"{self._formal_intro('First Year Program')} "
            "The first-year program is designed to provide a strong foundation in "
            "basic sciences, engineering fundamentals, and communication skills. "
            "The curriculum integrates mandatory laboratory and workshop components "
            "to foster practical skills from the first semester."
        )
        sp = self.inp.student_performance_data
        first_year_pass = sp.get("first_year_pass_rate", sp.get("average_pass_rate", 70.0))
        evidence = [
            EvidenceItem(
                evidence_type=EvidenceType.QUANTITATIVE,
                title="First Year Examination Results",
                description="Pass rates for all first-year courses",
                source="University Examination Cell",
                relevance_score=0.92,
                criteria_mapping=[SARCriteria.CRITERIA_8],
                quantitative_value=first_year_pass,
                unit="%",
            ),
        ]
        compliance = min(100.0, first_year_pass * 1.05)
        return SARSection(
            criteria=SARCriteria.CRITERIA_8,
            title="First Year Program",
            narrative=narrative,
            evidence_items=evidence,
            compliance_score=round(compliance, 2),
            gaps=[],
            strengths=["Strong foundational curriculum", "Bridge programs for lateral entry"],
        )

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    _BUILDERS: Dict[SARCriteria, str] = {
        SARCriteria.CRITERIA_1: "_build_criteria_1",
        SARCriteria.CRITERIA_2: "_build_criteria_2",
        SARCriteria.CRITERIA_3: "_build_criteria_3",
        SARCriteria.CRITERIA_4: "_build_criteria_4",
        SARCriteria.CRITERIA_5: "_build_criteria_5",
        SARCriteria.CRITERIA_6: "_build_criteria_6",
        SARCriteria.CRITERIA_7: "_build_criteria_7",
        SARCriteria.CRITERIA_8: "_build_criteria_8",
    }

    def build_sections(self) -> List[SARSection]:
        sections: List[SARSection] = []
        for criteria in self._criteria_to_build:
            method_name = self._BUILDERS.get(criteria)
            if method_name:
                section: SARSection = getattr(self, method_name)()
                # clean None gaps
                section.gaps = [g for g in section.gaps if g is not None]
                sections.append(section)
        return sections

    def build_executive_summary(self, sections: List[SARSection]) -> str:
        avg_score = sum(s.compliance_score for s in sections) / len(sections) if sections else 0
        gap_count = sum(len(s.gaps) for s in sections)
        return (
            f"This Self-Assessment Report for the {self.inp.program_name} program at "
            f"{self.inp.institution_name} (Department of {self.inp.department}) has been "
            f"prepared for NBA Accreditation for the academic year {self.inp.accreditation_year}. "
            f"The report covers all eight NBA criteria. The overall compliance score is "
            f"{avg_score:.1f}%, with {gap_count} improvement areas identified across "
            f"{len(sections)} criteria sections. Evidence documentation, attainment analysis, "
            "and continuous improvement actions have been systematically recorded and presented "
            "in the following sections."
        )

    def collect_evidence_recommendations(self, sections: List[SARSection]) -> List[EvidenceItem]:
        all_evidence: List[EvidenceItem] = []
        seen: set = set()
        for section in sections:
            for item in section.evidence_items:
                if item.evidence_id not in seen:
                    all_evidence.append(item)
                    seen.add(item.evidence_id)
        return sorted(all_evidence, key=lambda e: e.relevance_score, reverse=True)

    def identify_missing_evidence(self, sections: List[SARSection]) -> List[str]:
        missing: List[str] = []
        for section in sections:
            if not section.evidence_items:
                missing.append(f"No evidence items for {section.criteria.value}")
            elif len(section.evidence_items) < 2:
                missing.append(f"Insufficient evidence for {section.criteria.value} – minimum 2 items recommended")
        return missing

    def compute_readiness(self, sections: List[SARSection]) -> float:
        if not sections:
            return 0.0
        avg_compliance = sum(s.compliance_score for s in sections) / len(sections)
        total_gaps = sum(len(s.gaps) for s in sections)
        gap_penalty = min(20.0, total_gaps * 2.0)
        return round(max(0.0, avg_compliance - gap_penalty), 2)


# ---------------------------------------------------------------------------
# SAR Agent
# ---------------------------------------------------------------------------


class SARAgent(BaseAgent):
    """
    NBA Self-Assessment Report (SAR) generation agent.

    Generates complete, PDF-ready SAR documents with evidence recommendations,
    narrative generation, and readiness assessment for NBA accreditation.
    """

    def __init__(self) -> None:
        metadata = AgentMetadata(
            agent_id="sar-agent-v1",
            name="SAR Agent",
            version="1.0.0",
            description=(
                "Generates NBA Self-Assessment Reports with section narratives, "
                "evidence recommendations, compliance scoring, and PDF-ready output."
            ),
            capabilities=[
                AgentCapability.GENERATION,
                AgentCapability.ANALYSIS,
                AgentCapability.REPORTING,
                AgentCapability.VALIDATION,
            ],
            author="NBA Enterprise AI Platform",
            tags=["sar", "accreditation", "nba", "report", "pdf"],
        )
        super().__init__(metadata=metadata)

    # ------------------------------------------------------------------
    # Validation hooks
    # ------------------------------------------------------------------

    async def _validate_input(self, request: AgentRequest) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        payload = request.payload

        if not payload.get("institution_name"):
            errors.append("institution_name is required")
        if not payload.get("program_name"):
            errors.append("program_name is required")
        if not payload.get("department"):
            errors.append("department is required")
        accreditation_year = payload.get("accreditation_year")
        if not accreditation_year or not isinstance(accreditation_year, int):
            errors.append("accreditation_year must be an integer")
        elif accreditation_year < 2000 or accreditation_year > 2100:
            errors.append("accreditation_year must be between 2000 and 2100")

        return len(errors) == 0, errors

    async def _validate_output(self, result: Any) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not isinstance(result, SARGenerationOutput):
            errors.append("Output must be SARGenerationOutput")
            return False, errors
        if not result.sar_document.sections:
            errors.append("SAR document contains no sections")
        if result.readiness_percentage < 0 or result.readiness_percentage > 100:
            errors.append("readiness_percentage out of range")
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
            institution=request.payload.get("institution_name"),
        )
        log.info("sar_agent.execute.start")

        try:
            inp = SARGenerationInput(**request.payload)
        except Exception as exc:
            log.error("sar_agent.input_parse_error", error=str(exc))
            return self._error_response(
                request=request,
                message=f"Input validation failed: {exc}",
            )

        builder = _SARBuilder(inp)

        log.info("sar_agent.building_sections")
        sections = await asyncio.get_event_loop().run_in_executor(
            None, builder.build_sections
        )

        executive_summary = builder.build_executive_summary(sections)
        evidence_recs = builder.collect_evidence_recommendations(sections)
        missing_evidence = builder.identify_missing_evidence(sections)
        readiness = builder.compute_readiness(sections)

        sar_doc = SARDocument(
            institution_name=inp.institution_name,
            program_name=inp.program_name,
            department=inp.department,
            accreditation_year=inp.accreditation_year,
            sections=sections,
            executive_summary=executive_summary,
            pdf_metadata={
                "title": f"SAR – {inp.program_name} – {inp.accreditation_year}",
                "author": inp.institution_name,
                "subject": "NBA Accreditation Self-Assessment Report",
                "keywords": "NBA, Accreditation, SAR, Outcome-Based Education",
                "creator": "NBA Enterprise AI Platform",
                "producer": "SAR Agent v1.0.0",
                "page_size": "A4",
                "orientation": "portrait",
                "margin_cm": 2.5,
            },
        )

        warnings: List[str] = []
        if readiness < 70.0:
            warnings.append(f"Accreditation readiness is below 70% ({readiness:.1f}%). Review critical gaps.")
        if missing_evidence:
            warnings.append(f"{len(missing_evidence)} criteria have insufficient evidence documentation.")

        output = SARGenerationOutput(
            sar_document=sar_doc,
            evidence_recommendations=evidence_recs,
            missing_evidence=missing_evidence,
            readiness_percentage=readiness,
            generation_warnings=warnings,
        )

        log.info(
            "sar_agent.execute.complete",
            section_count=len(sections),
            evidence_count=len(evidence_recs),
            readiness=readiness,
            overall_compliance=sar_doc.overall_compliance_score,
        )

        return AgentResponse(
            request_id=request.request_id,
            agent_id=self.metadata.agent_id,
            status=AgentStatus.SUCCESS,
            result=output.model_dump(),
            metadata={
                "section_count": len(sections),
                "evidence_count": len(evidence_recs),
                "readiness_percentage": readiness,
                "overall_compliance": sar_doc.overall_compliance_score,
                "missing_evidence_count": len(missing_evidence),
                "warnings": warnings,
            },
        )
