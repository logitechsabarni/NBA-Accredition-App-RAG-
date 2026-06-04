# backend/agents/validation_agent.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, TypedDict, Union

from pydantic import BaseModel, Field, ValidationError, root_validator, validator
import logging
import json
import time
import uuid

# Structured logging setup (dependency-injection friendly)
# Expect external configuration to add handlers/formatters.
logger = logging.getLogger("agents.validation")


# ---- Common Types ----

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationDomain(str, Enum):
    COMPLIANCE = "COMPLIANCE"
    NBA_RULES = "NBA_RULES"
    WORKFLOW = "WORKFLOW"
    DATA = "DATA"
    SYSTEM = "SYSTEM"


class AuditAction(str, Enum):
    VALIDATION_STARTED = "VALIDATION_STARTED"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=lambda: time.time())
    actor: str = Field(default="ValidationAgent")
    action: AuditAction
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationFinding(BaseModel):
    domain: ValidationDomain
    code: str
    message: str
    severity: Severity = Severity.ERROR
    hint: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ValidationInput(BaseModel):
    # Core envelope for validations. Keep flexible but typed.
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    workflow: Optional[Dict[str, Any]] = None
    rules: Optional[Dict[str, Any]] = None
    # Optional identifiers for audit trail correlation.
    correlation_id: Optional[str] = None
    actor: Optional[str] = None

    @validator("payload", "context", pre=True)
    def ensure_dict(cls, v: Any) -> Dict[str, Any]:
        return v or {}


class ValidationSummary(BaseModel):
    total: int
    errors: int
    warnings: int
    infos: int
    critical: int


class ValidationResponse(BaseModel):
    ok: bool
    summary: ValidationSummary
    findings: List[ValidationFinding] = Field(default_factory=list)
    domains_run: List[ValidationDomain] = Field(default_factory=list)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---- Exceptions ----

class AgentError(Exception):
    """Base agent error for enterprise-safe handling."""
    def __init__(self, message: str, *, code: str = "AGENT_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ValidationAgentError(AgentError):
    """Validation-specific error."""
    pass


# ---- Dependency Interfaces (DI-friendly) ----

class AuditLoggerProtocol:
    async def write(self, record: AuditRecord) -> None:  # pragma: no cover - interface
        ...


class DefaultAuditLogger(AuditLoggerProtocol):
    def __init__(self, log: logging.Logger | None = None) -> None:
        self._log = log or logger

    async def write(self, record: AuditRecord) -> None:
        # Non-blocking structured log emission
        self._log.info(
            "audit_log",
            extra={
                "audit": {
                    "id": record.id,
                    "timestamp": record.timestamp,
                    "actor": record.actor,
                    "action": record.action,
                    "metadata": record.metadata,
                }
            },
        )


# ---- Rule Engines / Validators (pluggable via DI) ----

class ComplianceRule(TypedDict, total=False):
    id: str
    description: str
    required_fields: List[str]
    prohibited_fields: List[str]
    max_length: Dict[str, int]
    enum_sets: Dict[str, List[Any]]


class NBARule(TypedDict, total=False):
    id: str
    description: str
    # Example: salary cap, roster size, trade window, etc.
    type: str
    params: Dict[str, Any]


class WorkflowSpec(TypedDict, total=False):
    id: str
    steps: List[Dict[str, Any]]
    required_transitions: List[Tuple[str, str]]
    entrypoint: str
    terminal_steps: List[str]


class DataSchema(TypedDict, total=False):
    fields: Dict[str, Dict[str, Any]]  # name -> {type, required, min, max, pattern}


# ---- Utility functions ----

def _count_by_severity(findings: Sequence[ValidationFinding]) -> ValidationSummary:
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity == Severity.WARNING)
    infos = sum(1 for f in findings if f.severity == Severity.INFO)
    critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    return ValidationSummary(total=len(findings), errors=errors, warnings=warnings, infos=infos, critical=critical)


