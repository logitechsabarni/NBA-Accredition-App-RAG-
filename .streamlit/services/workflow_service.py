"""
services/workflow_service.py
LangGraph execution wrapper with workflow orchestration, history tracking,
node status updates, agent routing, audit logging, and async support.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import streamlit as st
import structlog

log = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class WorkflowStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"
    PAUSED    = "paused"


class NodeStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    SKIPPED   = "skipped"


class AgentType(str, Enum):
    INTENT_CLASSIFIER  = "intent_classifier"
    COPO_AGENT         = "copo_agent"
    ATTAINMENT_AGENT   = "attainment_agent"
    SAR_AGENT          = "sar_agent"
    CI_AGENT           = "ci_agent"
    ANALYTICS_AGENT    = "analytics_agent"
    VALIDATION_AGENT   = "validation_agent"
    RAG_RETRIEVAL      = "rag_retrieval"
    RESPONSE_GENERATOR = "response_generator"


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class NodeExecution:
    node_id:        str
    node_name:      str
    agent_type:     AgentType
    status:         NodeStatus = NodeStatus.PENDING
    started_at:     Optional[float] = None
    completed_at:   Optional[float] = None
    duration_ms:    Optional[int]   = None
    input_tokens:   int = 0
    output_tokens:  int = 0
    input_summary:  Optional[str]   = None
    output_summary: Optional[str]   = None
    error_message:  Optional[str]   = None
    metadata:       Dict[str, Any]  = field(default_factory=dict)

    @property
    def duration_display(self) -> str:
        if self.duration_ms is None:
            if self.started_at:
                ms = int((time.time() - self.started_at) * 1000)
                return f"{ms}ms ↺"
            return "—"
        if self.duration_ms >= 1000:
            return f"{self.duration_ms/1000:.1f}s"
        return f"{self.duration_ms}ms"


@dataclass
class WorkflowExecution:
    execution_id:   str    = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name:  str    = "NBA Accreditation Workflow"
    trigger_query:  str    = ""
    triggered_by:   str    = "system"
    status:         WorkflowStatus = WorkflowStatus.PENDING
    nodes:          List[NodeExecution] = field(default_factory=list)
    started_at:     Optional[float] = None
    completed_at:   Optional[float] = None
    total_tokens:   int  = 0
    total_cost_usd: float = 0.0
    final_response: Optional[str]  = None
    error_message:  Optional[str]  = None
    metadata:       Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> Optional[int]:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return int((end - self.started_at) * 1000)

    @property
    def duration_display(self) -> str:
        ms = self.duration_ms
        if ms is None:
            return "—"
        if ms >= 1000:
            return f"{ms/1000:.1f}s"
        return f"{ms}ms"

    @property
    def started_at_display(self) -> str:
        if self.started_at is None:
            return "—"
        return datetime.fromtimestamp(self.started_at, tz=timezone.utc).strftime("%H:%M:%S")

    @property
    def completed_nodes(self) -> int:
        return sum(1 for n in self.nodes if n.status == NodeStatus.COMPLETED)

    @property
    def failed_nodes(self) -> int:
        return sum(1 for n in self.nodes if n.status == NodeStatus.FAILED)

    @property
    def active_node(self) -> Optional[NodeExecution]:
        for n in self.nodes:
            if n.status == NodeStatus.RUNNING:
                return n
        return None


@dataclass
class WorkflowRoute:
    """Defines which agents run for a given intent."""
    intent:       str
    display_name: str
    agent_chain:  List[AgentType]
    description:  str = ""


# ─────────────────────────────────────────────────────────────
# Routing table
# ─────────────────────────────────────────────────────────────

WORKFLOW_ROUTES: List[WorkflowRoute] = [
    WorkflowRoute(
        intent="copo_mapping",
        display_name="CO-PO Mapping",
        agent_chain=[
            AgentType.INTENT_CLASSIFIER,
            AgentType.COPO_AGENT,
            AgentType.VALIDATION_AGENT,
            AgentType.RAG_RETRIEVAL,
            AgentType.RESPONSE_GENERATOR,
        ],
        description="Generate CO-PO correlation matrix and mapping analysis",
    ),
    WorkflowRoute(
        intent="attainment",
        display_name="Attainment Calculation",
        agent_chain=[
            AgentType.INTENT_CLASSIFIER,
            AgentType.ATTAINMENT_AGENT,
            AgentType.ANALYTICS_AGENT,
            AgentType.VALIDATION_AGENT,
            AgentType.RAG_RETRIEVAL,
            AgentType.RESPONSE_GENERATOR,
        ],
        description="Compute direct and indirect PO attainment",
    ),
    WorkflowRoute(
        intent="sar_generation",
        display_name="SAR Report Generation",
        agent_chain=[
            AgentType.INTENT_CLASSIFIER,
            AgentType.SAR_AGENT,
            AgentType.VALIDATION_AGENT,
            AgentType.RAG_RETRIEVAL,
            AgentType.RESPONSE_GENERATOR,
        ],
        description="Generate NBA SAR sections with evidence recommendations",
    ),
    WorkflowRoute(
        intent="continuous_improvement",
        display_name="Continuous Improvement",
        agent_chain=[
            AgentType.INTENT_CLASSIFIER,
            AgentType.CI_AGENT,
            AgentType.ANALYTICS_AGENT,
            AgentType.VALIDATION_AGENT,
            AgentType.RESPONSE_GENERATOR,
        ],
        description="Identify gaps and generate corrective action plans",
    ),
    WorkflowRoute(
        intent="analytics",
        display_name="Analytics & Insights",
        agent_chain=[
            AgentType.INTENT_CLASSIFIER,
            AgentType.ANALYTICS_AGENT,
            AgentType.RAG_RETRIEVAL,
            AgentType.RESPONSE_GENERATOR,
        ],
        description="Generate KPIs, trend analysis, and benchmarking",
    ),
    WorkflowRoute(
        intent="general_query",
        display_name="General Query",
        agent_chain=[
            AgentType.INTENT_CLASSIFIER,
            AgentType.RAG_RETRIEVAL,
            AgentType.RESPONSE_GENERATOR,
        ],
        description="General NBA accreditation knowledge retrieval",
    ),
]

# Map intent → route
_ROUTE_MAP: Dict[str, WorkflowRoute] = {r.intent: r for r in WORKFLOW_ROUTES}


# ─────────────────────────────────────────────────────────────
# Agent node metadata
# ─────────────────────────────────────────────────────────────

_AGENT_META: Dict[AgentType, Dict[str, str]] = {
    AgentType.INTENT_CLASSIFIER:  {"name": "Intent Classifier",   "icon": "🧠", "color": "purple"},
    AgentType.COPO_AGENT:         {"name": "CO-PO Agent",         "icon": "⬡",  "color": "blue"},
    AgentType.ATTAINMENT_AGENT:   {"name": "Attainment Agent",    "icon": "◈",  "color": "cyan"},
    AgentType.SAR_AGENT:          {"name": "SAR Agent",           "icon": "◉",  "color": "blue"},
    AgentType.CI_AGENT:           {"name": "CI Agent",            "icon": "🔄", "color": "yellow"},
    AgentType.ANALYTICS_AGENT:    {"name": "Analytics Agent",     "icon": "◇",  "color": "purple"},
    AgentType.VALIDATION_AGENT:   {"name": "Validation Agent",    "icon": "✓",  "color": "green"},
    AgentType.RAG_RETRIEVAL:      {"name": "RAG Retrieval",       "icon": "🔍", "color": "cyan"},
    AgentType.RESPONSE_GENERATOR: {"name": "Response Generator",  "icon": "📄", "color": "green"},
}


# ─────────────────────────────────────────────────────────────
# Simulated agent executors
# These call real agents when available; fall back to stubs.
# ─────────────────────────────────────────────────────────────

def _simulate_agent_execution(
    agent_type: AgentType,
    query: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Simulated agent execution. In production, replace with actual agent calls.
    Returns: {"output": str, "tokens": int, "metadata": dict}
    """
    simulated_outputs: Dict[AgentType, Callable[[], Dict[str, Any]]] = {
        AgentType.INTENT_CLASSIFIER: lambda: {
            "output": f"Intent classified as: {_classify_intent(query)}",
            "tokens": 45,
            "metadata": {"intent": _classify_intent(query), "confidence": 0.94},
        },
        AgentType.COPO_AGENT: lambda: {
            "output": "CO-PO correlation matrix generated. 12 COs mapped to 12 POs.",
            "tokens": 280,
            "metadata": {"co_count": 12, "po_count": 12, "avg_correlation": 2.1},
        },
        AgentType.ATTAINMENT_AGENT: lambda: {
            "output": "Attainment computed. Direct avg: 67.4%. Indirect avg: 72.1%.",
            "tokens": 320,
            "metadata": {"direct_avg": 67.4, "indirect_avg": 72.1, "threshold": 60.0},
        },
        AgentType.SAR_AGENT: lambda: {
            "output": "SAR sections generated for Criteria 1–8. 47 evidence items collected.",
            "tokens": 1200,
            "metadata": {"section_count": 8, "evidence_count": 47, "readiness": 78.5},
        },
        AgentType.CI_AGENT: lambda: {
            "output": "3 critical, 5 major gaps identified. 12 corrective actions planned.",
            "tokens": 450,
            "metadata": {"critical_gaps": 3, "major_gaps": 5, "actions": 12, "maturity": 64.0},
        },
        AgentType.ANALYTICS_AGENT: lambda: {
            "output": "KPI report generated. Readiness score: 74.2%. Risk: Medium.",
            "tokens": 380,
            "metadata": {"readiness": 74.2, "risk_level": "medium", "kpi_count": 18},
        },
        AgentType.VALIDATION_AGENT: lambda: {
            "output": "Validation passed. 2 warnings. NBA compliance: 81%.",
            "tokens": 120,
            "metadata": {"errors": 0, "warnings": 2, "compliance": 81.0},
        },
        AgentType.RAG_RETRIEVAL: lambda: {
            "output": "Retrieved 5 relevant documents from knowledge base.",
            "tokens": 680,
            "metadata": {"doc_count": 5, "avg_score": 0.87},
        },
        AgentType.RESPONSE_GENERATOR: lambda: {
            "output": "Structured response generated with citations.",
            "tokens": 420,
            "metadata": {"citation_count": 4},
        },
    }
    fn = simulated_outputs.get(agent_type, lambda: {"output": "Agent executed.", "tokens": 50, "metadata": {}})
    return fn()


