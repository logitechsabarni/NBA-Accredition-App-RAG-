"""
Base Agent - Foundation for all NBA Enterprise AI Platform agents.

Provides async execution, validation hooks, audit logging, metrics,
structured responses, and LangGraph-ready architecture.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Dict, Generic, List, Optional, TypeVar

import structlog
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VALIDATION_FAILED = "validation_failed"


class AgentPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentCategory(str, Enum):
    MAPPING = "mapping"
    ATTAINMENT = "attainment"
    REPORTING = "reporting"
    IMPROVEMENT = "improvement"
    ANALYTICS = "analytics"
    VALIDATION = "validation"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class AgentMetadata(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    agent_version: str = "1.0.0"
    category: AgentCategory
    description: str
    supports_streaming: bool = False
    max_retries: int = 3
    timeout_seconds: int = 300
    langgraph_compatible: bool = True


class RequestContext(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    department_id: Optional[str] = None
    academic_year: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: AgentPriority = AgentPriority.NORMAL
    initiated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("academic_year", mode="before")
    @classmethod
    def validate_academic_year(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v:
            parts = v.split("-")
            if len(parts) != 2 or not all(p.isdigit() and len(p) == 4 for p in parts):
                raise ValueError("academic_year must be in format YYYY-YYYY")
        return v


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentMetrics(BaseModel):
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    llm_calls: int = 0
    db_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    retry_count: int = 0
    memory_peak_mb: float = 0.0


class AuditEntry(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    action: str
    request_id: str
    user_id: Optional[str]
    organization_id: Optional[str]
    status: AgentStatus
    input_summary: Dict[str, Any]
    output_summary: Dict[str, Any]
    metrics: AgentMetrics
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


T = TypeVar("T")


class AgentResponse(BaseModel, Generic[T]):
    request_id: str
    agent_name: str
    agent_version: str
    status: AgentStatus
    data: Optional[T] = None
    validation: Optional[ValidationResult] = None
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_ms: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AgentError(Exception):
    """Base exception for all agent errors."""

    def __init__(self, message: str, agent_name: str, request_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.agent_name = agent_name
        self.request_id = request_id
        self.details = details or {}


class AgentValidationError(AgentError):
    """Raised when input validation fails."""

    def __init__(self, message: str, agent_name: str, request_id: str, validation_errors: List[str]):
        super().__init__(message, agent_name, request_id, {"validation_errors": validation_errors})
        self.validation_errors = validation_errors


class AgentTimeoutError(AgentError):
    """Raised when agent execution exceeds timeout."""


class AgentConfigurationError(AgentError):
    """Raised when agent is misconfigured."""


# ---------------------------------------------------------------------------
# Base Agent ABC
# ---------------------------------------------------------------------------


InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all NBA Enterprise AI Platform agents.

    Provides:
    - Async execute() with full lifecycle management
    - Pre/post validation hooks
    - Audit logging integration
    - Metrics collection
    - Structured logging with request context
    - LangGraph-ready state management
    - Enterprise error handling with retry logic
    """

    def __init__(self) -> None:
        self._metadata: AgentMetadata = self._build_metadata()
        self._log = structlog.get_logger(self.__class__.__name__)
        self._metrics = AgentMetrics()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_metadata(self) -> AgentMetadata:
        """Return agent metadata descriptor."""

    @abstractmethod
    async def _execute_core(self, input_data: InputT, context: RequestContext) -> OutputT:
        """Core business logic. Must be implemented by each agent."""

    @abstractmethod
    async def _validate_input(self, input_data: InputT, context: RequestContext) -> ValidationResult:
        """Validate incoming data before execution."""

    # ------------------------------------------------------------------
    # Optional hooks (override as needed)
    # ------------------------------------------------------------------

    async def _pre_execute_hook(self, input_data: InputT, context: RequestContext) -> None:
        """Called before execution. Override for custom pre-processing."""

    async def _post_execute_hook(
        self, input_data: InputT, output: OutputT, context: RequestContext
    ) -> None:
        """Called after successful execution. Override for custom post-processing."""

    async def _on_error_hook(self, error: Exception, context: RequestContext) -> None:
        """Called on execution failure. Override for custom error handling."""

    async def _validate_output(self, output: OutputT, context: RequestContext) -> ValidationResult:
        """Optional output validation. Override for strict output contracts."""
        return ValidationResult(is_valid=True)

    # ------------------------------------------------------------------
    # Public execute interface
    # ------------------------------------------------------------------

    async def execute(
        self,
        input_data: InputT,
        context: Optional[RequestContext] = None,
    ) -> AgentResponse[OutputT]:
        """
        Execute the agent with full lifecycle management.

        Lifecycle:
        1. Context initialization
        2. Input validation
        3. Pre-execute hook
        4. Core execution (with timeout + retry)
        5. Output validation
        6. Post-execute hook
        7. Audit log
        8. Return structured response
        """
        if context is None:
            context = RequestContext()

        bound_log = self._log.bind(
            request_id=context.request_id,
            agent_name=self._metadata.agent_name,
            user_id=context.user_id,
            organization_id=context.organization_id,
        )

        start_time = time.perf_counter()
        self._metrics = AgentMetrics()

        bound_log.info("agent_execution_started", priority=context.priority.value)

        # ---- Input validation ----
        validation_result = await self._validate_input(input_data, context)
        if not validation_result.is_valid:
            elapsed = (time.perf_counter() - start_time) * 1000
            bound_log.warning(
                "agent_input_validation_failed",
                errors=validation_result.errors,
            )
            await self._emit_audit(
                context=context,
                action="execute",
                status=AgentStatus.VALIDATION_FAILED,
                input_summary=self._summarize_input(input_data),
                output_summary={},
                error_message="; ".join(validation_result.errors),
                elapsed_ms=elapsed,
            )
            return AgentResponse(
                request_id=context.request_id,
                agent_name=self._metadata.agent_name,
                agent_version=self._metadata.agent_version,
                status=AgentStatus.VALIDATION_FAILED,
                validation=validation_result,
                errors=validation_result.errors,
                warnings=validation_result.warnings,
                execution_time_ms=elapsed,
            )

        # ---- Pre-execute hook ----
        try:
            await self._pre_execute_hook(input_data, context)
        except Exception as hook_err:
            bound_log.error("pre_execute_hook_failed", error=str(hook_err))

        # ---- Core execution with timeout + retry ----
        output: Optional[OutputT] = None
        last_error: Optional[Exception] = None
        attempt = 0

        while attempt <= self._metadata.max_retries:
            attempt += 1
            try:
                output = await asyncio.wait_for(
                    self._execute_core(input_data, context),
                    timeout=self._metadata.timeout_seconds,
                )
                break
            except asyncio.TimeoutError:
                last_error = AgentTimeoutError(
                    f"Agent {self._metadata.agent_name} timed out after {self._metadata.timeout_seconds}s",
                    self._metadata.agent_name,
                    context.request_id,
                )
                bound_log.warning("agent_execution_timeout", attempt=attempt)
                break
            except (AgentValidationError, AgentConfigurationError) as non_retryable:
                last_error = non_retryable
                bound_log.error("agent_non_retryable_error", error=str(non_retryable), attempt=attempt)
                break
            except Exception as exc:
                last_error = exc
                self._metrics.retry_count += 1
                bound_log.warning(
                    "agent_execution_attempt_failed",
                    attempt=attempt,
                    max_retries=self._metadata.max_retries,
                    error=str(exc),
                )
                if attempt <= self._metadata.max_retries:
                    await asyncio.sleep(min(2 ** (attempt - 1), 30))

        elapsed = (time.perf_counter() - start_time) * 1000
        self._metrics.execution_time_ms = elapsed

        # ---- Handle failure ----
        if last_error is not None or output is None:
            error_msg = str(last_error) if last_error else "Unknown execution failure"
            bound_log.error("agent_execution_failed", error=error_msg, elapsed_ms=elapsed)
            await self._on_error_hook(last_error or Exception(error_msg), context)
            await self._emit_audit(
                context=context,
                action="execute",
                status=AgentStatus.FAILED,
                input_summary=self._summarize_input(input_data),
                output_summary={},
                error_message=error_msg,
                elapsed_ms=elapsed,
            )
            return AgentResponse(
                request_id=context.request_id,
                agent_name=self._metadata.agent_name,
                agent_version=self._metadata.agent_version,
                status=AgentStatus.FAILED,
                metrics=self._metrics,
                errors=[error_msg],
                execution_time_ms=elapsed,
            )

        # ---- Output validation ----
        output_validation = await self._validate_output(output, context)
        warnings: List[str] = list(validation_result.warnings)
        if not output_validation.is_valid:
            warnings.extend(output_validation.errors)

        # ---- Post-execute hook ----
        try:
            await self._post_execute_hook(input_data, output, context)
        except Exception as hook_err:
            bound_log.error("post_execute_hook_failed", error=str(hook_err))

        bound_log.info("agent_execution_succeeded", elapsed_ms=elapsed)

        await self._emit_audit(
            context=context,
            action="execute",
            status=AgentStatus.SUCCESS,
            input_summary=self._summarize_input(input_data),
            output_summary=self._summarize_output(output),
            elapsed_ms=elapsed,
        )

        return AgentResponse(
            request_id=context.request_id,
            agent_name=self._metadata.agent_name,
            agent_version=self._metadata.agent_version,
            status=AgentStatus.SUCCESS,
            data=output,
            validation=validation_result,
            metrics=self._metrics,
            warnings=warnings,
            execution_time_ms=elapsed,
        )

    # ------------------------------------------------------------------
    # Streaming support (LangGraph-ready)
    # ------------------------------------------------------------------

    async def execute_stream(
        self,
        input_data: InputT,
        context: Optional[RequestContext] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming execution for LangGraph integration.
        Override _stream_core for actual streaming; default wraps execute().
        """
        if context is None:
            context = RequestContext()

        yield {"event": "start", "request_id": context.request_id, "agent": self._metadata.agent_name}

        response = await self.execute(input_data, context)
        yield {"event": "result", "data": response.model_dump(mode="json")}
        yield {"event": "end", "request_id": context.request_id, "status": response.status.value}

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    def increment_llm_calls(self, n: int = 1) -> None:
        self._metrics.llm_calls += n

    def increment_db_queries(self, n: int = 1) -> None:
        self._metrics.db_queries += n

    def record_cache_hit(self) -> None:
        self._metrics.cache_hits += 1

    def record_cache_miss(self) -> None:
        self._metrics.cache_misses += 1

    def add_tokens_used(self, n: int) -> None:
        self._metrics.tokens_used += n

    # ------------------------------------------------------------------
    # LangGraph state helpers
    # ------------------------------------------------------------------

    def to_langgraph_node(self) -> Dict[str, Any]:
        """Return metadata dict for LangGraph node registration."""
        return {
            "name": self._metadata.agent_name,
            "version": self._metadata.agent_version,
            "category": self._metadata.category.value,
            "supports_streaming": self._metadata.supports_streaming,
            "timeout": self._metadata.timeout_seconds,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _summarize_input(self, input_data: InputT) -> Dict[str, Any]:
        try:
            data = input_data.model_dump(mode="json")
            return {k: (str(v)[:120] if isinstance(v, str) and len(str(v)) > 120 else v) for k, v in data.items()}
        except Exception:
            return {"raw": str(input_data)[:200]}

    def _summarize_output(self, output: OutputT) -> Dict[str, Any]:
        try:
            data = output.model_dump(mode="json")
            return {k: v for k, v in list(data.items())[:10]}
        except Exception:
            return {"raw": str(output)[:200]}

    async def _emit_audit(
        self,
        context: RequestContext,
        action: str,
        status: AgentStatus,
        input_summary: Dict[str, Any],
        output_summary: Dict[str, Any],
        elapsed_ms: float,
        error_message: Optional[str] = None,
    ) -> None:
        self._metrics.execution_time_ms = elapsed_ms
        entry = AuditEntry(
            agent_name=self._metadata.agent_name,
            action=action,
            request_id=context.request_id,
            user_id=context.user_id,
            organization_id=context.organization_id,
            status=status,
            input_summary=input_summary,
            output_summary=output_summary,
            metrics=self._metrics,
            error_message=error_message,
        )
        self._log.info(
            "audit_entry",
            audit_id=entry.audit_id,
            agent_name=entry.agent_name,
            action=entry.action,
            status=entry.status.value,
            request_id=entry.request_id,
            execution_time_ms=elapsed_ms,
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    @property
    def name(self) -> str:
        return self._metadata.agent_name

    @property
    def version(self) -> str:
        return self._metadata.agent_version
