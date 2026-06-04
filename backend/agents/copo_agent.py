"""
CO-PO Agent - Course Outcome to Program Outcome Mapping Agent.

Handles CO-PO mapping generation, correlation scoring,
mapping validation, and recommendations for NBA accreditation.
"""

from __future__ import annotations

import math
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
# Domain Enums
# ---------------------------------------------------------------------------


class CorrelationLevel(str, Enum):
    NO_CORRELATION = "0"
    LOW = "1"
    MEDIUM = "2"
    HIGH = "3"


class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


BLOOM_WEIGHTS: Dict[BloomLevel, float] = {
    BloomLevel.REMEMBER: 1.0,
    BloomLevel.UNDERSTAND: 2.0,
    BloomLevel.APPLY: 3.0,
    BloomLevel.ANALYZE: 4.0,
    BloomLevel.EVALUATE: 5.0,
    BloomLevel.CREATE: 6.0,
}


# ---------------------------------------------------------------------------
# Input / Output Models
# ---------------------------------------------------------------------------


class CourseOutcome(BaseModel):
    co_id: str
    co_number: int
    description: str
    bloom_level: BloomLevel
    unit_references: List[int] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    @field_validator("co_number")
    @classmethod
    def validate_co_number(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("CO number must be between 1 and 20")
        return v


class ProgramOutcome(BaseModel):
    po_id: str
    po_number: int
    code: str
    description: str
    domain: str
    keywords: List[str] = Field(default_factory=list)

    @field_validator("po_number")
    @classmethod
    def validate_po_number(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError("PO number must be between 1 and 12 (NBA standard)")
        return v


class COPOInput(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    department_id: str
    academic_year: str
    semester: int
    program_id: str
    course_outcomes: List[CourseOutcome]
    program_outcomes: List[ProgramOutcome]
    existing_mapping: Optional[Dict[str, Dict[str, str]]] = None
    include_pso: bool = False
    program_specific_outcomes: Optional[List[ProgramOutcome]] = None

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: int) -> int:
        if v < 1 or v > 8:
            raise ValueError("Semester must be between 1 and 8")
        return v

    @field_validator("course_outcomes")
    @classmethod
    def validate_course_outcomes(cls, v: List[CourseOutcome]) -> List[CourseOutcome]:
        if not v:
            raise ValueError("At least one course outcome is required")
        if len(v) > 20:
            raise ValueError("Maximum 20 course outcomes allowed")
        return v

    @field_validator("program_outcomes")
    @classmethod
    def validate_program_outcomes(cls, v: List[ProgramOutcome]) -> List[ProgramOutcome]:
        if len(v) < 3:
            raise ValueError("Minimum 3 program outcomes required")
        return v


class COPOMappingEntry(BaseModel):
    co_id: str
    co_number: int
    po_id: str
    po_number: int
    po_code: str
    correlation_level: CorrelationLevel
    correlation_score: float
    justification: str
    bloom_contribution: float
    keyword_overlap_count: int
    is_validated: bool = False


class AttainmentWeight(BaseModel):
    co_id: str
    po_id: str
    weight: float
    normalized_weight: float


class MappingStatistics(BaseModel):
    total_mappings: int
    high_correlation_count: int
    medium_correlation_count: int
    low_correlation_count: int
    no_correlation_count: int
    coverage_percentage: float
    avg_correlation_per_co: float
    avg_correlation_per_po: float
    po_coverage_count: int
    uncovered_pos: List[str]
    strongest_co_po_pair: Optional[str]
    weakest_covered_pair: Optional[str]


class COPOMappingRecommendation(BaseModel):
    recommendation_id: str
    type: str
    priority: str
    target_co: Optional[str]
    target_po: Optional[str]
    current_level: Optional[str]
    suggested_level: Optional[str]
    rationale: str
    impact: str


class COPOMatrix(BaseModel):
    co_id: str
    co_number: int
    po_correlations: Dict[str, CorrelationLevel]
    pso_correlations: Optional[Dict[str, CorrelationLevel]] = None
    row_average: float


class COPOOutput(BaseModel):
    course_id: str
    course_code: str
    mapping_entries: List[COPOMappingEntry]
    matrix: List[COPOMatrix]
    attainment_weights: List[AttainmentWeight]
    statistics: MappingStatistics
    recommendations: List[COPOMappingRecommendation]
    overall_quality_score: float
    nba_compliance: bool
    compliance_notes: List[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# COPO Agent
# ---------------------------------------------------------------------------


class COPOAgent(BaseAgent[COPOInput, COPOOutput]):
    """
    CO-PO Mapping Agent for NBA Accreditation Platform.

    Generates and validates Course Outcome to Program Outcome mappings
    using keyword analysis, Bloom's taxonomy weighting, and domain alignment.
    """

    def _build_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_name="COPOAgent",
            agent_version="1.2.0",
            category=AgentCategory.MAPPING,
            description=(
                "Generates CO-PO correlation mappings using Bloom's taxonomy weighting, "
                "keyword overlap analysis, and domain alignment scoring for NBA compliance."
            ),
            supports_streaming=False,
            max_retries=2,
            timeout_seconds=120,
            langgraph_compatible=True,
        )

    async def _validate_input(self, input_data: COPOInput, context: RequestContext) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        co_numbers = [co.co_number for co in input_data.course_outcomes]
        if len(co_numbers) != len(set(co_numbers)):
            errors.append("Duplicate CO numbers found in course_outcomes")

        po_numbers = [po.po_number for po in input_data.program_outcomes]
        if len(po_numbers) != len(set(po_numbers)):
            errors.append("Duplicate PO numbers found in program_outcomes")

        if len(input_data.course_outcomes) < 3:
            warnings.append("NBA recommends minimum 5 course outcomes for meaningful mapping")

        bloom_levels = {co.bloom_level for co in input_data.course_outcomes}
        higher_order = {BloomLevel.APPLY, BloomLevel.ANALYZE, BloomLevel.EVALUATE, BloomLevel.CREATE}
        if not bloom_levels.intersection(higher_order):
            warnings.append("No higher-order Bloom's taxonomy levels (Apply and above) detected")

        if input_data.include_pso and not input_data.program_specific_outcomes:
            errors.append("include_pso is True but program_specific_outcomes is empty")

        if input_data.existing_mapping:
            for co_key, po_map in input_data.existing_mapping.items():
                for po_key, level in po_map.items():
                    if level not in {"0", "1", "2", "3"}:
                        errors.append(f"Invalid correlation level '{level}' in existing_mapping[{co_key}][{po_key}]")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    async def _execute_core(self, input_data: COPOInput, context: RequestContext) -> COPOOutput:
        bound_log = self._log.bind(
            request_id=context.request_id,
            course_id=input_data.course_id,
        )
        bound_log.info("copo_mapping_started", co_count=len(input_data.course_outcomes))

        mapping_entries: List[COPOMappingEntry] = []
        for co in input_data.course_outcomes:
            for po in input_data.program_outcomes:
                entry = self._compute_mapping_entry(co, po, input_data.existing_mapping)
                mapping_entries.append(entry)
                self.increment_db_queries()

        matrix = self._build_matrix(input_data.course_outcomes, input_data.program_outcomes, mapping_entries)
        attainment_weights = self._compute_attainment_weights(mapping_entries)
        statistics = self._compute_statistics(
            mapping_entries, input_data.course_outcomes, input_data.program_outcomes
        )
        recommendations = self._generate_recommendations(statistics, mapping_entries, input_data)
        quality_score, compliance, compliance_notes = self._assess_nba_compliance(statistics, input_data)

        bound_log.info(
            "copo_mapping_completed",
            total_mappings=len(mapping_entries),
            quality_score=quality_score,
            nba_compliance=compliance,
        )

        return COPOOutput(
            course_id=input_data.course_id,
            course_code=input_data.course_code,
            mapping_entries=mapping_entries,
            matrix=matrix,
            attainment_weights=attainment_weights,
            statistics=statistics,
            recommendations=recommendations,
            overall_quality_score=quality_score,
            nba_compliance=compliance,
            compliance_notes=compliance_notes,
        )

    # ------------------------------------------------------------------
    # Internal computation methods
    # ------------------------------------------------------------------

    def _compute_mapping_entry(
        self,
        co: CourseOutcome,
        po: ProgramOutcome,
        existing_mapping: Optional[Dict[str, Dict[str, str]]],
    ) -> COPOMappingEntry:
        # Check for existing manual mapping first
        if existing_mapping:
            co_key = f"CO{co.co_number}"
            po_key = f"PO{po.po_number}"
            if co_key in existing_mapping and po_key in existing_mapping[co_key]:
                level_str = existing_mapping[co_key][po_key]
                level = CorrelationLevel(level_str)
                score = float(level_str)
                return COPOMappingEntry(
                    co_id=co.co_id,
                    co_number=co.co_number,
                    po_id=po.po_id,
                    po_number=po.po_number,
                    po_code=po.code,
                    correlation_level=level,
                    correlation_score=score,
                    justification="Manually validated by faculty",
                    bloom_contribution=BLOOM_WEIGHTS.get(co.bloom_level, 1.0),
                    keyword_overlap_count=self._keyword_overlap(co.keywords, po.keywords),
                    is_validated=True,
                )

        keyword_overlap = self._keyword_overlap(co.keywords, po.keywords)
        bloom_weight = BLOOM_WEIGHTS.get(co.bloom_level, 1.0)
        domain_score = self._domain_alignment_score(co, po)
        raw_score = self._compute_raw_score(keyword_overlap, bloom_weight, domain_score, co, po)
        level, score = self._quantize_to_level(raw_score)
        justification = self._generate_justification(co, po, level, keyword_overlap, domain_score)

        return COPOMappingEntry(
            co_id=co.co_id,
            co_number=co.co_number,
            po_id=po.po_id,
            po_number=po.po_number,
            po_code=po.code,
            correlation_level=level,
            correlation_score=score,
            justification=justification,
            bloom_contribution=bloom_weight,
            keyword_overlap_count=keyword_overlap,
            is_validated=False,
        )

    def _keyword_overlap(self, co_keywords: List[str], po_keywords: List[str]) -> int:
        co_set = {k.lower().strip() for k in co_keywords}
        po_set = {k.lower().strip() for k in po_keywords}
        return len(co_set.intersection(po_set))

    def _domain_alignment_score(self, co: CourseOutcome, po: ProgramOutcome) -> float:
        domain_keyword_map: Dict[str, List[str]] = {
            "engineering_knowledge": ["theory", "principles", "concepts", "fundamentals", "knowledge"],
            "problem_analysis": ["analyze", "problem", "complex", "identify", "formulate"],
            "design": ["design", "develop", "solution", "system", "component"],
            "investigation": ["research", "investigate", "experiment", "interpret", "data"],
            "modern_tools": ["tools", "software", "technology", "techniques", "resources"],
            "engineer_society": ["society", "safety", "environmental", "sustainability", "context"],
            "ethics": ["ethical", "professional", "responsibility", "norms", "conduct"],
            "communication": ["communicate", "report", "present", "documentation", "write"],
            "project_management": ["management", "project", "economics", "finance", "teamwork"],
            "lifelong_learning": ["learning", "adapt", "contemporary", "independent", "update"],
        }

        domain_lower = po.domain.lower().replace(" ", "_")
        domain_keywords = domain_keyword_map.get(domain_lower, [])
        co_desc_lower = co.description.lower()
        hits = sum(1 for kw in domain_keywords if kw in co_desc_lower)

        if not domain_keywords:
            return 0.3
        return min(1.0, hits / max(len(domain_keywords), 1))

    def _compute_raw_score(
        self,
        keyword_overlap: int,
        bloom_weight: float,
        domain_score: float,
        co: CourseOutcome,
        po: ProgramOutcome,
    ) -> float:
        keyword_contrib = min(1.0, keyword_overlap / 3.0) * 0.35
        bloom_contrib = (bloom_weight / 6.0) * 0.25
        domain_contrib = domain_score * 0.40
        raw = keyword_contrib + bloom_contrib + domain_contrib
        return min(3.0, raw * 3.0)

    def _quantize_to_level(self, raw_score: float) -> Tuple[CorrelationLevel, float]:
        if raw_score >= 2.5:
            return CorrelationLevel.HIGH, 3.0
        elif raw_score >= 1.5:
            return CorrelationLevel.MEDIUM, 2.0
        elif raw_score >= 0.5:
            return CorrelationLevel.LOW, 1.0
        else:
            return CorrelationLevel.NO_CORRELATION, 0.0

    def _generate_justification(
        self,
        co: CourseOutcome,
        po: ProgramOutcome,
        level: CorrelationLevel,
        keyword_overlap: int,
        domain_score: float,
    ) -> str:
        if level == CorrelationLevel.NO_CORRELATION:
            return f"CO{co.co_number} focuses on {co.bloom_level.value}-level {co.description[:60]}... which has no direct alignment with PO{po.po_number} ({po.domain})."
        bloom_desc = f"Bloom's {co.bloom_level.value} level"
        kw_desc = f"{keyword_overlap} shared keyword(s)" if keyword_overlap > 0 else "domain alignment"
        level_map = {
            CorrelationLevel.LOW: "partially supports",
            CorrelationLevel.MEDIUM: "moderately supports",
            CorrelationLevel.HIGH: "strongly supports",
        }
        verb = level_map.get(level, "relates to")
        return (
            f"CO{co.co_number} ({bloom_desc}) {verb} PO{po.po_number} through {kw_desc} "
            f"and domain alignment score of {domain_score:.2f}."
        )

    def _build_matrix(
        self,
        course_outcomes: List[CourseOutcome],
        program_outcomes: List[ProgramOutcome],
        entries: List[COPOMappingEntry],
    ) -> List[COPOMatrix]:
        entry_map: Dict[str, Dict[str, CorrelationLevel]] = {}
        for entry in entries:
            co_key = entry.co_id
            po_key = entry.po_code
            if co_key not in entry_map:
                entry_map[co_key] = {}
            entry_map[co_key][po_key] = entry.correlation_level

        matrix: List[COPOMatrix] = []
        for co in course_outcomes:
            po_corrs = entry_map.get(co.co_id, {})
            scores = [float(v.value) for v in po_corrs.values()]
            row_avg = sum(scores) / len(scores) if scores else 0.0
            matrix.append(
                COPOMatrix(
                    co_id=co.co_id,
                    co_number=co.co_number,
                    po_correlations=po_corrs,
                    row_average=round(row_avg, 2),
                )
            )
        return matrix

    def _compute_attainment_weights(self, entries: List[COPOMappingEntry]) -> List[AttainmentWeight]:
        po_totals: Dict[str, float] = {}
        for entry in entries:
            if entry.correlation_score > 0:
                key = entry.po_id
                po_totals[key] = po_totals.get(key, 0.0) + entry.correlation_score

        weights: List[AttainmentWeight] = []
        for entry in entries:
            if entry.correlation_score > 0:
                total = po_totals.get(entry.po_id, 1.0)
                normalized = entry.correlation_score / total if total > 0 else 0.0
                weights.append(
                    AttainmentWeight(
                        co_id=entry.co_id,
                        po_id=entry.po_id,
                        weight=entry.correlation_score,
                        normalized_weight=round(normalized, 4),
                    )
                )
        return weights

    def _compute_statistics(
        self,
        entries: List[COPOMappingEntry],
        cos: List[CourseOutcome],
        pos: List[ProgramOutcome],
    ) -> MappingStatistics:
        high = sum(1 for e in entries if e.correlation_level == CorrelationLevel.HIGH)
        medium = sum(1 for e in entries if e.correlation_level == CorrelationLevel.MEDIUM)
        low = sum(1 for e in entries if e.correlation_level == CorrelationLevel.LOW)
        none = sum(1 for e in entries if e.correlation_level == CorrelationLevel.NO_CORRELATION)

        total = len(entries)
        covered_po_ids = {e.po_id for e in entries if e.correlation_score > 0}
        all_po_ids = {po.po_id for po in pos}
        uncovered_po_ids = all_po_ids - covered_po_ids
        uncovered_labels = [f"PO{po.po_number}" for po in pos if po.po_id in uncovered_po_ids]

        coverage_pct = (len(covered_po_ids) / len(pos) * 100) if pos else 0.0

        co_scores: Dict[str, List[float]] = {}
        po_scores: Dict[str, List[float]] = {}
        for e in entries:
            co_scores.setdefault(e.co_id, []).append(e.correlation_score)
            po_scores.setdefault(e.po_id, []).append(e.correlation_score)

        avg_per_co = sum(sum(v) / len(v) for v in co_scores.values()) / len(co_scores) if co_scores else 0.0
        avg_per_po = sum(sum(v) / len(v) for v in po_scores.values()) / len(po_scores) if po_scores else 0.0

        strongest = max(entries, key=lambda e: e.correlation_score, default=None)
        weakest_covered = min(
            (e for e in entries if e.correlation_score > 0),
            key=lambda e: e.correlation_score,
            default=None,
        )

        return MappingStatistics(
            total_mappings=total,
            high_correlation_count=high,
            medium_correlation_count=medium,
            low_correlation_count=low,
            no_correlation_count=none,
            coverage_percentage=round(coverage_pct, 2),
            avg_correlation_per_co=round(avg_per_co, 3),
            avg_correlation_per_po=round(avg_per_po, 3),
            po_coverage_count=len(covered_po_ids),
            uncovered_pos=uncovered_labels,
            strongest_co_po_pair=f"CO{strongest.co_number}-{strongest.po_code}" if strongest else None,
            weakest_covered_pair=f"CO{weakest_covered.co_number}-{weakest_covered.po_code}" if weakest_covered else None,
        )

    def _generate_recommendations(
        self,
        stats: MappingStatistics,
        entries: List[COPOMappingEntry],
        input_data: COPOInput,
    ) -> List[COPOMappingRecommendation]:
        recs: List[COPOMappingRecommendation] = []
        rec_id = 1

        if stats.uncovered_pos:
            recs.append(
                COPOMappingRecommendation(
                    recommendation_id=f"REC-{rec_id:03d}",
                    type="coverage_gap",
                    priority="high",
                    target_co=None,
                    target_po=", ".join(stats.uncovered_pos),
                    current_level="0",
                    suggested_level="1",
                    rationale=f"Program outcomes {', '.join(stats.uncovered_pos)} have no CO mapping. NBA requires comprehensive PO coverage.",
                    impact="Non-compliance risk for NBA accreditation criterion 3",
                )
            )
            rec_id += 1

        if stats.coverage_percentage < 70:
            recs.append(
                COPOMappingRecommendation(
                    recommendation_id=f"REC-{rec_id:03d}",
                    type="low_coverage",
                    priority="high",
                    target_co=None,
                    target_po=None,
                    current_level=f"{stats.coverage_percentage:.1f}%",
                    suggested_level=">=80%",
                    rationale="CO-PO coverage below 70% indicates insufficient program alignment.",
                    impact="May result in SAR review findings during NBA visit",
                )
            )
            rec_id += 1

        for co in input_data.course_outcomes:
            co_entries = [e for e in entries if e.co_id == co.co_id and e.correlation_score > 0]
            if len(co_entries) < 2:
                recs.append(
                    COPOMappingRecommendation(
                        recommendation_id=f"REC-{rec_id:03d}",
                        type="sparse_co_mapping",
                        priority="medium",
                        target_co=f"CO{co.co_number}",
                        target_po=None,
                        current_level=f"{len(co_entries)} PO(s)",
                        suggested_level=">=3 POs",
                        rationale=f"CO{co.co_number} maps to fewer than 2 POs. Broaden the CO scope or refine keywords.",
                        impact="Reduces attainment computation accuracy",
                    )
                )
                rec_id += 1

        high_bloom_cos = [co for co in input_data.course_outcomes if co.bloom_level in {BloomLevel.EVALUATE, BloomLevel.CREATE}]
        if not high_bloom_cos:
            recs.append(
                COPOMappingRecommendation(
                    recommendation_id=f"REC-{rec_id:03d}",
                    type="bloom_distribution",
                    priority="medium",
                    target_co=None,
                    target_po=None,
                    current_level="No Evaluate/Create level COs",
                    suggested_level="At least 1-2 higher-order COs",
                    rationale="Higher-order Bloom levels (Evaluate, Create) strengthen PO5 (Modern Tools) and PO12 (Project Management) mapping.",
                    impact="Improves OBE quality score and attainment credibility",
                )
            )
            rec_id += 1

        return recs

    def _assess_nba_compliance(
        self,
        stats: MappingStatistics,
        input_data: COPOInput,
    ) -> Tuple[float, bool, List[str]]:
        notes: List[str] = []
        score = 100.0

        if stats.coverage_percentage < 60:
            score -= 30
            notes.append(f"CRITICAL: PO coverage {stats.coverage_percentage:.1f}% below minimum 60% threshold")
        elif stats.coverage_percentage < 80:
            score -= 10
            notes.append(f"WARNING: PO coverage {stats.coverage_percentage:.1f}% below recommended 80%")

        if len(input_data.course_outcomes) < 5:
            score -= 15
            notes.append("WARNING: Less than 5 course outcomes. NBA typically requires 5-7 per course.")

        high_ratio = stats.high_correlation_count / max(stats.total_mappings, 1)
        if high_ratio < 0.1:
            score -= 10
            notes.append("WARNING: Less than 10% high-correlation mappings detected.")

        if not stats.uncovered_pos:
            notes.append("PASS: All program outcomes have at least one CO mapping.")

        if len(input_data.program_outcomes) >= 12:
            notes.append("PASS: All 12 NBA mandatory POs are present.")
        else:
            score -= 20
            notes.append(f"CRITICAL: Only {len(input_data.program_outcomes)} POs found. NBA requires all 12.")

        score = max(0.0, min(100.0, score))
        compliant = score >= 70.0 and len(input_data.program_outcomes) >= 12
        return round(score, 2), compliant, notes
