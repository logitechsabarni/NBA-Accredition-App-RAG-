"""
components/workflow_visualizer.py
Interactive LangGraph workflow visualizer with animated nodes,
execution status, timeline, and real-time state tracking.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components


# ─────────────────────────────────────────────────────────────
# Enumerations & data classes
# ─────────────────────────────────────────────────────────────

class NodeStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    SKIPPED   = "skipped"


@dataclass
class WorkflowNode:
    node_id:     str
    name:        str
    description: str
    icon:        str         = "◆"
    color:       str         = "blue"
    status:      NodeStatus  = NodeStatus.PENDING
    start_time:  Optional[datetime] = None
    end_time:    Optional[datetime] = None
    duration_ms: Optional[int]      = None
    output_preview: Optional[str]   = None
    error_message:  Optional[str]   = None
    metadata:    Dict[str, Any]     = field(default_factory=dict)


@dataclass
class WorkflowEdge:
    from_node: str
    to_node:   str
    label:     Optional[str] = None
    condition: Optional[str] = None


@dataclass
class WorkflowDefinition:
    workflow_id:  str
    name:         str
    description:  str
    nodes:        List[WorkflowNode] = field(default_factory=list)
    edges:        List[WorkflowEdge] = field(default_factory=list)
    created_at:   Optional[datetime] = None
    started_at:   Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status:       str = "pending"
    total_tokens: int = 0
    total_cost:   float = 0.0


# ─────────────────────────────────────────────────────────────
# Pre-built NBA Platform workflow
# ─────────────────────────────────────────────────────────────

def get_nba_workflow() -> WorkflowDefinition:
    """Return the default NBA Accreditation LangGraph workflow definition."""
    return WorkflowDefinition(
        workflow_id="nba-accreditation-v1",
        name="NBA Accreditation Workflow",
        description="End-to-end LangGraph pipeline for NBA accreditation intelligence",
        nodes=[
            WorkflowNode(
                node_id="intent_classifier",
                name="Intent Classification",
                description="Classify user query into accreditation domain",
                icon="🧠",
                color="purple",
            ),
            WorkflowNode(
                node_id="copo_agent",
                name="CO-PO Agent",
                description="Generate & validate CO-PO correlation matrix",
                icon="⬡",
                color="blue",
            ),
            WorkflowNode(
                node_id="validation_agent",
                name="Validation Agent",
                description="NBA compliance & schema validation",
                icon="✓",
                color="green",
            ),
            WorkflowNode(
                node_id="rag_retrieval",
                name="RAG Retrieval",
                description="Semantic search over accreditation knowledge base",
                icon="🔍",
                color="cyan",
            ),
            WorkflowNode(
                node_id="watsonx_granite",
                name="Watsonx Granite",
                description="IBM Granite LLM generation with RAG context",
                icon="◆",
                color="blue",
            ),
            WorkflowNode(
                node_id="response_gen",
                name="Response Generation",
                description="Format structured accreditation response",
                icon="📄",
                color="green",
            ),
        ],
        edges=[
            WorkflowEdge("intent_classifier", "copo_agent",      label="route"),
            WorkflowEdge("copo_agent",         "validation_agent",label="validate"),
            WorkflowEdge("validation_agent",   "rag_retrieval",   label="retrieve"),
            WorkflowEdge("rag_retrieval",      "watsonx_granite", label="augment"),
            WorkflowEdge("watsonx_granite",    "response_gen",    label="generate"),
        ],
    )


# ─────────────────────────────────────────────────────────────
# Status helpers
# ─────────────────────────────────────────────────────────────

_STATUS_PILL: Dict[NodeStatus, str] = {
    NodeStatus.PENDING:   '<span class="wf-status-pill waiting">WAITING</span>',
    NodeStatus.RUNNING:   '<span class="wf-status-pill running">RUNNING</span>',
    NodeStatus.COMPLETED: '<span class="wf-status-pill done">DONE</span>',
    NodeStatus.FAILED:    '<span class="wf-status-pill error">FAILED</span>',
    NodeStatus.SKIPPED:   '<span class="wf-status-pill waiting">SKIP</span>',
}

_STATUS_NODE_CLASS: Dict[NodeStatus, str] = {
    NodeStatus.PENDING:   "wf-node pending",
    NodeStatus.RUNNING:   "wf-node active",
    NodeStatus.COMPLETED: "wf-node completed",
    NodeStatus.FAILED:    "wf-node failed",
    NodeStatus.SKIPPED:   "wf-node pending",
}


def _duration_str(node: WorkflowNode) -> str:
    if node.duration_ms is not None:
        return f"{node.duration_ms}ms"
    if node.start_time and node.status == NodeStatus.RUNNING:
        elapsed = (datetime.now(timezone.utc) - node.start_time).total_seconds()
        return f"{elapsed:.1f}s ↺"
    return ""


def _connector_html(edge: Optional[WorkflowEdge] = None) -> str:
    label = edge.label if edge else "→"
    return (
        f'<div class="wf-connector">'
        f'<div class="wf-connector-line"></div>'
        f'<span style="font-size:0.6rem;color:var(--text-disabled);'
        f'white-space:nowrap;padding:0 4px;">{label}</span>'
        f'<div class="wf-connector-line"></div>'
        f'</div>'
    )


def _node_html(node: WorkflowNode) -> str:
    pill      = _STATUS_PILL[node.status]
    node_cls  = _STATUS_NODE_CLASS[node.status]
    dur       = _duration_str(node)
    dur_html  = (
        f'<span style="font-size:0.625rem;font-family:var(--font-mono);'
        f'color:var(--text-disabled);margin-left:4px;">{dur}</span>'
        if dur else ""
    )
    err_html  = (
        f'<div style="font-size:0.75rem;color:var(--wx-red);margin-top:4px;'
        f'font-family:var(--font-mono);">{node.error_message}</div>'
        if node.error_message else ""
    )
    out_html  = (
        f'<div style="font-size:0.75rem;color:var(--text-secondary);margin-top:4px;'
        f'font-family:var(--font-mono);max-height:40px;overflow:hidden;'
        f'text-overflow:ellipsis;">{node.output_preview}</div>'
        if node.output_preview else ""
    )
    return f"""
    <div class="{node_cls}">
      <div class="wf-node-icon {node.color}">{node.icon}</div>
      <div class="wf-node-content">
        <div class="wf-node-name">{node.name}{dur_html}</div>
        <div class="wf-node-desc">{node.description}</div>
        {err_html}{out_html}
      </div>
      {pill}
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Main vertical pipeline renderer
# ─────────────────────────────────────────────────────────────