def _classify_intent(query: str) -> str:
    query_lower = query.lower()
    if any(w in query_lower for w in ["co-po", "copo", "mapping", "correlation"]):
        return "copo_mapping"
    if any(w in query_lower for w in ["attainment", "achievement", "pass rate"]):
        return "attainment"
    if any(w in query_lower for w in ["sar", "self-assessment", "report", "criteria"]):
        return "sar_generation"
    if any(w in query_lower for w in ["improve", "gap", "corrective", "action", "ci"]):
        return "continuous_improvement"
    if any(w in query_lower for w in ["analytics", "kpi", "trend", "benchmark"]):
        return "analytics"
    return "general_query"


# ─────────────────────────────────────────────────────────────
# Session state helpers
# ─────────────────────────────────────────────────────────────

_WF_HISTORY_KEY  = "workflow_history"
_WF_CURRENT_KEY  = "workflow_current"
_WF_STATS_KEY    = "workflow_stats"


def _init_workflow_session() -> None:
    if _WF_HISTORY_KEY not in st.session_state:
        st.session_state[_WF_HISTORY_KEY] = deque(maxlen=50)
    if _WF_CURRENT_KEY not in st.session_state:
        st.session_state[_WF_CURRENT_KEY] = None
    if _WF_STATS_KEY not in st.session_state:
        st.session_state[_WF_STATS_KEY] = {
            "total_executions": 0,
            "successful":       0,
            "failed":           0,
            "total_tokens":     0,
            "total_cost_usd":   0.0,
        }