def _safe_get(d: Mapping[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for p in path.split("."):
        if isinstance(cur, Mapping) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


# ---- ValidationAgent ----

class ValidationAgent:
    """
    Async, FastAPI- and LangGraph-ready agent that performs:
    - compliance validation
    - NBA rule validation
    - workflow validation
    - data validation
    Includes audit support, structured responses, and enterprise error handling.
    """

    def __init__(
        self,
        *,
        audit_logger: Optional[AuditLoggerProtocol] = None,
        compliance_rules_provider: Optional[Callable[[ValidationInput], Awaitable[List[ComplianceRule]]]] = None,
        nba_rules_provider: Optional[Callable[[ValidationInput], Awaitable[List[NBARule]]]] = None,
        workflow_provider: Optional[Callable[[ValidationInput], Awaitable[WorkflowSpec | None]]] = None,
        data_schema_provider: Optional[Callable[[ValidationInput], Awaitable[DataSchema | None]]] = None,
        logger_: Optional[logging.Logger] = None,
    ) -> None:
        self._audit = audit_logger or DefaultAuditLogger()
        self._get_compliance_rules = compliance_rules_provider or self._default_compliance_rules
        self._get_nba_rules = nba_rules_provider or self._default_nba_rules
        self._get_workflow_spec = workflow_provider or self._default_workflow
        self._get_data_schema = data_schema_provider or self._default_schema
        self._log = logger_ or logger

    # ---- Public API ----

    async def validate(self, vin: ValidationInput) -> ValidationResponse:
        """
        Orchestrate all validation domains and return a structured response.
        LangGraph-ready: signature is pure-async and returns Pydantic model.
        """
        correlation_id = vin.correlation_id or str(uuid.uuid4())
        actor = vin.actor or "ValidationAgent"

        await self._audit.write(
            AuditRecord(action=AuditAction.VALIDATION_STARTED, actor=actor, metadata={"correlation_id": correlation_id})
        )

        self._log.info(
            "validation_started",
            extra={"correlation_id": correlation_id, "domains": [d.value for d in ValidationDomain]},
        )

        try:
            tasks = [
                self._validate_compliance(vin, correlation_id),
                self._validate_nba_rules(vin, correlation_id),
                self._validate_workflow(vin, correlation_id),
                self._validate_data(vin, correlation_id),
            ]
            results_nested: List[List[ValidationFinding]] = await asyncio.gather(*tasks)
            findings = [f for sub in results_nested for f in sub]
            summary = _count_by_severity(findings)
            ok = summary.errors == 0 and summary.critical == 0

            resp = ValidationResponse(
                ok=ok,
                summary=summary,
                findings=findings,
                domains_run=[
                    ValidationDomain.COMPLIANCE,
                    ValidationDomain.NBA_RULES,
                    ValidationDomain.WORKFLOW,
                    ValidationDomain.DATA,
                ],
                correlation_id=correlation_id,
                metadata={"actor": actor},
            )

            await self._audit.write(
                AuditRecord(
                    action=AuditAction.VALIDATION_COMPLETED,
                    actor=actor,
                    metadata={
                        "correlation_id": correlation_id,
                        "ok": ok,
                        "summary": resp.summary.dict(),
                    },
                )
            )

            self._log.info(
                "validation_completed",
                extra={"correlation_id": correlation_id, "ok": ok, "summary": resp.summary.dict()},
            )
            return resp

        except Exception as e:
            err = ValidationAgentError(str(e), code="VALIDATION_UNHANDLED_EXCEPTION")
            await self._audit.write(
                AuditRecord(
                    action=AuditAction.VALIDATION_FAILED,
                    actor=actor,
                    metadata={"correlation_id": correlation_id, "error": {"code": err.code, "message": str(err)}},
                )
            )
            self._log.exception(
                "validation_failed",
                extra={"correlation_id": correlation_id, "error_code": err.code},
            )
            # Return structured failure response rather than raising to keep FastAPI/LangGraph flows stable
            finding = ValidationFinding(
                domain=ValidationDomain.SYSTEM,
                code=err.code,
                message="Unhandled exception during validation.",
                severity=Severity.CRITICAL,
                details={"exception": str(e)},
            )
            summary = _count_by_severity([finding])
            return ValidationResponse(
                ok=False,
                summary=summary,
                findings=[finding],
                domains_run=[],
                correlation_id=correlation_id,
                metadata={"actor": actor},
            )

    # ---- Domain validators ----

    async def _validate_compliance(self, vin: ValidationInput, cid: str) -> List[ValidationFinding]:
        rules = await self._get_compliance_rules(vin)
        findings: List[ValidationFinding] = []

        payload = vin.payload
        for r in rules:
            rid = r.get("id", "COMPLIANCE_RULE")
            # Required fields
            for field in r.get("required_fields", []) or []:
                if _safe_get(payload, field) is None:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.COMPLIANCE,
                            code=f"{rid}_MISSING_FIELD",
                            message=f"Required field '{field}' is missing.",
                            severity=Severity.ERROR,
                            hint="Provide the required field or adjust rule configuration.",
                            details={"field": field, "rule": r},
                        )
                    )
            # Prohibited fields
            for field in r.get("prohibited_fields", []) or []:
                if _safe_get(payload, field) is not None:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.COMPLIANCE,
                            code=f"{rid}_PROHIBITED_FIELD",
                            message=f"Prohibited field '{field}' is present.",
                            severity=Severity.ERROR,
                            hint="Remove the field to comply with policy.",
                            details={"field": field, "rule": r},
                        )
                    )
            # Max length checks
            for field, max_len in (r.get("max_length") or {}).items():
                val = _safe_get(payload, field)
                if isinstance(val, str) and len(val) > int(max_len):
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.COMPLIANCE,
                            code=f"{rid}_MAX_LENGTH_EXCEEDED",
                            message=f"Field '{field}' exceeds max length {max_len}.",
                            severity=Severity.ERROR,
                            hint="Shorten the value or update the rule limit.",
                            details={"field": field, "length": len(val), "max": max_len},
                        )
                    )
            # Enum checks
            for field, allowed in (r.get("enum_sets") or {}).items():
                val = _safe_get(payload, field)
                if val is not None and val not in allowed:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.COMPLIANCE,
                            code=f"{rid}_ENUM_VIOLATION",
                            message=f"Field '{field}' has value '{val}' not in allowed set.",
                            severity=Severity.ERROR,
                            hint=f"Use one of: {allowed}",
                            details={"field": field, "value": val, "allowed": allowed},
                        )
                    )

        if findings:
            self._log.debug("compliance_findings", extra={"correlation_id": cid, "count": len(findings)})
        return findings

    async def _validate_nba_rules(self, vin: ValidationInput, cid: str) -> List[ValidationFinding]:
        rules = await self._get_nba_rules(vin)
        findings: List[ValidationFinding] = []
        payload = vin.payload
        context = vin.context

        for r in rules:
            rid = r.get("id", "NBA_RULE")
            rtype = r.get("type")
            params = r.get("params", {})

            # Example rule: salary_cap
            if rtype == "salary_cap":
                team_salary = float(_safe_get(payload, "team.salary_total", 0) or 0)
                cap = float(params.get("cap", 0) or 0)
                if team_salary > cap:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.NBA_RULES,
                            code=f"{rid}_SALARY_CAP_EXCEEDED",
                            message=f"Team salary {team_salary} exceeds cap {cap}.",
                            severity=Severity.ERROR,
                            hint="Adjust roster or contracts to fit within cap limits.",
                            details={"salary": team_salary, "cap": cap},
                        )
                    )
            # Example rule: roster_size
            elif rtype == "roster_size":
                players = _safe_get(payload, "team.players", []) or []
                min_size = int(params.get("min", 0))
                max_size = int(params.get("max", 999))
                count = len(players) if isinstance(players, list) else 0
                if count < min_size or count > max_size:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.NBA_RULES,
                            code=f"{rid}_ROSTER_SIZE_VIOLATION",
                            message=f"Roster size {count} outside allowed range [{min_size}, {max_size}].",
                            severity=Severity.ERROR,
                            hint="Add or remove players to meet roster requirements.",
                            details={"count": count, "min": min_size, "max": max_size},
                        )
                    )
            # Example rule: trade_window
            elif rtype == "trade_window":
                trade_open = bool(params.get("open", True))
                op = _safe_get(payload, "operation.type")
                if op == "trade" and not trade_open:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.NBA_RULES,
                            code=f"{rid}_TRADE_WINDOW_CLOSED",
                            message="Trade operation attempted while trade window is closed.",
                            severity=Severity.ERROR,
                            hint="Schedule trade within the designated window.",
                            details={"operation": op, "window_open": trade_open},
                        )
                    )
            else:
                # Unknown rule type: informational
                findings.append(
                    ValidationFinding(
                        domain=ValidationDomain.NBA_RULES,
                        code=f"{rid}_UNKNOWN_RULE_TYPE",
                        message=f"Unknown NBA rule type '{rtype}'.",
                        severity=Severity.INFO,
                        details={"rule": r},
                    )
                )

        if findings:
            self._log.debug("nba_rule_findings", extra={"correlation_id": cid, "count": len(findings)})
        return findings

    async def _validate_workflow(self, vin: ValidationInput, cid: str) -> List[ValidationFinding]:
        spec = vin.workflow or await self._get_workflow_spec(vin)
        findings: List[ValidationFinding] = []

        if not spec:
            return findings  # No workflow constraints

        steps: List[Dict[str, Any]] = spec.get("steps", []) or []
        step_ids = {s.get("id") for s in steps if "id" in s}
        entry = spec.get("entrypoint")
        terminals = set(spec.get("terminal_steps", []) or [])
        transitions: List[Tuple[str, str]] = spec.get("required_transitions", []) or []

        # Entrypoint exists
        if entry and entry not in step_ids:
            findings.append(
                ValidationFinding(
                    domain=ValidationDomain.WORKFLOW,
                    code="WORKFLOW_ENTRYPOINT_MISSING",
                    message=f"Entrypoint step '{entry}' is not defined.",
                    severity=Severity.ERROR,
                    hint="Define the entrypoint step in workflow steps.",
                    details={"entrypoint": entry},
                )
            )

        # Transition validity
        for fr, to in transitions:
            if fr not in step_ids or to not in step_ids:
                findings.append(
                    ValidationFinding(
                        domain=ValidationDomain.WORKFLOW,
                        code="WORKFLOW_TRANSITION_INVALID",
                        message=f"Transition '{fr}' -> '{to}' references undefined step(s).",
                        severity=Severity.ERROR,
                        hint="Ensure all transitions reference valid step IDs.",
                        details={"from": fr, "to": to},
                    )
                )

        # Terminal coverage: ensure at least one terminal exists
        if terminals and not (terminals & step_ids):
            findings.append(
                ValidationFinding(
                    domain=ValidationDomain.WORKFLOW,
                    code="WORKFLOW_TERMINAL_MISSING",
                    message="No terminal steps are defined among workflow steps.",
                    severity=Severity.ERROR,
                    hint="Add terminal step(s) to indicate workflow completion.",
                    details={"terminal_steps": list(terminals)},
                )
            )

        # Optional: payload indicates a path; verify it matches allowed transitions (lightweight)
        path: List[str] = vin.context.get("workflow_path", []) or []
        if path:
            invalid_edges: List[Tuple[str, str]] = []
            allowed = set(tuple(t) for t in transitions)
            for a, b in zip(path, path[1:]):
                if (a, b) not in allowed:
                    invalid_edges.append((a, b))
            if invalid_edges:
                findings.append(
                    ValidationFinding(
                        domain=ValidationDomain.WORKFLOW,
                        code="WORKFLOW_PATH_INVALID",
                        message="Workflow path contains invalid transitions.",
                        severity=Severity.ERROR,
                        hint="Adjust steps to follow required transitions.",
                        details={"invalid": invalid_edges, "path": path},
                    )
                )

        if findings:
            self._log.debug("workflow_findings", extra={"correlation_id": cid, "count": len(findings)})
        return findings

    async def _validate_data(self, vin: ValidationInput, cid: str) -> List[ValidationFinding]:
        schema = await self._get_data_schema(vin)
        findings: List[ValidationFinding] = []
        if not schema:
            return findings

        fields = schema.get("fields", {}) or {}
        payload = vin.payload

        for fname, spec in fields.items():
            ftype = spec.get("type")
            required = bool(spec.get("required", False))
            val = _safe_get(payload, fname)

            # Required check
            if required and val is None:
                findings.append(
                    ValidationFinding(
                        domain=ValidationDomain.DATA,
                        code="DATA_REQUIRED_MISSING",
                        message=f"Required field '{fname}' is missing.",
                        severity=Severity.ERROR,
                        hint="Populate required field or revise schema requirement.",
                        details={"field": fname},
                    )
                )
                continue

            if val is None:
                continue  # nothing else to check

            # Type check (basic)
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "object": Mapping,
                "array": list,
            }
            pytype = type_map.get(ftype)
            if pytype and not isinstance(val, pytype):
                findings.append(
                    ValidationFinding(
                        domain=ValidationDomain.DATA,
                        code="DATA_TYPE_MISMATCH",
                        message=f"Field '{fname}' expected type '{ftype}'.",
                        severity=Severity.ERROR,
                        hint="Cast or transform the value to the expected type.",
                        details={"field": fname, "expected": ftype, "actual": type(val).__name__},
                    )
                )
                continue

            # Numeric constraints
            if isinstance(val, (int, float)):
                if "min" in spec and val < spec["min"]:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.DATA,
                            code="DATA_MIN_VIOLATION",
                            message=f"Field '{fname}' value {val} is below minimum {spec['min']}.",
                            severity=Severity.ERROR,
                            hint="Increase the value to meet minimum requirements.",
                            details={"field": fname, "value": val, "min": spec["min"]},
                        )
                    )
                if "max" in spec and val > spec["max"]:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.DATA,
                            code="DATA_MAX_VIOLATION",
                            message=f"Field '{fname}' value {val} exceeds maximum {spec['max']}.",
                            severity=Severity.ERROR,
                            hint="Reduce the value to meet maximum constraints.",
                            details={"field": fname, "value": val, "max": spec["max"]},
                        )
                    )

            # String constraints
            if isinstance(val, str):
                if "min_length" in spec and len(val) < spec["min_length"]:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.DATA,
                            code="DATA_MIN_LENGTH_VIOLATION",
                            message=f"Field '{fname}' length {len(val)} is below minimum {spec['min_length']}.",
                            severity=Severity.ERROR,
                            hint="Provide a longer value.",
                            details={"field": fname, "length": len(val), "min_length": spec["min_length"]},
                        )
                    )
                if "max_length" in spec and len(val) > spec["max_length"]:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.DATA,
                            code="DATA_MAX_LENGTH_VIOLATION",
                            message=f"Field '{fname}' length {len(val)} exceeds maximum {spec['max_length']}.",
                            severity=Severity.ERROR,
                            hint="Shorten the value.",
                            details={"field": fname, "length": len(val), "max_length": spec["max_length"]},
                        )
                    )
                if "pattern" in spec:
                    import re
                    pattern = spec["pattern"]
                    if not re.fullmatch(pattern, val or ""):
                        findings.append(
                            ValidationFinding(
                                domain=ValidationDomain.DATA,
                                code="DATA_PATTERN_MISMATCH",
                                message=f"Field '{fname}' does not match required pattern.",
                                severity=Severity.ERROR,
                                hint=f"Ensure value matches regex: {pattern}",
                                details={"field": fname, "pattern": pattern},
                            )
                        )

            # Enum
            if "enum" in spec:
                allowed = spec["enum"] or []
                if val not in allowed:
                    findings.append(
                        ValidationFinding(
                            domain=ValidationDomain.DATA,
                            code="DATA_ENUM_VIOLATION",
                            message=f"Field '{fname}' value '{val}' not in allowed set.",
                            severity=Severity.ERROR,
                            hint=f"Use one of: {allowed}",
                            details={"field": fname, "value": val, "allowed": allowed},
                        )
                    )

        if findings:
            self._log.debug("data_findings", extra={"correlation_id": cid, "count": len(findings)})
        return findings

    # ---- Default providers (safe no-ops; can be overridden via DI) ----

    async def _default_compliance_rules(self, vin: ValidationInput) -> List[ComplianceRule]:
        # Sensible light default: require an operation.type and a request.id for traceability
        return [
            {
                "id": "BASE_TRACEABILITY",
                "description": "Ensure minimal traceability envelope.",
                "required_fields": ["operation.type", "request.id"],
                "prohibited_fields": [],
                "max_length": {"request.id": 128},
                "enum_sets": {"operation.type": ["create", "update", "delete", "read", "trade"]},
            }
        ]

    async def _default_nba_rules(self, vin: ValidationInput) -> List[NBARule]:
        # Conservative defaults; real rules to be provided via DI
        return [
            {
                "id": "BASE_ROSTER",
                "description": "Enforce reasonable roster bounds.",
                "type": "roster_size",
                "params": {"min": 8, "max": 20},
            }
        ]

    async def _default_workflow(self, vin: ValidationInput) -> WorkflowSpec | None:
        # No default workflow; must be injected if needed
        return None

    async def _default_schema(self, vin: ValidationInput) -> DataSchema | None:
        # Lightweight default schema for common envelope
        return {
            "fields": {
                "request.id": {"type": "string", "required": True, "min_length": 1, "max_length": 128},
                "operation.type": {"type": "string", "required": True},
                "team.salary_total": {"type": "number", "required": False, "min": 0},
                "team.players": {"type": "array", "required": False},
            }
        }

    # ---- FastAPI integration helpers ----

    async def __call__(self, vin: ValidationInput) -> ValidationResponse:
        # Allows direct DI into FastAPI routes
        return await self.validate(vin)

    # ---- LangGraph integration helpers ----

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node-compatible method.
        Expects 'validation_input' in state (dict) or constructs from keys.
        Returns updated state with 'validation_result'.
        """
        try:
            if "validation_input" in state and isinstance(state["validation_input"], ValidationInput):
                vin = state["validation_input"]
            else:
                vin = ValidationInput(
                    payload=state.get("payload") or {},
                    context=state.get("context") or {},
                    workflow=state.get("workflow"),
                    rules=state.get("rules"),
                    correlation_id=state.get("correlation_id"),
                    actor=state.get("actor"),
                )
            result = await self.validate(vin)
            state["validation_result"] = result
            return state
        except Exception as e:
            # Ensure LangGraph flow continues with structured error in state
            finding = ValidationFinding(
                domain=ValidationDomain.SYSTEM,
                code="LANGGRAPH_NODE_ERROR",
                message="Validation node encountered an error.",
                severity=Severity.CRITICAL,
                details={"exception": str(e)},
            )
            state["validation_result"] = ValidationResponse(
                ok=False,
                summary=_count_by_severity([finding]),
                findings=[finding],
                domains_run=[],
                correlation_id=(state.get("correlation_id") or str(uuid.uuid4())),
                metadata={"actor": state.get("actor") or "ValidationAgent"},
            )
            return state