def render_workflow_pipeline(
    workflow: WorkflowDefinition,
    title: str = "LangGraph Execution Pipeline",
    show_summary: bool = True,
) -> None:
    """
    Render a vertical workflow pipeline with animated status nodes.
    """
    completed = sum(1 for n in workflow.nodes if n.status == NodeStatus.COMPLETED)
    failed    = sum(1 for n in workflow.nodes if n.status == NodeStatus.FAILED)
    running   = sum(1 for n in workflow.nodes if n.status == NodeStatus.RUNNING)
    total     = len(workflow.nodes)

    # Summary bar
    if show_summary:
        st.markdown(
            f"""
            <div style="display:flex;gap:8px;margin-bottom:1rem;flex-wrap:wrap;">
              <span class="badge badge-blue">
                {total} nodes
              </span>
              <span class="badge badge-green">{completed} completed</span>
              {'<span class="badge badge-red">' + str(failed) + ' failed</span>' if failed else ''}
              {'<span class="badge badge-yellow">' + str(running) + ' running</span>' if running else ''}
              <span class="badge badge-purple" style="margin-left:auto;">
                {workflow.name}
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Nodes + connectors
    st.markdown(
        f'<div class="workflow-container"><div class="workflow-title">{title}</div>',
        unsafe_allow_html=True,
    )

    edge_map: Dict[str, WorkflowEdge] = {}
    for e in workflow.edges:
        edge_map[e.from_node] = e

    for i, node in enumerate(workflow.nodes):
        st.markdown(_node_html(node), unsafe_allow_html=True)
        if i < len(workflow.nodes) - 1:
            edge = edge_map.get(node.node_id)
            st.markdown(_connector_html(edge), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Timeline renderer
# ─────────────────────────────────────────────────────────────

def render_workflow_timeline(workflow: WorkflowDefinition) -> None:
    """
    Render a vertical event timeline for workflow execution.
    Shows only nodes that have been started.
    """
    active_nodes = [
        n for n in workflow.nodes
        if n.status in (NodeStatus.RUNNING, NodeStatus.COMPLETED, NodeStatus.FAILED)
    ]
    if not active_nodes:
        st.markdown(
            '<div style="font-size:0.875rem;color:var(--text-helper);'
            'text-align:center;padding:2rem;">No execution events yet.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="timeline">', unsafe_allow_html=True)
    for node in active_nodes:
        ts_str = ""
        if node.start_time:
            ts_str = node.start_time.strftime("%H:%M:%S")

        item_cls = {
            NodeStatus.RUNNING:   "running",
            NodeStatus.COMPLETED: "completed",
            NodeStatus.FAILED:    "failed",
        }.get(node.status, "pending")

        detail = node.output_preview or node.error_message or node.description
        dur    = f" ({_duration_str(node)})" if _duration_str(node) else ""

        st.markdown(
            f"""
            <div class="timeline-item {item_cls}">
              <div class="timeline-time">{ts_str}{dur}</div>
              <div class="timeline-event">{node.icon} {node.name}</div>
              <div class="timeline-detail">{detail[:80]}{"…" if len(detail)>80 else ""}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Interactive D3-style HTML visualizer (embedded iframe)
# ─────────────────────────────────────────────────────────────

def render_interactive_graph(workflow: WorkflowDefinition, height: int = 420) -> None:
    """
    Render an interactive HTML/SVG LangGraph visualizer using D3-like
    positioning embedded as an iframe component.
    """
    nodes_json = json.dumps([
        {
            "id":     n.node_id,
            "label":  n.name,
            "icon":   n.icon,
            "status": n.status.value,
            "desc":   n.description,
            "color": {
                "blue":   "#4589ff",
                "green":  "#42be65",
                "purple": "#be95ff",
                "cyan":   "#33b1ff",
                "yellow": "#f1c21b",
                "red":    "#fa4d56",
            }.get(n.color, "#4589ff"),
        }
        for n in workflow.nodes
    ])
    edges_json = json.dumps([
        {"from": e.from_node, "to": e.to_node, "label": e.label or "→"}
        for e in workflow.edges
    ])

    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: 'IBM Plex Mono', monospace;
    overflow: hidden;
  }}
  svg {{ width: 100%; height: {height}px; }}
  .node-group {{ cursor: pointer; }}
  .node-rect {{
    rx: 8; ry: 8;
    stroke-width: 1.5;
    transition: all 0.3s;
  }}
  .node-label {{
    fill: #f4f4f4;
    font-size: 11px;
    font-weight: 500;
    pointer-events: none;
    font-family: 'IBM Plex Sans', sans-serif;
  }}
  .node-icon {{
    fill: rgba(255,255,255,0.6);
    font-size: 14px;
    pointer-events: none;
  }}
  .edge-line {{
    stroke-width: 1.5;
    stroke: rgba(255,255,255,0.15);
    fill: none;
    marker-end: url(#arrow);
  }}
  .edge-label {{
    fill: #525252;
    font-size: 9px;
    font-family: 'IBM Plex Mono', monospace;
  }}
  @keyframes pulse {{
    0%,100% {{ opacity: 1; }}
    50%       {{ opacity: 0.5; }}
  }}
  .status-running {{ animation: pulse 1.5s ease-in-out infinite; }}
</style>
</head>
<body>
<svg id="graph" viewBox="0 0 760 {height}">
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8"
            refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="rgba(255,255,255,0.25)"/>
    </marker>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
</svg>

<script>
const nodes = {nodes_json};
const edges = {edges_json};

const W = 760, H = {height};
const NODE_W = 160, NODE_H = 52;
const cols = Math.min(3, nodes.length);
const rows = Math.ceil(nodes.length / cols);
const padX = (W - cols * NODE_W) / (cols + 1);
const padY = (H - rows * NODE_H) / (rows + 1);

const positions = {{}};
nodes.forEach((n, i) => {{
  const col = i % cols;
  const row = Math.floor(i / cols);
  positions[n.id] = {{
    x: padX + col * (NODE_W + padX) + NODE_W / 2,
    y: padY + row * (NODE_H + padY) + NODE_H / 2,
  }};
}});

const svg = document.getElementById('graph');

function svgEl(tag, attrs) {{
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}}

// Draw edges
edges.forEach(e => {{
  const s = positions[e.from], t = positions[e.to];
  if (!s || !t) return;
  const path = svgEl('path', {{
    class: 'edge-line',
    d: `M${{s.x}},${{s.y + NODE_H/2}} C${{s.x}},${{(s.y+t.y)/2 + 20}} ${{t.x}},${{(s.y+t.y)/2 - 20}} ${{t.x}},${{t.y - NODE_H/2}}`,
  }});
  svg.appendChild(path);

  const mx = (s.x + t.x) / 2;
  const my = (s.y + t.y) / 2;
  const lbl = svgEl('text', {{ class: 'edge-label', x: mx + 4, y: my, 'text-anchor':'middle' }});
  lbl.textContent = e.label;
  svg.appendChild(lbl);
}});

// Draw nodes
nodes.forEach(n => {{
  const pos = positions[n.id];
  if (!pos) return;
  const x = pos.x - NODE_W / 2, y = pos.y - NODE_H / 2;

  const statusColors = {{
    pending:   {{ fill:'rgba(28,35,51,0.9)',   stroke:'rgba(255,255,255,0.12)' }},
    running:   {{ fill:`${{n.color}}22`,        stroke: n.color }},
    completed: {{ fill:'rgba(66,190,101,0.10)', stroke:'rgba(66,190,101,0.50)' }},
    failed:    {{ fill:'rgba(250,77,86,0.10)',  stroke:'rgba(250,77,86,0.50)' }},
  }};
  const sc = statusColors[n.status] || statusColors.pending;

  const g = svgEl('g', {{
    class: `node-group ${{n.status === 'running' ? 'status-running' : ''}}`,
    transform: `translate(${{x}},${{y}})`,
  }});

  const rect = svgEl('rect', {{
    class: 'node-rect',
    x:0, y:0, width: NODE_W, height: NODE_H,
    fill: sc.fill, stroke: sc.stroke,
    ...(n.status === 'running' ? {{ filter:'url(#glow)' }} : {{}}),
  }});
  g.appendChild(rect);

  const iconEl = svgEl('text', {{
    class: 'node-icon',
    x: 14, y: 30,
    'dominant-baseline': 'middle',
  }});
  iconEl.textContent = n.icon;
  g.appendChild(iconEl);

  const labelEl = svgEl('text', {{
    class: 'node-label',
    x: 34, y: 20,
  }});
  labelEl.textContent = n.label;
  g.appendChild(labelEl);

  const descEl = svgEl('text', {{
    class: 'node-label',
    x: 34, y: 36,
    style: 'fill:#8d8d8d;font-size:9px;',
  }});
  descEl.textContent = n.desc.length > 28 ? n.desc.slice(0,28)+'…' : n.desc;
  g.appendChild(descEl);

  // Status dot
  const dotColors = {{ pending:'#525252',running:n.color,completed:'#42be65',failed:'#fa4d56' }};
  const dot = svgEl('circle', {{
    cx: NODE_W - 10, cy: 10, r: 4,
    fill: dotColors[n.status] || '#525252',
  }});
  g.appendChild(dot);

  svg.appendChild(g);
}});
</script>
</body>
</html>
"""
    components.html(html, height=height, scrolling=False)


# ─────────────────────────────────────────────────────────────
# Composite full visualizer
# ─────────────────────────────────────────────────────────────

def render_full_workflow_visualizer(
    workflow: Optional[WorkflowDefinition] = None,
    view_mode: str = "pipeline",
) -> None:
    """
    Render the complete workflow visualizer with tab switcher.

    Args:
        workflow: WorkflowDefinition; defaults to get_nba_workflow().
        view_mode: "pipeline" | "graph" | "timeline"
    """
    if workflow is None:
        workflow = get_nba_workflow()

    col_tabs, col_meta = st.columns([3, 1])
    with col_tabs:
        mode = st.radio(
            "wf_view",
            options=["Pipeline", "Graph", "Timeline"],
            horizontal=True,
            index=["Pipeline", "Graph", "Timeline"].index(
                view_mode.capitalize() if view_mode.capitalize() in ["Pipeline","Graph","Timeline"] else "Pipeline"
            ),
            label_visibility="collapsed",
        )
    with col_meta:
        st.markdown(
            f'<div style="text-align:right;padding-top:4px;">'
            f'<span class="badge badge-purple">{workflow.status.upper()}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if mode == "Pipeline":
        render_workflow_pipeline(workflow)
    elif mode == "Graph":
        render_interactive_graph(workflow)
    else:
        render_workflow_timeline(workflow)


# ─────────────────────────────────────────────────────────────
# Workflow state updater (for real-time simulation)
# ─────────────────────────────────────────────────────────────

def simulate_workflow_step(
    workflow: WorkflowDefinition,
    node_id: str,
    status: NodeStatus,
    duration_ms: Optional[int] = None,
    output_preview: Optional[str] = None,
    error_message: Optional[str] = None,
) -> WorkflowDefinition:
    """
    Update a single node's status in the workflow definition.
    Returns the modified workflow.
    """
    for node in workflow.nodes:
        if node.node_id == node_id:
            node.status = status
            if status == NodeStatus.RUNNING:
                node.start_time = datetime.now(timezone.utc)
            elif status in (NodeStatus.COMPLETED, NodeStatus.FAILED):
                node.end_time    = datetime.now(timezone.utc)
                node.duration_ms = duration_ms
            if output_preview:
                node.output_preview = output_preview
            if error_message:
                node.error_message  = error_message
            break
    return workflow
