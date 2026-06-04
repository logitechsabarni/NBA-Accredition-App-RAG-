"""
NBA Enterprise AI Platform — Domain Validators
Business-rule validation helpers for NBA accreditation data.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


# ----------------------------------------------------------------
# CO / PO code validators
# ----------------------------------------------------------------

CO_PATTERN = re.compile(r"^CO[1-9]\d*$", re.IGNORECASE)
PO_PATTERN = re.compile(r"^PO[1-9]\d*$|^PSO[1-9]\d*$", re.IGNORECASE)


def validate_co_code(code: str) -> Tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if not code:
        return False, "CO code cannot be empty"
    if not CO_PATTERN.match(code.strip()):
        return False, f"Invalid CO code format: '{code}'. Expected format: CO1, CO2, ..."
    return True, ""


def validate_po_code(code: str) -> Tuple[bool, str]:
    """Returns (is_valid, error_message). Accepts PO and PSO codes."""
    if not code:
        return False, "PO/PSO code cannot be empty"
    if not PO_PATTERN.match(code.strip()):
        return False, f"Invalid PO/PSO code format: '{code}'. Expected: PO1..PO12 or PSO1..PSO3"
    return True, ""


def validate_correlation_value(value: float) -> Tuple[bool, str]:
    """NBA correlation values: 0 (no correlation), 1 (low), 2 (medium), 3 (high)."""
    if value not in {0, 1, 2, 3}:
        return False, f"Correlation value must be 0, 1, 2, or 3. Got: {value}"
    return True, ""


def validate_attainment_target(target: float) -> Tuple[bool, str]:
    """NBA attainment target: typically 40–70%."""
    if not (0 <= target <= 100):
        return False, f"Attainment target must be between 0 and 100. Got: {target}"
    return True, ""


def validate_copo_matrix(
    matrix: Dict[str, Dict[str, float]],
    co_codes: List[str],
    po_codes: List[str],
) -> Tuple[bool, List[str]]:
    """
    Validate a full CO-PO mapping matrix.
    Returns (is_valid, list_of_errors).
    """
    errors: List[str] = []

    for co in co_codes:
        if co not in matrix:
            errors.append(f"Missing CO in matrix: {co}")
            continue
        for po in po_codes:
            if po not in matrix[co]:
                errors.append(f"Missing mapping for {co} → {po}")
                continue
            ok, msg = validate_correlation_value(matrix[co][po])
            if not ok:
                errors.append(f"{co} → {po}: {msg}")

    return len(errors) == 0, errors


def validate_marks_data(
    marks: List[float],
    max_marks: float,
) -> Tuple[bool, str]:
    """Validate a list of student marks."""
    if not marks:
        return False, "Marks list cannot be empty"
    if max_marks <= 0:
        return False, "Max marks must be greater than 0"
    for i, m in enumerate(marks):
        if m < 0:
            return False, f"Mark at index {i} is negative: {m}"
        if m > max_marks:
            return False, f"Mark at index {i} ({m}) exceeds max marks ({max_marks})"
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    pattern = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$")
    if not pattern.match(email):
        return False, f"Invalid email address: {email}"
    return True, ""
