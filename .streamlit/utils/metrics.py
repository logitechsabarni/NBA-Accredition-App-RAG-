import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple


# ─── NBA Constants ────────────────────────────────────────────────────────────
NBA_TARGET_ATTAINMENT = 60.0  # 60% threshold for NBA
NBA_DIRECT_WEIGHT = 0.8
NBA_INDIRECT_WEIGHT = 0.2
PO_LEVELS = {1: "Low", 2: "Medium", 3: "High"}
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]

# Program Outcomes (as per NBA/AICTE)
NBA_POS = {
    "PO1": "Engineering Knowledge",
    "PO2": "Problem Analysis",
    "PO3": "Design/Development of Solutions",
    "PO4": "Conduct Investigations of Complex Problems",
    "PO5": "Modern Tool Usage",
    "PO6": "The Engineer and Society",
    "PO7": "Environment and Sustainability",
    "PO8": "Ethics",
    "PO9": "Individual and Team Work",
    "PO10": "Communication",
    "PO11": "Project Management and Finance",
    "PO12": "Life-long Learning",
}


# ─── CO Attainment ────────────────────────────────────────────────────────────

def calculate_co_attainment(
    direct_scores: Dict[str, float],
    indirect_scores: Dict[str, float],
    direct_weight: float = NBA_DIRECT_WEIGHT,
    indirect_weight: float = NBA_INDIRECT_WEIGHT,
    target: float = NBA_TARGET_ATTAINMENT,
) -> Dict[str, Any]:
    """
    Calculate CO attainment from direct and indirect assessment.

    Args:
        direct_scores: {CO_id: percentage_of_students_achieving_target}
        indirect_scores: {CO_id: indirect_attainment_percentage}
        direct_weight: Weight for direct assessment (default 0.80)
        indirect_weight: Weight for indirect assessment (default 0.20)
        target: Target attainment percentage

    Returns:
        Dict with attainment values, levels, and analysis.
    """
    all_cos = set(direct_scores.keys()) | set(indirect_scores.keys())
    results = {}

    for co in sorted(all_cos):
        direct = direct_scores.get(co, 0.0)
        indirect = indirect_scores.get(co, 0.0)
        attainment = direct_weight * direct + indirect_weight * indirect

        level = "Not Attained"
        if attainment >= target + 10:
            level = "Highly Attained"
        elif attainment >= target:
            level = "Attained"
        elif attainment >= target - 10:
            level = "Partially Attained"

        results[co] = {
            "direct": round(direct, 2),
            "indirect": round(indirect, 2),
            "attainment": round(attainment, 2),
            "target": target,
            "level": level,
            "gap": round(max(0, target - attainment), 2),
            "exceeded": max(0, attainment - target),
        }

    return results


