"""
backend/api/routes/workflow.py
──────────────────────────────
Workflow execution routes — submit, status, cancel, list.
Designed to plug into the LangGraph execution engine (Phase 5 core).
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import CurrentUser

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class WorkflowSubmitRequest(BaseModel):
    task: str = Field(..., description="Workflow task name / identifier")
    context: dict[str, Any] = Field(default_factory=dict, description="Execution context payload")
    priority: Literal["low", "normal", "high"] = "normal"


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    task: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    priority: str
    submitted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    submitted_by: str


class WorkflowListResponse(BaseModel):
    total: int
    workflows: list[WorkflowStatusResponse]


class WorkflowCancelResponse(BaseModel):
    workflow_id: str
    cancelled: bool
    message: str


# ── In-memory workflow registry (replace with DB/Redis queue) ─────────────────
_workflows: dict[str, WorkflowStatusResponse] = {}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/execute",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a workflow task for LangGraph execution",
)
async def execute_workflow(body: WorkflowSubmitRequest, user: CurrentUser) -> WorkflowStatusResponse:
    wf_id = str(uuid.uuid4())
    record = WorkflowStatusResponse(
        workflow_id=wf_id,
        task=body.task,
        status="queued",
        priority=body.priority,
        submitted_at=datetime.utcnow(),
        submitted_by=user.sub,
    )
    _workflows[wf_id] = record

    # ── Hook: dispatch to LangGraph orchestrator here ──────────────────────
    # await orchestrator.run({"workflow_id": wf_id, "task": body.task, **body.context})

    return record


@router.get(
    "/{workflow_id}",
    response_model=WorkflowStatusResponse,
    summary="Poll the status of a specific workflow",
)
async def get_workflow_status(workflow_id: str, user: CurrentUser) -> WorkflowStatusResponse:
    record = _workflows.get(workflow_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )
    return record


@router.get(
    "/",
    response_model=WorkflowListResponse,
    summary="List all submitted workflows (optionally filter by status)",
)
async def list_workflows(
    user: CurrentUser,
    status_filter: str | None = None,
) -> WorkflowListResponse:
    workflows = list(_workflows.values())
    if status_filter:
        workflows = [w for w in workflows if w.status == status_filter]
    return WorkflowListResponse(total=len(workflows), workflows=workflows)


@router.post(
    "/{workflow_id}/cancel",
    response_model=WorkflowCancelResponse,
    summary="Request cancellation of a queued or running workflow",
)
async def cancel_workflow(workflow_id: str, user: CurrentUser) -> WorkflowCancelResponse:
    record = _workflows.get(workflow_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    if record.status in ("completed", "failed", "cancelled"):
        return WorkflowCancelResponse(
            workflow_id=workflow_id,
            cancelled=False,
            message=f"Workflow already in terminal state: {record.status}",
        )

    record.status = "cancelled"
    record.completed_at = datetime.utcnow()
    return WorkflowCancelResponse(
        workflow_id=workflow_id,
        cancelled=True,
        message="Workflow cancellation requested",
    )


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a workflow record",
)
async def delete_workflow(workflow_id: str, user: CurrentUser) -> None:
    if workflow_id not in _workflows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )
    del _workflows[workflow_id]
