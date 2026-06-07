"""
pages/Workflow_Monitor.py
NBA Enterprise AI Platform — Workflow Monitor
Real-time LangGraph workflow visualization and execution monitoring.
IBM Watsonx enterprise styling.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Internal imports (resolved at runtime from the existing project structure)
# ---------------------------------------------------------------------------
try:
    from components import navbar as _navbar_mod
    from components import workflow_visualizer as _wv_mod
    from components import metric_cards as _mc_mod
    from components import charts as _charts_mod
    from services import workflow_service as _ws_mod

    _IMPORTS_OK = True
except ImportError:
    _IMPORTS_OK = False


# ---------------------------------------------------------------------------
# IBM Watsonx colour palette & global CSS
# ---------------------------------------------------------------------------

_IBM_CSS = """
<style>
/* ── Google Font: IBM Plex Sans ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ibm-blue-70:  #0043ce;
    --ibm-blue-60:  #0f62fe;
    --ibm-blue-50:  #4589ff;
    --ibm-blue-40:  #78a9ff;
    --ibm-gray-100: #161616;
    --ibm-gray-90:  #262626;
    --ibm-gray-80:  #393939;
    --ibm-gray-70:  #525252;
    --ibm-gray-60:  #6f6f6f;
    --ibm-gray-30:  #c6c6c6;
    --ibm-gray-10:  #f4f4f4;
    --ibm-green-40: #42be65;
    --ibm-green-50: #24a148;
    --ibm-red-50:   #da1e28;
    --ibm-red-40:   #fa4d56;
    --ibm-yellow-30:#f1c21b;
    --ibm-purple-50:#8a3ffc;
    --ibm-teal-40:  #3ddbd9;
    --card-bg:      #1e1e1e;
    --card-border:  #333333;
    --surface:      #262626;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: var(--ibm-gray-100) !important;
    color: var(--ibm-gray-10) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--ibm-gray-90) !important;
    border-right: 1px solid var(--card-border);
}
[data-testid="stSidebar"] * { color: var(--ibm-gray-10) !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}
[data-testid="stMetricValue"] { color: var(--ibm-blue-40) !important; font-weight: 600; }
[data-testid="stMetricLabel"] { color: var(--ibm-gray-30) !important; font-size: 0.75rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--card-border);
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--ibm-gray-30) !important;
    border-radius: 0 !important;
    font-size: 0.875rem !important;
    padding: 0.6rem 1.25rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--ibm-blue-40) !important;
    border-bottom: 2px solid var(--ibm-blue-60) !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: var(--ibm-blue-60) !important;
    color: white !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em;
    padding: 0.5rem 1.25rem !important;
    transition: background 0.15s;
}
.stButton > button:hover { background: var(--ibm-blue-70) !important; }
.stButton > button:disabled { background: var(--ibm-gray-70) !important; }

/* DataFrames / tables */
[data-testid="stDataFrame"] {
    border: 1px solid var(--card-border) !important;
}

/* Progress bars */
.stProgress > div > div { background: var(--ibm-blue-60) !important; }

/* Selectbox / inputs */
.stSelectbox > div > div,
.stTextInput > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 0 !important;
    color: var(--ibm-gray-10) !important;
}

/* Divider */
hr { border-color: var(--card-border) !important; }

/* Status pill helper */
.ibm-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 1px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.pill-success  { background: #0e2a1a; color: var(--ibm-green-40); border: 1px solid var(--ibm-green-50); }
.pill-running  { background: #001a40; color: var(--ibm-blue-40);  border: 1px solid var(--ibm-blue-60); }
.pill-error    { background: #2a0a0b; color: var(--ibm-red-40);   border: 1px solid var(--ibm-red-50); }
.pill-pending  { background: #2a2400; color: var(--ibm-yellow-30);border: 1px solid var(--ibm-yellow-30); }
.pill-idle     { background: var(--ibm-gray-80); color: var(--ibm-gray-30); border: 1px solid var(--card-border); }

/* Node card */
.node-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-left: 3px solid var(--ibm-blue-60);
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 1px;
    position: relative;
}
.node-card.active  { border-left-color: var(--ibm-blue-50); }
.node-card.success { border-left-color: var(--ibm-green-40); }
.node-card.error   { border-left-color: var(--ibm-red-50); }
.node-card.idle    { border-left-color: var(--ibm-gray-70); }

.node-title {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--ibm-gray-10);
    margin: 0 0 0.2rem;
}
.node-subtitle {
    font-size: 0.72rem;
    color: var(--ibm-gray-30);
    font-family: 'IBM Plex Mono', monospace;
}
.node-connector {
    text-align: center;
    color: var(--ibm-gray-60);
    font-size: 1.1rem;
    margin: 0.1rem 0;
    line-height: 1;
}

/* Timeline row */
.timeline-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--card-border);
    font-size: 0.8rem;
}
.timeline-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* Section header */
.section-header {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ibm-gray-60);
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--card-border);
}

