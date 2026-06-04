# backend/agents/__init__.py
from __future__ import annotations

# Re-export primary agents for convenient imports across the platform.
# Keep imports lazy-safe to avoid heavy side effects during FastAPI startup.

from .base_agent import BaseAgent as BaseAgent  # type: ignore
from .copo_agent import CoPoAgent as CoPoAgent  # type: ignore
from .attainment_agent import AttainmentAgent as AttainmentAgent  # type: ignore
from .sar_agent import SARAgent as SARAgent  # type: ignore
from .ci_agent import CIAgent as CIAgent  # type: ignore
from .analytics_agent import AnalyticsAgent as AnalyticsAgent  # type: ignore
from .validation_agent import (
    ValidationAgent as ValidationAgent,
    ValidationInput as ValidationInput,
    ValidationResponse as ValidationResponse,
    ValidationFinding as ValidationFinding,
    ValidationSummary as ValidationSummary,
    ValidationDomain as ValidationDomain,
    Severity as Severity,
    AuditRecord as AuditRecord,
    AuditAction as AuditAction,
    ValidationAgentError as ValidationAgentError,
)  # type: ignore

__all__ = [
    "BaseAgent",
    "CoPoAgent",
    "AttainmentAgent",
    "SARAgent",
    "CIAgent",
    "AnalyticsAgent",
    "ValidationAgent",
    "ValidationInput",
    "ValidationResponse",
    "ValidationFinding",
    "ValidationSummary",
    "ValidationDomain",
    "Severity",
    "AuditRecord",
    "AuditAction",
    "ValidationAgentError",
]