def _get_history() -> List[WorkflowExecution]:
    _init_workflow_session()
    return list(st.session_state[_WF_HISTORY_KEY])


def _save_execution(execution: WorkflowExecution) -> None:
    _init_workflow_session()
    st.session_state[_WF_HISTORY_KEY].appendleft(execution)
    st.session_state[_WF_CURRENT_KEY] = execution

    stats = st.session_state[_WF_STATS_KEY]
    stats["total_executions"] += 1
    stats["total_tokens"]     += execution.total_tokens
    stats["total_cost_usd"]   += execution.total_cost_usd
    if execution.status == WorkflowStatus.COMPLETED:
        stats["successful"] += 1
    elif execution.status == WorkflowStatus.FAILED:
        stats["failed"] += 1


# ─────────────────────────────────────────────────────────────
# WorkflowService
# ─────────────────────────────────────────────────────────────

class WorkflowService:
    """
    Orchestration service for LangGraph-based NBA accreditation workflows.
    Manages execution, routing, status tracking, and history.
    """

    COST_PER_1K_TOKENS = 0.002  # USD placeholder

    # ── Intent → Route ────────────────────────────────────────

    @staticmethod
    def route(query: str) -> WorkflowRoute:
        """Classify the query and return the appropriate workflow route."""
        intent = _classify_intent(query)
        return _ROUTE_MAP.get(intent, _ROUTE_MAP["general_query"])

    # ── Build execution plan ──────────────────────────────────

    @staticmethod
    def build_execution(
        query: str,
        triggered_by: str = "user",
        route: Optional[WorkflowRoute] = None,
    ) -> WorkflowExecution:
        """Create a WorkflowExecution with pre-populated nodes."""
        resolved_route = route or WorkflowService.route(query)
        nodes: List[NodeExecution] = []
        for agent_type in resolved_route.agent_chain:
            meta = _AGENT_META.get(agent_type, {"name": agent_type.value, "icon": "◆", "color": "blue"})
            nodes.append(NodeExecution(
                node_id=str(uuid.uuid4()),
                node_name=meta["name"],
                agent_type=agent_type,
                status=NodeStatus.PENDING,
            ))
        return WorkflowExecution(
            trigger_query=query,
            triggered_by=triggered_by,
            workflow_name=resolved_route.display_name,
            nodes=nodes,
            metadata={"route": resolved_route.intent, "description": resolved_route.description},
        )

    # ── Synchronous execution ─────────────────────────────────

    @staticmethod
    def execute(
        query: str,
        triggered_by: str = "user",
        on_node_update: Optional[Callable[[WorkflowExecution], None]] = None,
    ) -> WorkflowExecution:
        """
        Execute the workflow synchronously with simulated agent calls.

        Args:
            query: User query triggering the workflow.
            triggered_by: Username or system identifier.
            on_node_update: Optional callback after each node completes.

        Returns: Completed WorkflowExecution.
        """
        _init_workflow_session()
        execution = WorkflowService.build_execution(query, triggered_by)
        execution.status     = WorkflowStatus.RUNNING
        execution.started_at = time.time()
        context: Dict[str, Any] = {"query": query}

        log.info("workflow.execute.start",
                 execution_id=execution.execution_id,
                 route=execution.metadata.get("route"),
                 query=query[:80])

        try:
            for node in execution.nodes:
                node.status     = NodeStatus.RUNNING
                node.started_at = time.time()

                # Simulate network / compute delay
                import random
                delay = random.uniform(0.3, 1.2)
                time.sleep(delay)

                try:
                    result = _simulate_agent_execution(node.agent_type, query, context)
                    node.status        = NodeStatus.COMPLETED
                    node.completed_at  = time.time()
                    node.duration_ms   = int((node.completed_at - node.started_at) * 1000)
                    node.output_tokens = result.get("tokens", 0)
                    node.output_summary = result.get("output", "")
                    node.metadata.update(result.get("metadata", {}))
                    context[node.agent_type.value] = result
                    execution.total_tokens += node.output_tokens

                    log.info("workflow.node.completed",
                             node=node.node_name,
                             duration_ms=node.duration_ms)

                    if on_node_update:
                        on_node_update(execution)

                except Exception as node_err:
                    node.status       = NodeStatus.FAILED
                    node.completed_at = time.time()
                    node.duration_ms  = int((node.completed_at - node.started_at) * 1000)
                    node.error_message = str(node_err)
                    log.error("workflow.node.failed", node=node.node_name, error=str(node_err))

                    # Mark remaining nodes as skipped
                    idx = execution.nodes.index(node)
                    for remaining in execution.nodes[idx + 1:]:
                        remaining.status = NodeStatus.SKIPPED
                    execution.status    = WorkflowStatus.FAILED
                    execution.error_message = f"Node '{node.node_name}' failed: {node_err}"
                    break
            else:
                execution.status = WorkflowStatus.COMPLETED
                # Extract final response from last completed response-gen node
                for n in reversed(execution.nodes):
                    if n.agent_type == AgentType.RESPONSE_GENERATOR and n.output_summary:
                        execution.final_response = n.output_summary
                        break

            execution.completed_at  = time.time()
            execution.total_cost_usd = (execution.total_tokens / 1000) * WorkflowService.COST_PER_1K_TOKENS

            _save_execution(execution)
            log.info("workflow.execute.complete",
                     execution_id=execution.execution_id,
                     status=execution.status.value,
                     duration_ms=execution.duration_ms,
                     tokens=execution.total_tokens)

        except Exception as exc:
            execution.status        = WorkflowStatus.FAILED
            execution.error_message = str(exc)
            execution.completed_at  = time.time()
            _save_execution(execution)
            log.error("workflow.execute.error", error=str(exc))

        return execution

    # ── Async execution ───────────────────────────────────────

    @staticmethod
    async def execute_async(
        query: str,
        triggered_by: str = "user",
        on_node_update: Optional[Callable[[WorkflowExecution], None]] = None,
    ) -> WorkflowExecution:
        """Async variant of execute(). Wraps sync execution in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: WorkflowService.execute(query, triggered_by, on_node_update),
        )

    # ── Streaming execution ───────────────────────────────────

    @staticmethod
    def execute_streaming(
        query: str,
        triggered_by: str = "user",
    ) -> Generator[Tuple[WorkflowExecution, Optional[NodeExecution]], None, None]:
        """
        Execute workflow with streaming node updates.
        Yields (execution_snapshot, current_node) after each node step.
        """
        _init_workflow_session()
        execution = WorkflowService.build_execution(query, triggered_by)
        execution.status     = WorkflowStatus.RUNNING
        execution.started_at = time.time()
        context: Dict[str, Any] = {"query": query}

        for node in execution.nodes:
            node.status     = NodeStatus.RUNNING
            node.started_at = time.time()
            yield execution, node

            import random
            time.sleep(random.uniform(0.4, 1.0))

            try:
                result = _simulate_agent_execution(node.agent_type, query, context)
                node.status        = NodeStatus.COMPLETED
                node.completed_at  = time.time()
                node.duration_ms   = int((node.completed_at - node.started_at) * 1000)
                node.output_tokens = result.get("tokens", 0)
                node.output_summary = result.get("output", "")
                node.metadata.update(result.get("metadata", {}))
                context[node.agent_type.value] = result
                execution.total_tokens += node.output_tokens
            except Exception as exc:
                node.status        = NodeStatus.FAILED
                node.error_message = str(exc)
                execution.status   = WorkflowStatus.FAILED
                execution.error_message = str(exc)
                yield execution, node
                break

            yield execution, node

        if execution.status != WorkflowStatus.FAILED:
            execution.status = WorkflowStatus.COMPLETED

        execution.completed_at  = time.time()
        execution.total_cost_usd = (execution.total_tokens / 1000) * WorkflowService.COST_PER_1K_TOKENS
        _save_execution(execution)
        yield execution, None

    # ── History ───────────────────────────────────────────────

    @staticmethod
    def get_history(limit: int = 20) -> List[WorkflowExecution]:
        return _get_history()[:limit]

    @staticmethod
    def get_current() -> Optional[WorkflowExecution]:
        _init_workflow_session()
        return st.session_state.get(_WF_CURRENT_KEY)

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        _init_workflow_session()
        return dict(st.session_state[_WF_STATS_KEY])

    # ── Node update ───────────────────────────────────────────

    @staticmethod
    def update_node_status(
        execution: WorkflowExecution,
        node_id: str,
        status: NodeStatus,
        output_summary: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> WorkflowExecution:
        """Manually update a node's status (for external LangGraph callbacks)."""
        for node in execution.nodes:
            if node.node_id == node_id:
                node.status = status
                if output_summary:
                    node.output_summary = output_summary
                if error_message:
                    node.error_message = error_message
                if duration_ms is not None:
                    node.duration_ms = duration_ms
                if status == NodeStatus.RUNNING and node.started_at is None:
                    node.started_at = time.time()
                if status in (NodeStatus.COMPLETED, NodeStatus.FAILED):
                    node.completed_at = time.time()
                break
        return execution

    # ── Conversion for visualizer ─────────────────────────────

    @staticmethod
    def to_visualizer_workflow(execution: WorkflowExecution) -> Dict[str, Any]:
        """
        Convert WorkflowExecution to the dict format expected by
        components.workflow_visualizer.WorkflowDefinition.
        """
        from components.workflow_visualizer import (
            WorkflowDefinition,
            WorkflowEdge,
            WorkflowNode,
            NodeStatus as VizNodeStatus,
        )

        _status_map = {
            NodeStatus.PENDING:   VizNodeStatus.PENDING,
            NodeStatus.RUNNING:   VizNodeStatus.RUNNING,
            NodeStatus.COMPLETED: VizNodeStatus.COMPLETED,
            NodeStatus.FAILED:    VizNodeStatus.FAILED,
            NodeStatus.SKIPPED:   VizNodeStatus.SKIPPED,
        }

        viz_nodes = []
        for n in execution.nodes:
            meta = _AGENT_META.get(n.agent_type, {"name": n.node_name, "icon": "◆", "color": "blue"})
            dt_start = datetime.fromtimestamp(n.started_at, tz=timezone.utc) if n.started_at else None
            viz_nodes.append(WorkflowNode(
                node_id=n.node_id,
                name=meta["name"],
                description=n.output_summary or meta.get("color", "Awaiting execution"),
                icon=meta["icon"],
                color=meta["color"],
                status=_status_map.get(n.status, VizNodeStatus.PENDING),
                start_time=dt_start,
                duration_ms=n.duration_ms,
                output_preview=n.output_summary,
                error_message=n.error_message,
            ))

        # Build sequential edges
        viz_edges = []
        labels = ["route", "validate", "retrieve", "augment", "generate", "finalize", "output"]
        for i in range(len(viz_nodes) - 1):
            viz_edges.append(WorkflowEdge(
                from_node=viz_nodes[i].node_id,
                to_node=viz_nodes[i + 1].node_id,
                label=labels[i] if i < len(labels) else "→",
            ))

        return WorkflowDefinition(
            workflow_id=execution.execution_id,
            name=execution.workflow_name,
            description=execution.trigger_query[:80] if execution.trigger_query else "",
            nodes=viz_nodes,
            edges=viz_edges,
            status=execution.status.value,
            total_tokens=execution.total_tokens,
            total_cost=execution.total_cost_usd,
        )

    # ── Audit log integration ─────────────────────────────────

    @staticmethod
    def audit_execution(execution: WorkflowExecution, username: str = "system") -> None:
        """Write workflow execution summary to auth service audit log."""
        try:
            from services.auth_service import auth_service, AuditLogEntry
            auth_service.audit(
                action="WORKFLOW_EXECUTED",
                resource=f"workflow/{execution.execution_id}",
                status="success" if execution.status == WorkflowStatus.COMPLETED else "failure",
                detail=(
                    f"Route: {execution.metadata.get('route','unknown')} | "
                    f"Tokens: {execution.total_tokens} | "
                    f"Duration: {execution.duration_display}"
                ),
            )
        except Exception:
            pass  # Audit failure must not break workflow


# ─────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────

workflow_service = WorkflowService()
