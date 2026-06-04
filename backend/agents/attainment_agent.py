"""
Attainment Agent - Direct, Indirect, and PO Attainment Computation.

Calculates CO attainment from assessment data, indirect attainment from
surveys, and computes PO attainment using CO-PO mapping weights.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.agents.base_agent import (
    AgentCategory,
    AgentMetadata,
    BaseAgent,
    RequestContext,
    ValidationResult,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AttainmentMethod(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    COMBINED = "combined"


class AttainmentGrade(str, Enum):
    EXCELLENT = "excellent"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"


class AssessmentType(str, Enum):
    INTERNAL_EXAM = "internal_exam"
    EXTERNAL_EXAM = "external_exam"
    ASSIGNMENT = "assignment"
    LAB_EXAM = "lab_exam"
    PROJECT = "project"
    QUIZ = "quiz"
    VIVA = "viva"
    SEMINAR = "seminar"


# ---------------------------------------------------------------------------
# Input Models
# ---------------------------------------------------------------------------


class StudentScore(BaseModel):
    student_id: str
    roll_number: str
    scores_by_question: Dict[str, float]
    total_scored: float
    total_maximum: float
    is_absent: bool = False


class QuestionCOMapping(BaseModel):
    question_id: str
    question_number: str
    co_ids: List[str]
    maximum_marks: float
    bloom_level: str
    weightage: float = 1.0


class AssessmentRecord(BaseModel):
    assessment_id: str
    assessment_type: AssessmentType
    assessment_name: str
    academic_year: str
    semester: int
    maximum_marks: float
    threshold_percentage: float = 40.0
    weightage: float
    question_co_mapping: List[QuestionCOMapping]
    student_scores: List[StudentScore]

    @field_validator("threshold_percentage")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if v < 20.0 or v > 80.0:
            raise ValueError("Threshold must be between 20% and 80%")
        return v

    @field_validator("weightage")
    @classmethod
    def validate_weightage(cls, v: float) -> float:
        if v <= 0.0 or v > 1.0:
            raise ValueError("Weightage must be between 0 and 1")
        return v


class IndirectSurveyResponse(BaseModel):
    student_id: str
    co_ratings: Dict[str, float]
    survey_type: str
    response_date: datetime


class COPOMappingWeight(BaseModel):
    co_id: str
    po_id: str
    weight: float
    normalized_weight: float


class AttainmentInput(BaseModel):
    course_id: str
    course_code: str
    department_id: str
    academic_year: str
    semester: int
    program_id: str
    direct_assessments: List[AssessmentRecord]
    indirect_survey_responses: Optional[List[IndirectSurveyResponse]] = None
    co_po_mapping_weights: List[COPOMappingWeight]
    co_ids: List[str]
    po_ids: List[str]
    direct_weight: float = 0.8
    indirect_weight: float = 0.2
    target_attainment_percentage: float = 60.0
    attainment_level_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"level_3": 70.0, "level_2": 60.0, "level_1": 50.0}
    )

    @model_validator(mode="after")
    def validate_weights(self) -> "AttainmentInput":
        if not math.isclose(self.direct_weight + self.indirect_weight, 1.0, abs_tol=0.001):
            raise ValueError("direct_weight + indirect_weight must equal 1.0")
        return self

    @field_validator("target_attainment_percentage")
    @classmethod
    def validate_target(cls, v: float) -> float:
        if v < 40.0 or v > 90.0:
            raise ValueError("Target attainment must be between 40% and 90%")
        return v


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------


class CODirectAttainment(BaseModel):
    co_id: str
    assessment_contributions: List[Dict[str, Any]]
    weighted_attainment_percentage: float
    students_above_threshold: int
    total_students: int
    attainment_percentage_of_students: float
    attainment_level: int
    grade: AttainmentGrade


class COIndirectAttainment(BaseModel):
    co_id: str
    avg_rating: float
    scaled_attainment: float
    response_count: int
    rating_distribution: Dict[str, int]


class COCombinedAttainment(BaseModel):
    co_id: str
    direct_attainment: float
    indirect_attainment: Optional[float]
    combined_attainment: float
    attainment_level: int
    grade: AttainmentGrade
    target_met: bool
    gap_percentage: float


class POAttainment(BaseModel):
    po_id: str
    contributing_cos: List[str]
    weighted_contributions: List[Dict[str, float]]
    attainment_percentage: float
    attainment_level: int
    grade: AttainmentGrade
    target_met: bool
    gap_percentage: float


class AttainmentSummary(BaseModel):
    total_cos: int
    cos_target_met: int
    cos_target_not_met: int
    cos_critical: int
    total_pos: int
    pos_target_met: int
    pos_target_not_met: int
    avg_co_attainment: float
    avg_po_attainment: float
    highest_co_attainment: Dict[str, float]
    lowest_co_attainment: Dict[str, float]
    highest_po_attainment: Dict[str, float]
    lowest_po_attainment: Dict[str, float]
    overall_attainment_score: float
    attainment_trend: str


class AttainmentAnalytics(BaseModel):
    course_id: str
    course_code: str
    academic_year: str
    semester: int
    co_direct_attainments: List[CODirectAttainment]
    co_indirect_attainments: Optional[List[COIndirectAttainment]]
    co_combined_attainments: List[COCombinedAttainment]
    po_attainments: List[POAttainment]
    summary: AttainmentSummary
    improvement_areas: List[str]
    strength_areas: List[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Attainment Agent
# ---------------------------------------------------------------------------


class AttainmentAgent(BaseAgent[AttainmentInput, AttainmentAnalytics]):
    """
    Attainment Agent for NBA OBE Platform.

    Computes direct attainment from exam scores, indirect attainment
    from surveys, combines them using configurable weights, and maps
    CO attainment to PO attainment using CO-PO mapping weights.
    """

    def _build_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_name="AttainmentAgent",
            agent_version="1.3.0",
            category=AgentCategory.ATTAINMENT,
            description=(
                "Computes CO attainment (direct + indirect), PO attainment from "
                "CO-PO mapping weights, and generates analytics for NBA compliance."
            ),
            supports_streaming=False,
            max_retries=2,
            timeout_seconds=180,
            langgraph_compatible=True,
        )

    async def _validate_input(self, input_data: AttainmentInput, context: RequestContext) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        total_weightage = sum(a.weightage for a in input_data.direct_assessments)
        if not math.isclose(total_weightage, 1.0, abs_tol=0.05):
            warnings.append(
                f"Assessment weightages sum to {total_weightage:.2f}; expected ~1.0. Normalization will be applied."
            )

        all_mapped_cos: set = set()
        for assessment in input_data.direct_assessments:
            for qm in assessment.question_co_mapping:
                all_mapped_cos.update(qm.co_ids)

        unmapped_cos = set(input_data.co_ids) - all_mapped_cos
        if unmapped_cos:
            warnings.append(f"COs not mapped to any assessment question: {', '.join(sorted(unmapped_cos))}")

        if not input_data.co_po_mapping_weights:
            errors.append("co_po_mapping_weights cannot be empty; PO attainment cannot be computed.")

        weight_co_ids = {w.co_id for w in input_data.co_po_mapping_weights}
        orphan_cos = set(input_data.co_ids) - weight_co_ids
        if orphan_cos:
            warnings.append(f"COs with no PO mapping weights: {', '.join(sorted(orphan_cos))}")

        for assessment in input_data.direct_assessments:
            if not assessment.student_scores:
                warnings.append(f"Assessment {assessment.assessment_name} has no student scores")
            if not assessment.question_co_mapping:
                errors.append(f"Assessment {assessment.assessment_name} has no question-CO mapping")

        if input_data.indirect_survey_responses:
            if len(input_data.indirect_survey_responses) < 5:
                warnings.append("Less than 5 survey responses. Indirect attainment may not be statistically reliable.")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    async def _execute_core(self, input_data: AttainmentInput, context: RequestContext) -> AttainmentAnalytics:
        bound_log = self._log.bind(
            request_id=context.request_id,
            course_id=input_data.course_id,
        )
        bound_log.info("attainment_computation_started")

        normalized_weights = self._normalize_assessment_weights(input_data.direct_assessments)

        direct_attainments = self._compute_direct_attainments(
            input_data.co_ids, input_data.direct_assessments, normalized_weights, input_data
        )
        self.increment_db_queries(len(input_data.direct_assessments))

        indirect_attainments: Optional[List[COIndirectAttainment]] = None
        if input_data.indirect_survey_responses:
            indirect_attainments = self._compute_indirect_attainments(
                input_data.co_ids, input_data.indirect_survey_responses
            )

        combined_attainments = self._compute_combined_attainments(
            direct_attainments, indirect_attainments, input_data
        )

        po_attainments = self._compute_po_attainments(
            combined_attainments, input_data.co_po_mapping_weights, input_data
        )

        summary = self._build_summary(combined_attainments, po_attainments, input_data)
        improvement_areas = self._identify_improvement_areas(combined_attainments, po_attainments, input_data)
        strength_areas = self._identify_strength_areas(combined_attainments, po_attainments, input_data)

        bound_log.info(
            "attainment_computation_completed",
            co_count=len(combined_attainments),
            po_count=len(po_attainments),
            avg_co_attainment=summary.avg_co_attainment,
        )

        return AttainmentAnalytics(
            course_id=input_data.course_id,
            course_code=input_data.course_code,
            academic_year=input_data.academic_year,
            semester=input_data.semester,
            co_direct_attainments=direct_attainments,
            co_indirect_attainments=indirect_attainments,
            co_combined_attainments=combined_attainments,
            po_attainments=po_attainments,
            summary=summary,
            improvement_areas=improvement_areas,
            strength_areas=strength_areas,
        )

    # ------------------------------------------------------------------
    # Direct Attainment
    # ------------------------------------------------------------------

    def _normalize_assessment_weights(self, assessments: List[AssessmentRecord]) -> Dict[str, float]:
        total = sum(a.weightage for a in assessments)
        if total == 0:
            return {a.assessment_id: 1.0 / len(assessments) for a in assessments}
        return {a.assessment_id: a.weightage / total for a in assessments}

    def _compute_direct_attainments(
        self,
        co_ids: List[str],
        assessments: List[AssessmentRecord],
        normalized_weights: Dict[str, float],
        input_data: AttainmentInput,
    ) -> List[CODirectAttainment]:
        results: List[CODirectAttainment] = []

        for co_id in co_ids:
            contributions: List[Dict[str, Any]] = []
            weighted_total = 0.0
            total_weight = 0.0

            for assessment in assessments:
                co_questions = [
                    qm for qm in assessment.question_co_mapping if co_id in qm.co_ids
                ]
                if not co_questions:
                    continue

                co_max_marks = sum(qm.maximum_marks for qm in co_questions)
                if co_max_marks == 0:
                    continue

                present_students = [s for s in assessment.student_scores if not s.is_absent]
                if not present_students:
                    continue

                students_above = 0
                for student in present_students:
                    student_co_score = sum(
                        student.scores_by_question.get(qm.question_id, 0.0)
                        for qm in co_questions
                    )
                    pct = (student_co_score / co_max_marks) * 100
                    if pct >= assessment.threshold_percentage:
                        students_above += 1

                pct_above = (students_above / len(present_students)) * 100
                aw = normalized_weights.get(assessment.assessment_id, 0.0)
                weighted_total += pct_above * aw
                total_weight += aw

                contributions.append({
                    "assessment_id": assessment.assessment_id,
                    "assessment_name": assessment.assessment_name,
                    "assessment_type": assessment.assessment_type.value,
                    "students_above_threshold": students_above,
                    "total_students": len(present_students),
                    "percentage_above": round(pct_above, 2),
                    "weight": round(aw, 4),
                    "weighted_contribution": round(pct_above * aw, 4),
                })

            final_pct = weighted_total / total_weight if total_weight > 0 else 0.0
            level = self._attainment_level(final_pct, input_data.attainment_level_thresholds)
            grade = self._attainment_grade(final_pct, input_data.target_attainment_percentage)

            total_students = len(
                set(
                    s.student_id
                    for a in assessments
                    for s in a.student_scores
                    if not s.is_absent
                )
            )

            results.append(
                CODirectAttainment(
                    co_id=co_id,
                    assessment_contributions=contributions,
                    weighted_attainment_percentage=round(final_pct, 2),
                    students_above_threshold=round(final_pct * total_students / 100),
                    total_students=total_students,
                    attainment_percentage_of_students=round(final_pct, 2),
                    attainment_level=level,
                    grade=grade,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Indirect Attainment
    # ------------------------------------------------------------------

    def _compute_indirect_attainments(
        self,
        co_ids: List[str],
        survey_responses: List[IndirectSurveyResponse],
    ) -> List[COIndirectAttainment]:
        results: List[COIndirectAttainment] = []

        for co_id in co_ids:
            ratings = [
                resp.co_ratings[co_id]
                for resp in survey_responses
                if co_id in resp.co_ratings
            ]
            if not ratings:
                results.append(
                    COIndirectAttainment(
                        co_id=co_id,
                        avg_rating=0.0,
                        scaled_attainment=0.0,
                        response_count=0,
                        rating_distribution={},
                    )
                )
                continue

            avg = statistics.mean(ratings)
            scaled = (avg / 5.0) * 100.0

            distribution: Dict[str, int] = {}
            for r in ratings:
                bucket = str(round(r))
                distribution[bucket] = distribution.get(bucket, 0) + 1

            results.append(
                COIndirectAttainment(
                    co_id=co_id,
                    avg_rating=round(avg, 3),
                    scaled_attainment=round(scaled, 2),
                    response_count=len(ratings),
                    rating_distribution=distribution,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Combined Attainment
    # ------------------------------------------------------------------

    def _compute_combined_attainments(
        self,
        direct: List[CODirectAttainment],
        indirect: Optional[List[COIndirectAttainment]],
        input_data: AttainmentInput,
    ) -> List[COCombinedAttainment]:
        indirect_map: Dict[str, COIndirectAttainment] = {}
        if indirect:
            indirect_map = {ia.co_id: ia for ia in indirect}

        results: List[COCombinedAttainment] = []
        for da in direct:
            ind_att: Optional[float] = None
            if da.co_id in indirect_map:
                ind_att = indirect_map[da.co_id].scaled_attainment

            if ind_att is not None:
                combined = (da.weighted_attainment_percentage * input_data.direct_weight) + (
                    ind_att * input_data.indirect_weight
                )
            else:
                combined = da.weighted_attainment_percentage

            level = self._attainment_level(combined, input_data.attainment_level_thresholds)
            grade = self._attainment_grade(combined, input_data.target_attainment_percentage)
            target_met = combined >= input_data.target_attainment_percentage
            gap = max(0.0, input_data.target_attainment_percentage - combined)

            results.append(
                COCombinedAttainment(
                    co_id=da.co_id,
                    direct_attainment=da.weighted_attainment_percentage,
                    indirect_attainment=ind_att,
                    combined_attainment=round(combined, 2),
                    attainment_level=level,
                    grade=grade,
                    target_met=target_met,
                    gap_percentage=round(gap, 2),
                )
            )

        return results

    # ------------------------------------------------------------------
    # PO Attainment
    # ------------------------------------------------------------------

    def _compute_po_attainments(
        self,
        co_combined: List[COCombinedAttainment],
        weights: List[COPOMappingWeight],
        input_data: AttainmentInput,
    ) -> List[POAttainment]:
        co_att_map: Dict[str, float] = {ca.co_id: ca.combined_attainment for ca in co_combined}

        po_groups: Dict[str, List[COPOMappingWeight]] = {}
        for w in weights:
            if w.po_id not in po_groups:
                po_groups[w.po_id] = []
            po_groups[w.po_id].append(w)

        results: List[POAttainment] = []
        for po_id in input_data.po_ids:
            group = po_groups.get(po_id, [])
            if not group:
                results.append(
                    POAttainment(
                        po_id=po_id,
                        contributing_cos=[],
                        weighted_contributions=[],
                        attainment_percentage=0.0,
                        attainment_level=0,
                        grade=AttainmentGrade.CRITICAL,
                        target_met=False,
                        gap_percentage=input_data.target_attainment_percentage,
                    )
                )
                continue

            total_weight = sum(w.normalized_weight for w in group)
            if total_weight == 0:
                total_weight = 1.0

            weighted_sum = 0.0
            contributions: List[Dict[str, float]] = []
            for w in group:
                co_att = co_att_map.get(w.co_id, 0.0)
                contrib = (co_att * w.normalized_weight) / total_weight
                weighted_sum += contrib
                contributions.append({
                    "co_id_ref": w.co_id,
                    "co_attainment": co_att,
                    "mapping_weight": w.normalized_weight,
                    "contribution": round(contrib, 4),
                })

            po_att = weighted_sum
            level = self._attainment_level(po_att, input_data.attainment_level_thresholds)
            grade = self._attainment_grade(po_att, input_data.target_attainment_percentage)
            target_met = po_att >= input_data.target_attainment_percentage
            gap = max(0.0, input_data.target_attainment_percentage - po_att)

            results.append(
                POAttainment(
                    po_id=po_id,
                    contributing_cos=[w.co_id for w in group],
                    weighted_contributions=contributions,
                    attainment_percentage=round(po_att, 2),
                    attainment_level=level,
                    grade=grade,
                    target_met=target_met,
                    gap_percentage=round(gap, 2),
                )
            )

        return results

    # ------------------------------------------------------------------
    # Summary & Analytics
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        co_attainments: List[COCombinedAttainment],
        po_attainments: List[POAttainment],
        input_data: AttainmentInput,
    ) -> AttainmentSummary:
        co_met = [ca for ca in co_attainments if ca.target_met]
        co_critical = [ca for ca in co_attainments if ca.grade == AttainmentGrade.CRITICAL]
        po_met = [pa for pa in po_attainments if pa.target_met]

        co_values = [ca.combined_attainment for ca in co_attainments]
        po_values = [pa.attainment_percentage for pa in po_attainments]

        avg_co = statistics.mean(co_values) if co_values else 0.0
        avg_po = statistics.mean(po_values) if po_values else 0.0

        best_co = max(co_attainments, key=lambda ca: ca.combined_attainment, default=None)
        worst_co = min(co_attainments, key=lambda ca: ca.combined_attainment, default=None)
        best_po = max(po_attainments, key=lambda pa: pa.attainment_percentage, default=None)
        worst_po = min(po_attainments, key=lambda pa: pa.attainment_percentage, default=None)

        overall = (avg_co * 0.5 + avg_po * 0.5)

        if overall >= input_data.target_attainment_percentage + 10:
            trend = "improving"
        elif overall >= input_data.target_attainment_percentage:
            trend = "on_target"
        elif overall >= input_data.target_attainment_percentage - 10:
            trend = "slightly_below_target"
        else:
            trend = "needs_significant_improvement"

        return AttainmentSummary(
            total_cos=len(co_attainments),
            cos_target_met=len(co_met),
            cos_target_not_met=len(co_attainments) - len(co_met),
            cos_critical=len(co_critical),
            total_pos=len(po_attainments),
            pos_target_met=len(po_met),
            pos_target_not_met=len(po_attainments) - len(po_met),
            avg_co_attainment=round(avg_co, 2),
            avg_po_attainment=round(avg_po, 2),
            highest_co_attainment={best_co.co_id: best_co.combined_attainment} if best_co else {},
            lowest_co_attainment={worst_co.co_id: worst_co.combined_attainment} if worst_co else {},
            highest_po_attainment={best_po.po_id: best_po.attainment_percentage} if best_po else {},
            lowest_po_attainment={worst_po.po_id: worst_po.attainment_percentage} if worst_po else {},
            overall_attainment_score=round(overall, 2),
            attainment_trend=trend,
        )

    def _identify_improvement_areas(
        self,
        co_attainments: List[COCombinedAttainment],
        po_attainments: List[POAttainment],
        input_data: AttainmentInput,
    ) -> List[str]:
        areas: List[str] = []
        for ca in sorted(co_attainments, key=lambda x: x.combined_attainment):
            if not ca.target_met:
                areas.append(
                    f"{ca.co_id}: Attainment {ca.combined_attainment:.1f}% is {ca.gap_percentage:.1f}% below target."
                )
        for pa in sorted(po_attainments, key=lambda x: x.attainment_percentage):
            if not pa.target_met:
                areas.append(
                    f"{pa.po_id}: PO attainment {pa.attainment_percentage:.1f}% is {pa.gap_percentage:.1f}% below target."
                )
        return areas[:10]

    def _identify_strength_areas(
        self,
        co_attainments: List[COCombinedAttainment],
        po_attainments: List[POAttainment],
        input_data: AttainmentInput,
    ) -> List[str]:
        areas: List[str] = []
        for ca in sorted(co_attainments, key=lambda x: x.combined_attainment, reverse=True):
            if ca.target_met:
                areas.append(
                    f"{ca.co_id}: Strong attainment at {ca.combined_attainment:.1f}% (target: {input_data.target_attainment_percentage}%)."
                )
        for pa in sorted(po_attainments, key=lambda x: x.attainment_percentage, reverse=True):
            if pa.target_met:
                areas.append(
                    f"{pa.po_id}: PO achieved {pa.attainment_percentage:.1f}% (target: {input_data.target_attainment_percentage}%)."
                )
        return areas[:10]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _attainment_level(self, pct: float, thresholds: Dict[str, float]) -> int:
        if pct >= thresholds.get("level_3", 70.0):
            return 3
        elif pct >= thresholds.get("level_2", 60.0):
            return 2
        elif pct >= thresholds.get("level_1", 50.0):
            return 1
        return 0

    def _attainment_grade(self, pct: float, target: float) -> AttainmentGrade:
        if pct >= target + 10:
            return AttainmentGrade.EXCELLENT
        elif pct >= target:
            return AttainmentGrade.SATISFACTORY
        elif pct >= target - 15:
            return AttainmentGrade.NEEDS_IMPROVEMENT
        return AttainmentGrade.CRITICAL
