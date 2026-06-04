"""
Workflow state definitions for LangGraph orchestration.
Pydantic v2 models representing agent and workflow state.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    ANALYST = "analyst"
    RETRIEVER = "retriever"
    SUMMARIZER = "summarizer"
    VALIDATOR = "validator"
    ROUTER = "router"


class MessageRole(str, Enum):
    SYSTEM = "system"
    HUMAN = "human"
    AI = "ai"
    TOOL = "tool"


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_role: AgentRole
    action: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None


class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 2.0
    initial_delay_ms: float = 500.0
    max_delay_ms: float = 10000.0


class WorkflowContext(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    tenant_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowState(BaseModel):
    """
    Central state object passed through the LangGraph workflow.
    All agents read from and write to this state.
    """

    context: WorkflowContext
    status: WorkflowStatus = WorkflowStatus.PENDING
    messages: list[Message] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    current_agent: AgentRole | None = None
    next_agent: AgentRole | None = None
    retrieved_documents: list[dict[str, Any]] = Field(default_factory=dict)
    llm_responses: dict[str, Any] = Field(default_factory=dict)
    final_output: str | None = None
    error: str | None = None
    retry_count: int = 0
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str, metadata: dict[str, Any] | None = None) -> None:
        self.messages.append(
            Message(role=role, content=content, metadata=metadata or {})
        )
        self.updated_at_now()

    def add_step(self, step: AgentStep) -> None:
        self.steps.append(step)
        self.updated_at_now()

    def record_trace(self, event: str, data: dict[str, Any]) -> None:
        self.execution_trace.append(
            {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": self.current_agent,
                **data,
            }
        )

    def updated_at_now(self) -> None:
        self.context.updated_at = datetime.utcnow()

    def is_terminal(self) -> bool:
        return self.status in {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        }

    def can_retry(self) -> bool:
        return self.retry_count < self.retry_policy.max_retries

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