/* Page title */
.page-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--ibm-gray-10);
    letter-spacing: -0.01em;
}
.page-subtitle {
    font-size: 0.8rem;
    color: var(--ibm-gray-60);
    margin-top: 0.15rem;
}

/* Live badge */
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--ibm-green-40);
    background: #0e2a1a;
    border: 1px solid var(--ibm-green-50);
    padding: 2px 8px;
    border-radius: 1px;
    vertical-align: middle;
}
.live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--ibm-green-40);
    animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}

/* Execution bar */
.exec-bar-container {
    background: var(--ibm-gray-80);
    height: 4px;
    border-radius: 2px;
    overflow: hidden;
    margin-top: 0.3rem;
}
.exec-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: var(--ibm-blue-60);
    transition: width 0.4s ease;
}
</style>
"""

# ---------------------------------------------------------------------------
# Workflow node definitions (the canonical LangGraph pipeline)
# ---------------------------------------------------------------------------

_WORKFLOW_NODES: list[dict[str, Any]] = [
    {
        "id": "intent_classifier",
        "label": "Intent Classifier",
        "description": "LangGraph router — classifies query intent and selects downstream agent",
        "icon": "🔍",
        "agent_class": "IntentClassifierAgent",
    },
    {
        "id": "copo_agent",
        "label": "COPO Agent",
        "description": "CO-PO mapping generation & correlation scoring",
        "icon": "🗺️",
        "agent_class": "COPOAgent",
    },
    {
        "id": "validation_agent",
        "label": "Validation Agent",
        "description": "NBA compliance & business rule validation",
        "icon": "✅",
        "agent_class": "ValidationAgent",
    },
    {
        "id": "rag_retrieval",
        "label": "RAG Retrieval",
        "description": "FAISS vector search + SentenceTransformer re-ranking",
        "icon": "📚",
        "agent_class": "RAGRetriever",
    },
    {
        "id": "watsonx_granite",
        "label": "Watsonx Granite",
        "description": "IBM Granite 13B inference via watsonx.ai — primary LLM router",
        "icon": "🤖",
        "agent_class": "GraniteLLMClient",
    },
    {
        "id": "response_gen",
        "label": "Response Generation",
        "description": "Structured response assembly, citation injection & audit logging",
        "icon": "✉️",
        "agent_class": "ResponseGenerator",
    },
]

_STATUS_COLOURS: dict[str, str] = {
    "success": "#42be65",
    "running": "#4589ff",
    "error":   "#fa4d56",
    "pending": "#f1c21b",
    "idle":    "#6f6f6f",
}

_STATUS_LABELS: dict[str, str] = {
    "success": "Completed",
    "running": "Running",
    "error":   "Error",
    "pending": "Queued",
    "idle":    "Idle",
}


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    if "wm_auto_refresh" not in st.session_state:
        st.session_state["wm_auto_refresh"] = False
    if "wm_selected_run_id" not in st.session_state:
        st.session_state["wm_selected_run_id"] = None
    if "wm_filter_status" not in st.session_state:
        st.session_state["wm_filter_status"] = "All"
    if "wm_mock_tick" not in st.session_state:
        st.session_state["wm_mock_tick"] = 0


# ---------------------------------------------------------------------------
# Data helpers — wrap service calls with graceful fallback mock data
# ---------------------------------------------------------------------------

def _get_workflow_stats() -> dict[str, Any]:
    """Fetch live stats or return deterministic mock data."""
    if _IMPORTS_OK:
        try:
            return _ws_mod.get_workflow_statistics()  # type: ignore[attr-defined]
        except Exception:
            pass
    tick = st.session_state.get("wm_mock_tick", 0)
    base_success = 1_284 + tick
    base_failed  = 37
    base_running = random.choice([0, 1, 2])
    base_queued  = random.randint(0, 5)
    avg_latency  = round(random.uniform(1.8, 3.2), 2)
    return {
        "total_executions":      base_success + base_failed + base_running,
        "successful_executions": base_success,
        "failed_executions":     base_failed,
        "running_executions":    base_running,
        "queued_executions":     base_queued,
        "avg_latency_seconds":   avg_latency,
        "p95_latency_seconds":   round(avg_latency * 1.6, 2),
        "throughput_per_hour":   random.randint(48, 120),
        "success_rate":          round(base_success / (base_success + base_failed) * 100, 1),
        "rag_hit_rate":          round(random.uniform(78.0, 94.0), 1),
        "watsonx_token_budget":  50_000,
        "watsonx_tokens_used":   random.randint(18_000, 44_000),
    }


def _get_node_statuses() -> list[dict[str, Any]]:
    """Return per-node runtime status."""
    if _IMPORTS_OK:
        try:
            return _ws_mod.get_node_statuses()  # type: ignore[attr-defined]
        except Exception:
            pass
    statuses = ["success", "success", "success", "success", "running", "idle"]
    random.shuffle(statuses)
    result = []
    for idx, node in enumerate(_WORKFLOW_NODES):
        status = statuses[idx % len(statuses)]
        latency = round(random.uniform(0.05, 1.8), 3) if status != "idle" else 0.0
        result.append({
            "node_id":      node["id"],
            "label":        node["label"],
            "icon":         node["icon"],
            "agent_class":  node["agent_class"],
            "description":  node["description"],
            "status":       status,
            "latency_ms":   round(latency * 1000),
            "invocations":  random.randint(50, 1400),
            "errors":       random.randint(0, 8),
            "last_run":     (datetime.now() - timedelta(seconds=random.randint(5, 300)))
                            .strftime("%H:%M:%S"),
        })
    return result


def _get_execution_history(limit: int = 25) -> list[dict[str, Any]]:
    """Return recent workflow execution records."""
    if _IMPORTS_OK:
        try:
            return _ws_mod.get_execution_history(limit=limit)  # type: ignore[attr-defined]
        except Exception:
            pass
    intents = [
        "CO-PO Mapping Query",
        "Attainment Calculation",
        "SAR Draft Generation",
        "Gap Analysis",
        "Validation Check",
        "Analytics Summary",
        "Evidence Lookup",
    ]
    users = ["admin@nba.edu", "faculty@nit.ac.in", "hod@vit.edu", "dean@iit.ac.in"]
    history = []
    for i in range(limit):
        ts = datetime.now() - timedelta(minutes=i * random.randint(2, 12))
        status = random.choices(
            ["success", "success", "success", "error", "running"],
            weights=[60, 10, 10, 10, 10],
        )[0]
        latency = round(random.uniform(0.9, 4.5), 2)
        history.append({
            "run_id":          f"run_{1300 - i:04d}",
            "timestamp":       ts.strftime("%Y-%m-%d %H:%M:%S"),
            "intent":          random.choice(intents),
            "user":            random.choice(users),
            "status":          status,
            "latency_s":       latency if status != "running" else None,
            "nodes_executed":  random.randint(3, 6) if status != "running" else random.randint(1, 4),
            "rag_chunks":      random.randint(0, 8),
            "tokens_used":     random.randint(400, 3200),
            "model_routed":    random.choice(["granite-13b", "gpt-4o"]),
        })
    return history


def _get_timeline_events() -> list[dict[str, Any]]:
    """Return the last N timeline events from active execution."""
    if _IMPORTS_OK:
        try:
            return _ws_mod.get_active_timeline()  # type: ignore[attr-defined]
        except Exception:
            pass
    events = []
    base = datetime.now() - timedelta(seconds=len(_WORKFLOW_NODES) * 0.8)
    statuses_seq = ["success", "success", "success", "success", "running", "pending"]
    for idx, node in enumerate(_WORKFLOW_NODES):
        status = statuses_seq[idx]
        ts = base + timedelta(seconds=idx * 0.75)
        events.append({
            "timestamp": ts.strftime("%H:%M:%S.%f")[:-3],
            "node":      node["label"],
            "event":     "completed" if status == "success" else ("started" if status == "running" else "queued"),
            "status":    status,
            "detail":    f"{random.randint(50, 900)} ms" if status == "success" else "—",
        })
    return events


# ---------------------------------------------------------------------------
# Sub-renders
# ---------------------------------------------------------------------------

def _render_kpi_strip(stats: dict[str, Any]) -> None:
    """Render the top KPI metric strip."""
    cols = st.columns(7)
    metrics = [
        ("Total Runs",       f"{stats['total_executions']:,}",           None),
        ("Success Rate",     f"{stats['success_rate']}%",                 "+0.4%"),
        ("Avg Latency",      f"{stats['avg_latency_seconds']}s",          None),
        ("P95 Latency",      f"{stats['p95_latency_seconds']}s",          None),
        ("Throughput/hr",    f"{stats['throughput_per_hour']}",           None),
        ("RAG Hit Rate",     f"{stats['rag_hit_rate']}%",                 None),
        ("Running Now",      str(stats["running_executions"]),             None),
    ]
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            st.metric(label, value, delta)


def _render_workflow_graph(node_statuses: list[dict[str, Any]]) -> None:
    """Render the LangGraph pipeline as a vertical node chain."""
    st.markdown("<div class='section-header'>LangGraph Execution Pipeline</div>", unsafe_allow_html=True)

    node_map = {n["node_id"]: n for n in node_statuses}

    cols = st.columns([2, 1])
    with cols[0]:
        for idx, node_def in enumerate(_WORKFLOW_NODES):
            nid   = node_def["id"]
            ndata = node_map.get(nid, {})
            status  = ndata.get("status", "idle")
            latency = ndata.get("latency_ms", 0)
            inv     = ndata.get("invocations", 0)
            errs    = ndata.get("errors", 0)
            colour  = _STATUS_COLOURS.get(status, "#6f6f6f")
            label_s = _STATUS_LABELS.get(status, "Idle")

            card_class = f"node-card {status}"
            st.markdown(
                f"""
                <div class="{card_class}">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                      <div class="node-title">{node_def['icon']} &nbsp;{node_def['label']}</div>
                      <div class="node-subtitle">{node_def['agent_class']}</div>
                      <div class="node-subtitle" style="margin-top:4px; color:#6f6f6f;">{node_def['description']}</div>
                    </div>
                    <div style="text-align:right;">
                      <span class="ibm-pill pill-{status}">{label_s}</span>
                      <div class="node-subtitle" style="margin-top:6px;">
                        {f'{latency} ms' if latency else '—'} &nbsp;·&nbsp;
                        {inv:,} calls &nbsp;·&nbsp;
                        {errs} err
                      </div>
                    </div>
                  </div>
                  {"" if status != "running" else
                   '<div class="exec-bar-container" style="margin-top:8px;"><div class="exec-bar-fill" style="width:60%;"></div></div>'}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if idx < len(_WORKFLOW_NODES) - 1:
                st.markdown(
                    '<div class="node-connector">│</div>',
                    unsafe_allow_html=True,
                )

    with cols[1]:
        st.markdown("<div class='section-header'>Node Legend</div>", unsafe_allow_html=True)
        for status_key, colour in _STATUS_COLOURS.items():
            st.markdown(
                f"""<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:0.8rem;">
                      <div style="width:10px;height:10px;border-radius:50%;background:{colour};flex-shrink:0;"></div>
                      <span style="color:#c6c6c6;">{_STATUS_LABELS[status_key]}</span>
                    </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-header' style='margin-top:1.5rem;'>Active Run</div>", unsafe_allow_html=True)
        running = [n for n in node_statuses if n.get("status") == "running"]
        if running:
            r = running[0]
            st.markdown(
                f"""<div style="font-size:0.78rem; color:#4589ff; font-family:'IBM Plex Mono',monospace;">
                    ▶ {r['label']}</div>
                    <div style="font-size:0.7rem; color:#6f6f6f; margin-top:3px;">
                    Last heartbeat: {r['last_run']}</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='font-size:0.78rem; color:#6f6f6f;'>No active execution</div>",
                unsafe_allow_html=True,
            )