def calculate_po_attainment(
    co_attainment: Dict[str, Dict],
    co_po_matrix: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Calculate PO attainment from CO attainment and CO-PO mapping.

    Args:
        co_attainment: Output from calculate_co_attainment()
        co_po_matrix: DataFrame with COs as rows and POs as columns (values 0,1,2,3)

    Returns:
        Dict with PO attainment values and analysis.
    """
    po_attainment = {}

    for po in co_po_matrix.columns:
        weighted_sum = 0.0
        weight_total = 0.0

        for co in co_po_matrix.index:
            if co in co_attainment:
                mapping_strength = co_po_matrix.loc[co, po]
                if mapping_strength > 0:
                    co_val = co_attainment[co]["attainment"]
                    weighted_sum += co_val * mapping_strength
                    weight_total += mapping_strength

        po_val = (weighted_sum / weight_total) if weight_total > 0 else 0.0
        po_attainment[po] = {
            "attainment": round(po_val, 2),
            "level": "Attained" if po_val >= NBA_TARGET_ATTAINMENT else "Not Attained",
            "contributing_cos": int(weight_total > 0),
        }

    return po_attainment


# ─── CO-PO Mapping ────────────────────────────────────────────────────────────

def generate_copo_matrix(
    cos: List[str],
    pos: List[str],
    manual_values: Optional[Dict] = None,
) -> pd.DataFrame:
    """
    Generate a CO-PO mapping matrix.

    Args:
        cos: List of CO identifiers.
        pos: List of PO identifiers.
        manual_values: Optional dict of {(co, po): strength}

    Returns:
        DataFrame with mapping strengths (0-3).
    """
    matrix = pd.DataFrame(0, index=cos, columns=pos)

    if manual_values:
        for (co, po), val in manual_values.items():
            if co in matrix.index and po in matrix.columns:
                matrix.loc[co, po] = int(val)
    else:
        # Default heuristic: assign reasonable NBA-standard mappings
        for i, co in enumerate(cos):
            for j, po in enumerate(pos):
                # Engineering-standard defaults
                if j < 3:  # PO1-PO3: Technical POs - higher mapping for early COs
                    matrix.loc[co, po] = np.random.choice([1, 2, 3], p=[0.2, 0.4, 0.4])
                elif j < 6:
                    matrix.loc[co, po] = np.random.choice([0, 1, 2], p=[0.3, 0.4, 0.3])
                else:
                    matrix.loc[co, po] = np.random.choice([0, 1, 2], p=[0.5, 0.35, 0.15])

    return matrix


def compute_coverage(matrix: pd.DataFrame) -> Dict[str, Any]:
    """Compute mapping coverage statistics."""
    total = matrix.size
    mapped = (matrix > 0).sum().sum()
    coverage_pct = (mapped / total * 100) if total > 0 else 0

    co_coverage = {}
    for co in matrix.index:
        row = matrix.loc[co]
        co_coverage[co] = round((row > 0).sum() / len(row) * 100, 1)

    po_coverage = {}
    for po in matrix.columns:
        col = matrix[po]
        po_coverage[po] = round((col > 0).sum() / len(col) * 100, 1)

    gaps = [(co, po) for co in matrix.index for po in matrix.columns if matrix.loc[co, po] == 0]

    return {
        "total_cells": total,
        "mapped_cells": int(mapped),
        "coverage_pct": round(coverage_pct, 1),
        "co_coverage": co_coverage,
        "po_coverage": po_coverage,
        "gap_cells": len(gaps),
        "strong_mappings": int((matrix == 3).sum().sum()),
        "medium_mappings": int((matrix == 2).sum().sum()),
        "weak_mappings": int((matrix == 1).sum().sum()),
    }


# ─── Readiness Score ─────────────────────────────────────────────────────────

def calculate_readiness_score(
    co_attainment: Dict[str, Dict],
    po_attainment: Dict[str, Dict],
    sar_completion: float,
    doc_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate overall NBA accreditation readiness score.

    Returns a composite score out of 100.
    """
    # Component weights
    weights = {
        "co_attainment": 0.30,
        "po_attainment": 0.30,
        "sar_completion": 0.25,
        "documentation": 0.15,
    }

    # CO attainment score
    if co_attainment:
        co_vals = [v["attainment"] for v in co_attainment.values()]
        co_score = np.mean(co_vals)
    else:
        co_score = 0.0

    # PO attainment score
    if po_attainment:
        po_vals = [v["attainment"] for v in po_attainment.values()]
        po_score = np.mean(po_vals)
    else:
        po_score = 0.0

    composite = (
        weights["co_attainment"] * co_score
        + weights["po_attainment"] * po_score
        + weights["sar_completion"] * sar_completion
        + weights["documentation"] * doc_score
    )

    level = "Critical"
    color = "#ef4444"
    if composite >= 80:
        level = "Excellent"
        color = "#22c55e"
    elif composite >= 70:
        level = "Good"
        color = "#84cc16"
    elif composite >= 60:
        level = "Satisfactory"
        color = "#f59e0b"
    elif composite >= 50:
        level = "Needs Improvement"
        color = "#f97316"

    return {
        "score": round(composite, 1),
        "level": level,
        "color": color,
        "co_score": round(co_score, 1),
        "po_score": round(po_score, 1),
        "sar_score": round(sar_completion, 1),
        "doc_score": round(doc_score, 1),
        "components": weights,
    }


def generate_recommendations(
    co_attainment: Dict[str, Dict],
    po_attainment: Dict[str, Dict],
    coverage: Dict[str, Any],
) -> List[str]:
    """Generate actionable NBA improvement recommendations."""
    recs = []

    # CO recommendations
    weak_cos = [co for co, v in co_attainment.items() if v["attainment"] < NBA_TARGET_ATTAINMENT]
    if weak_cos:
        recs.append(
            f"🔴 **CO Attainment Below Target**: {', '.join(weak_cos)} are below {NBA_TARGET_ATTAINMENT}%. "
            f"Consider remedial teaching, additional assessments, or curriculum revision."
        )

    # PO recommendations
    weak_pos = [po for po, v in po_attainment.items() if v["attainment"] < NBA_TARGET_ATTAINMENT]
    if weak_pos:
        recs.append(
            f"🟡 **PO Attainment Gap**: {', '.join(weak_pos)} need improvement. "
            f"Review CO-PO mapping to ensure adequate coverage and increase relevant assessments."
        )

    # Coverage recommendations
    if coverage.get("coverage_pct", 100) < 50:
        recs.append(
            "⚠️ **Low CO-PO Coverage**: Less than 50% of COs are mapped to POs. "
            "Review and update CO-PO mapping matrix to ensure comprehensive coverage."
        )

    if coverage.get("gap_cells", 0) > coverage.get("total_cells", 1) * 0.5:
        recs.append(
            "📋 **Many Unmapped COs**: Consider revising course content to address more Program Outcomes."
        )

    if not recs:
        recs.append("✅ **All indicators meet NBA targets.** Maintain current practices and document evidence thoroughly.")

    return recs