def _render_execution_timeline(events: list[dict[str, Any]]) -> None:
    """Render live execution event timeline."""
    st.markdown("<div class='section-header'>Execution Timeline — Active Run</div>", unsafe_allow_html=True)
    if not events:
        st.info("No active workflow execution.")
        return

    for ev in events:
        colour = _STATUS_COLOURS.get(ev["status"], "#6f6f6f")
        st.markdown(
            f"""<div class="timeline-row">
                  <div class="timeline-dot" style="background:{colour};"></div>
                  <span style="color:#6f6f6f; font-family:'IBM Plex Mono',monospace; font-size:0.72rem; flex-shrink:0;">{ev['timestamp']}</span>
                  <span style="color:#c6c6c6; flex:1;">{ev['node']}</span>
                  <span style="color:#6f6f6f;">{ev['event'].upper()}</span>
                  <span style="color:#4589ff; font-family:'IBM Plex Mono',monospace;">{ev['detail']}</span>
               </div>""",
            unsafe_allow_html=True,
        )


def _render_agent_status_cards(node_statuses: list[dict[str, Any]]) -> None:
    """Render compact per-agent status cards in a 3-column grid."""
    st.markdown("<div class='section-header'>Agent Status Cards</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, node in enumerate(node_statuses):
        status  = node.get("status", "idle")
        colour  = _STATUS_COLOURS.get(status, "#6f6f6f")
        label_s = _STATUS_LABELS.get(status, "Idle")
        pill_c  = f"pill-{status}"
        with cols[idx % 3]:
            st.markdown(
                f"""<div style="background:#1e1e1e; border:1px solid #333; border-top:3px solid {colour};
                               padding:0.85rem; border-radius:1px; margin-bottom:0.75rem;">
                      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                        <span style="font-size:0.82rem; font-weight:600; color:#f4f4f4;">
                          {node['icon']} {node['label']}
                        </span>
                        <span class="ibm-pill {pill_c}">{label_s}</span>
                      </div>
                      <div style="font-size:0.7rem; color:#6f6f6f; font-family:'IBM Plex Mono',monospace; margin-bottom:0.5rem;">
                        {node['agent_class']}
                      </div>
                      <div style="display:flex; gap:1rem; font-size:0.72rem; color:#c6c6c6;">
                        <div><span style="color:#6f6f6f;">Calls</span><br/><strong>{node['invocations']:,}</strong></div>
                        <div><span style="color:#6f6f6f;">Latency</span><br/><strong>{node['latency_ms']} ms</strong></div>
                        <div><span style="color:#6f6f6f;">Errors</span><br/><strong style="color:{'#fa4d56' if node['errors']>0 else '#42be65'};">{node['errors']}</strong></div>
                        <div><span style="color:#6f6f6f;">Last run</span><br/><strong>{node['last_run']}</strong></div>
                      </div>
                    </div>""",
                unsafe_allow_html=True,
            )


def _render_execution_history_table(history: list[dict[str, Any]], filter_status: str) -> None:
    """Render the execution history table with filtering."""
    st.markdown("<div class='section-header'>Execution History</div>", unsafe_allow_html=True)

    filtered = history if filter_status == "All" else [
        r for r in history if r["status"] == filter_status.lower()
    ]
    if not filtered:
        st.info("No executions match the selected filter.")
        return

    import pandas as pd

    rows = []
    for r in filtered:
        status_label = _STATUS_LABELS.get(r["status"], r["status"].title())
        rows.append({
            "Run ID":          r["run_id"],
            "Timestamp":       r["timestamp"],
            "Intent":          r["intent"],
            "User":            r["user"],
            "Status":          status_label,
            "Latency (s)":     r["latency_s"] if r["latency_s"] is not None else "—",
            "Nodes":           r["nodes_executed"],
            "RAG Chunks":      r["rag_chunks"],
            "Tokens":          r["tokens_used"],
            "Model":           r["model_routed"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Run ID": st.column_config.TextColumn(width="small"),
            "Latency (s)": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    # Export
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Export CSV",
        data=csv_bytes,
        file_name=f"workflow_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="wm_export_csv",
    )


def _render_latency_chart(history: list[dict[str, Any]]) -> None:
    """Render a simple per-run latency line chart using Plotly via st.plotly_chart."""
    try:
        import plotly.graph_objects as go
        import pandas as pd

        completed = [r for r in history if r["latency_s"] is not None]
        if not completed:
            return

        df = pd.DataFrame(completed).head(20).iloc[::-1]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["latency_s"],
            mode="lines+markers",
            line=dict(color="#4589ff", width=2),
            marker=dict(size=5, color="#4589ff"),
            name="Latency (s)",
            fill="tozeroy",
            fillcolor="rgba(69,137,255,0.08)",
        ))
        fig.update_layout(
            paper_bgcolor="#161616",
            plot_bgcolor="#1e1e1e",
            font=dict(family="IBM Plex Sans", color="#c6c6c6", size=11),
            margin=dict(l=40, r=20, t=30, b=60),
            xaxis=dict(showgrid=False, linecolor="#333", tickangle=-30, tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#333", linecolor="#333", title="seconds"),
            height=220,
            title=dict(text="End-to-End Latency — Last 20 Runs", font=dict(size=12, color="#f4f4f4")),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Install plotly for the latency chart.")


def _render_token_usage_chart(stats: dict[str, Any]) -> None:
    """Render a Plotly gauge for Watsonx token budget consumption."""
    try:
        import plotly.graph_objects as go

        used   = stats["watsonx_tokens_used"]
        budget = stats["watsonx_token_budget"]
        pct    = used / budget * 100

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=used,
            delta={"reference": budget * 0.7, "valueformat": ","},
            title={"text": "Watsonx Token Usage", "font": {"color": "#f4f4f4", "size": 12}},
            number={"valueformat": ",", "font": {"color": "#4589ff", "size": 20}},
            gauge={
                "axis": {"range": [0, budget], "tickcolor": "#6f6f6f", "nticks": 5},
                "bar":  {"color": "#0f62fe"},
                "bgcolor": "#1e1e1e",
                "bordercolor": "#333",
                "steps": [
                    {"range": [0, budget * 0.6],  "color": "#0e2a1a"},
                    {"range": [budget * 0.6, budget * 0.85], "color": "#2a2400"},
                    {"range": [budget * 0.85, budget], "color": "#2a0a0b"},
                ],
                "threshold": {"line": {"color": "#fa4d56", "width": 2}, "value": budget * 0.90},
            },
        ))
        fig.update_layout(
            paper_bgcolor="#161616",
            font=dict(family="IBM Plex Sans", color="#c6c6c6"),
            margin=dict(l=30, r=30, t=50, b=10),
            height=200,
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        token_pct = stats["watsonx_tokens_used"] / stats["watsonx_token_budget"]
        st.progress(token_pct, text=f"Watsonx Tokens: {stats['watsonx_tokens_used']:,} / {stats['watsonx_token_budget']:,}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render() -> None:  # noqa: C901
    """
    Render the Workflow Monitor page.
    Called by the Streamlit multi-page router (app.py).
    """
    # ── Config ──────────────────────────────────────────────────────────────
    st.set_page_config(
        page_title="Workflow Monitor — NBA AI Platform",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_IBM_CSS, unsafe_allow_html=True)
    _init_session_state()

    # ── Navbar ───────────────────────────────────────────────────────────────
    if _IMPORTS_OK:
        try:
            _navbar_mod.render(active_page="Workflow Monitor")  # type: ignore[attr-defined]
        except Exception:
            pass

    # ── Sidebar controls ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='font-size:0.7rem; font-weight:700; letter-spacing:0.08em; "
            "text-transform:uppercase; color:#6f6f6f; padding:0.5rem 0 0.75rem;'>Monitor Controls</div>",
            unsafe_allow_html=True,
        )

        auto_refresh = st.toggle("Auto-refresh (10 s)", value=st.session_state["wm_auto_refresh"])
        st.session_state["wm_auto_refresh"] = auto_refresh

        filter_status = st.selectbox(
            "Filter history by status",
            ["All", "Success", "Error", "Running", "Pending"],
            index=0,
            key="wm_filter_status_select",
        )
        st.session_state["wm_filter_status"] = filter_status

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.7rem; font-weight:700; letter-spacing:0.08em; "
            "text-transform:uppercase; color:#6f6f6f; margin-bottom:0.5rem;'>Quick Actions</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.session_state["wm_mock_tick"] = st.session_state.get("wm_mock_tick", 0) + 1
            st.rerun()

        if st.button("⏸ Pause Workflows", use_container_width=True, disabled=True):
            pass

        if st.button("🗑 Clear History", use_container_width=True, disabled=True):
            pass

        st.markdown("---")
        st.markdown(
            f"""<div style='font-size:0.72rem; color:#6f6f6f; line-height:1.6;'>
              <strong style='color:#c6c6c6;'>Platform</strong><br/>
              NBA Enterprise AI v2.0<br/>
              LangGraph 0.1.x<br/>
              Watsonx.ai granite-13b<br/>
              FAISS + SentenceTransformers
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Page header ─────────────────────────────────────────────────────────
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.markdown(
            """<div class="page-title">⚙️ Workflow Monitor</div>
               <div class="page-subtitle">LangGraph execution pipeline — real-time agent orchestration visibility</div>""",
            unsafe_allow_html=True,
        )
    with hcol2:
        st.markdown(
            '<div style="padding-top:0.4rem;">'
            '<span class="live-badge"><span class="live-dot"></span> LIVE</span>'
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:0.6rem 0 1rem;'/>", unsafe_allow_html=True)

    # ── Fetch data ───────────────────────────────────────────────────────────
    stats        = _get_workflow_stats()
    node_statuses = _get_node_statuses()
    history      = _get_execution_history(limit=30)
    timeline     = _get_execution_timeline()

    # ── KPI strip ────────────────────────────────────────────────────────────
    _render_kpi_strip(stats)

    st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)

    # ── Main tabs ────────────────────────────────────────────────────────────
    tab_pipeline, tab_agents, tab_history, tab_metrics = st.tabs(
        ["Pipeline Visualizer", "Agent Status", "Execution History", "Performance Metrics"]
    )

    # ── Tab 1: Pipeline ───────────────────────────────────────────────────────
    with tab_pipeline:
        left_col, right_col = st.columns([3, 2])
        with left_col:
            _render_workflow_graph(node_statuses)
        with right_col:
            _render_execution_timeline(timeline)

    # ── Tab 2: Agent Status ───────────────────────────────────────────────────
    with tab_agents:
        _render_agent_status_cards(node_statuses)

        st.markdown("<div class='section-header'>Aggregate Node Metrics</div>", unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            import pandas as pd

            df_nodes = pd.DataFrame(node_statuses)
            fig = go.Figure(go.Bar(
                x=df_nodes["label"],
                y=df_nodes["invocations"],
                marker=dict(
                    color=df_nodes["invocations"],
                    colorscale=[[0, "#1a3a6e"], [1, "#4589ff"]],
                    showscale=False,
                ),
                text=df_nodes["invocations"],
                textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="#161616",
                plot_bgcolor="#1e1e1e",
                font=dict(family="IBM Plex Sans", color="#c6c6c6", size=11),
                margin=dict(l=40, r=20, t=20, b=80),
                xaxis=dict(showgrid=False, linecolor="#333", tickangle=-20),
                yaxis=dict(gridcolor="#333", linecolor="#333", title="Total Invocations"),
                height=260,
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for detailed node charts.")

    # ── Tab 3: History ────────────────────────────────────────────────────────
    with tab_history:
        _render_execution_history_table(history, st.session_state["wm_filter_status"])

    # ── Tab 4: Performance ────────────────────────────────────────────────────
    with tab_metrics:
        m_left, m_right = st.columns(2)
        with m_left:
            _render_latency_chart(history)
        with m_right:
            _render_token_usage_chart(stats)

        st.markdown("<div class='section-header'>Model Routing Distribution</div>", unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go

            granite_pct = round(sum(1 for r in history if r["model_routed"] == "granite-13b") / len(history) * 100)
            gpt4o_pct   = 100 - granite_pct

            fig = go.Figure(go.Pie(
                labels=["Watsonx Granite-13B", "OpenAI GPT-4o"],
                values=[granite_pct, gpt4o_pct],
                hole=0.62,
                marker=dict(colors=["#0f62fe", "#8a3ffc"]),
                textinfo="label+percent",
                textfont=dict(family="IBM Plex Sans", size=11, color="#f4f4f4"),
            ))
            fig.update_layout(
                paper_bgcolor="#161616",
                font=dict(family="IBM Plex Sans", color="#c6c6c6"),
                showlegend=True,
                legend=dict(font=dict(color="#c6c6c6")),
                margin=dict(l=20, r=20, t=30, b=20),
                height=240,
                title=dict(text="LLM Router — Last 30 Runs", font=dict(size=12, color="#f4f4f4")),
                annotations=[dict(
                    text=f"<b>{granite_pct}%</b><br>Granite",
                    x=0.5, y=0.5,
                    font=dict(size=13, color="#4589ff"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

    # ── Auto-refresh logic ───────────────────────────────────────────────────
    if st.session_state["wm_auto_refresh"]:
        time.sleep(10)
        st.session_state["wm_mock_tick"] = st.session_state.get("wm_mock_tick", 0) + 1
        st.rerun()


def _get_execution_timeline() -> list[dict[str, Any]]:
    """Alias used internally before service import resolves."""
    return _get_timeline_events()


# ---------------------------------------------------------------------------
# Standalone dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    render()
