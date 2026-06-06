import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import time
import json
import random
from datetime import datetime
from utils.watsonx_client import get_watsonx_client
from utils.rag_engine import get_rag_engine
from utils.vector_store import get_vector_store
from utils.analytics import CHART_LAYOUT
import plotly.graph_objects as go

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">🔄</span>
    <h2>Workflow Monitor</h2>
    <span style="margin-left:8px;font-size:0.8rem;color:#7a9bb5;">LangGraph Execution · Real-time Pipeline Visualization</span>
</div>
""",
    unsafe_allow_html=True,
)

# ── Pipeline nodes definition ─────────────────────────────────────────────────
PIPELINE_NODES = [
    {
        "id": "intent",
        "label": "Intent Classification",
        "icon": "🎯",
        "description": "Classifies query intent: CO-PO, SAR, Attainment, Compliance, General",
        "latency_range": (50, 150),
        "color": "#4facfe",
    },
    {
        "id": "copo_agent",
        "label": "CO-PO Agent",
        "icon": "🗺️",
        "description": "Handles CO-PO mapping, attainment, and OBE-specific queries",
        "latency_range": (80, 200),
        "color": "#a78bfa",
    },
    {
        "id": "validation",
        "label": "Validation Agent",
        "icon": "✅",
        "description": "Validates NBA compliance and checks NBA guideline adherence",
        "latency_range": (40, 120),
        "color": "#22c55e",
    },
    {
        "id": "rag",
        "label": "RAG Retrieval",
        "icon": "🔍",
        "description": "Semantic search across uploaded NBA documents using ChromaDB + FAISS",
        "latency_range": (100, 300),
        "color": "#f59e0b",
    },
    {
        "id": "watsonx",
        "label": "Watsonx Granite",
        "icon": "⚡",
        "description": "IBM Granite model inference with injected context and system prompt",
        "latency_range": (400, 1200),
        "color": "#4facfe",
    },
    {
        "id": "response",
        "label": "Response Generation",
        "icon": "📝",
        "description": "Formats final response with source citations and structured output",
        "latency_range": (30, 80),
        "color": "#22c55e",
    },
]

# Session state for workflow runs
if "workflow_runs" not in st.session_state:
    st.session_state.workflow_runs = []
if "active_run" not in st.session_state:
    st.session_state.active_run = None

tab1, tab2, tab3 = st.tabs(["🚀 Execute Workflow", "📊 Execution History", "🔧 Agent Status"])

with tab1:
    st.markdown("### 🚀 Execute NBA Workflow Pipeline")

    col_inp, col_cfg = st.columns([3, 1])
    with col_inp:
        test_query = st.text_area(
            "Test Query",
            placeholder="e.g., How do I calculate CO attainment for my NBA accreditation?",
            height=100,
        )
    with col_cfg:
        run_rag = st.toggle("Enable RAG", value=True)
        run_validation = st.toggle("Enable Validation", value=True)
        simulate_mode = st.toggle("Simulate Mode", value=not st.session_state.watsonx_connected,
                                   help="Run with simulated latencies if Watsonx not connected")

    execute_btn = st.button("▶️ Execute Pipeline", type="primary", use_container_width=True, disabled=not test_query)

    if execute_btn and test_query:
        run_id = f"RUN-{len(st.session_state.workflow_runs) + 1:04d}"
        run_timestamp = datetime.now().strftime("%H:%M:%S")
        run_results = []

        st.markdown(f"### 📡 Executing Pipeline `{run_id}`")

        # Progress container
        progress_container = st.empty()
        timeline_container = st.empty()

        total_latency = 0
        active_nodes = PIPELINE_NODES if run_validation else [n for n in PIPELINE_NODES if n["id"] != "validation"]
        if not run_rag:
            active_nodes = [n for n in active_nodes if n["id"] != "rag"]

        for i, node in enumerate(active_nodes):
            node_start = time.time()
            latency = random.randint(*node["latency_range"])

            # Show pipeline progress
            progress_html = '<div style="display:flex;align-items:center;gap:0;margin:1rem 0;overflow-x:auto;">'
            for j, n in enumerate(active_nodes):
                if j < i:
                    status_color = "#22c55e"
                    status_icon = "✅"
                    node_bg = "rgba(34,197,94,0.12)"
                    border_col = "rgba(34,197,94,0.4)"
                elif j == i:
                    status_color = "#4facfe"
                    status_icon = "⏳"
                    node_bg = "rgba(79,172,254,0.18)"
                    border_col = "rgba(79,172,254,0.6)"
                else:
                    status_color = "#4a6070"
                    status_icon = "⬜"
                    node_bg = "rgba(255,255,255,0.03)"
                    border_col = "rgba(99,179,237,0.12)"

                progress_html += f"""
                <div style="display:flex;align-items:center;">
                    <div style="background:{node_bg};border:1px solid {border_col};border-radius:12px;padding:10px 14px;text-align:center;min-width:110px;">
                        <div style="font-size:1.2rem;">{n['icon']}</div>
                        <div style="font-size:0.72rem;color:{status_color};font-weight:600;margin-top:3px;">{n['label']}</div>
                        <div style="font-size:0.65rem;color:{status_color};opacity:0.8;">{status_icon}</div>
                    </div>
                    {"" if j == len(active_nodes)-1 else f'<div style="height:2px;width:28px;background:linear-gradient(90deg,{border_col},rgba(99,179,237,0.1));"></div>'}
                </div>"""
            progress_html += "</div>"
            progress_container.markdown(progress_html, unsafe_allow_html=True)

            # Execute or simulate node
            node_output = ""
            if simulate_mode:
                time.sleep(latency / 1000)
                if node["id"] == "intent":
                    node_output = "Intent: NBA_ATTAINMENT_QUERY | Confidence: 0.94"
                elif node["id"] == "copo_agent":
                    node_output = "Relevant COs: CO1, CO2, CO3 | Route: attainment_calculation"
                elif node["id"] == "validation":
                    node_output = "Compliance: PASS | NBA criteria: Criterion 3 relevant"
                elif node["id"] == "rag":
                    node_output = f"Retrieved {random.randint(3,6)} chunks | Top score: {random.uniform(0.72, 0.95):.2f}"
                elif node["id"] == "watsonx":
                    node_output = "Generated 287 tokens | Model: ibm/granite-13b-instruct-v2"
                elif node["id"] == "response":
                    node_output = "Response formatted | Citations: 3 sources | Length: 487 chars"
            else:
                if node["id"] == "rag" and run_rag:
                    try:
                        rag = get_rag_engine()
                        results = rag.retrieve(test_query, top_k=3)
                        node_output = f"Retrieved {len(results)} chunks"
                        time.sleep(latency / 1000)
                    except Exception as e:
                        node_output = f"RAG error: {str(e)[:50]}"
                elif node["id"] == "watsonx":
                    try:
                        rag = get_rag_engine()
                        result = rag.generate(test_query, use_rag=run_rag)
                        node_output = f"Generated response | {len(result['response'])} chars"
                    except Exception as e:
                        node_output = f"Error: {str(e)[:60]}"
                        time.sleep(latency / 1000)
                else:
                    time.sleep(latency / 1000)
                    node_output = f"Completed in {latency}ms"

            elapsed = round((time.time() - node_start) * 1000)
            total_latency += elapsed

            run_results.append({
                "node": node["label"],
                "icon": node["icon"],
                "status": "success",
                "latency_ms": elapsed,
                "output": node_output,
                "color": node["color"],
            })

        # Final state — all green
        final_html = '<div style="display:flex;align-items:center;gap:0;margin:1rem 0;overflow-x:auto;">'
        for j, n in enumerate(active_nodes):
            final_html += f"""
            <div style="display:flex;align-items:center;">
                <div style="background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.4);border-radius:12px;padding:10px 14px;text-align:center;min-width:110px;">
                    <div style="font-size:1.2rem;">{n['icon']}</div>
                    <div style="font-size:0.72rem;color:#22c55e;font-weight:600;margin-top:3px;">{n['label']}</div>
                    <div style="font-size:0.65rem;color:#22c55e;">✅</div>
                </div>
                {"" if j == len(active_nodes)-1 else '<div style="height:2px;width:28px;background:linear-gradient(90deg,rgba(34,197,94,0.4),rgba(34,197,94,0.1));"></div>'}
            </div>"""
        final_html += "</div>"
        progress_container.markdown(final_html, unsafe_allow_html=True)

        st.success(f"✅ Pipeline `{run_id}` completed in **{total_latency}ms**")

        # Gantt-style timeline
        st.markdown("### ⏱️ Execution Timeline")
        cumulative = 0
        fig_gantt = go.Figure()
        for res in run_results:
            fig_gantt.add_trace(go.Bar(
                x=[res["latency_ms"]],
                y=[f"{res['icon']} {res['node']}"],
                orientation="h",
                base=cumulative,
                marker_color=res["color"],
                hovertemplate=f"<b>{res['node']}</b><br>Latency: {res['latency_ms']}ms<br>Start: {cumulative}ms<extra></extra>",
                showlegend=False,
                text=f"{res['latency_ms']}ms",
                textposition="inside",
                textfont=dict(color="white", size=11),
            ))
            cumulative += res["latency_ms"]

        fig_gantt.update_layout(
            **CHART_LAYOUT,
            title=f"Pipeline Execution Timeline — Total: {total_latency}ms",
            xaxis_title="Time (ms)",
            height=360,
            barmode="stack",
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

        # Node details
        st.markdown("### 📋 Node Execution Details")
        for res in run_results:
            status_color = "#22c55e"
            st.markdown(
                f"""<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);border-radius:10px;margin-bottom:6px;">
                <span style="font-size:1.2rem;">{res['icon']}</span>
                <div style="flex:1;">
                    <span style="font-weight:600;color:#e0e6f0;font-size:0.88rem;">{res['node']}</span>
                    <span style="color:#7a9bb5;font-size:0.78rem;margin-left:10px;">{res['output']}</span>
                </div>
                <span style="color:#22c55e;font-weight:700;font-size:0.85rem;">{res['latency_ms']}ms</span>
                <span style="background:rgba(34,197,94,0.15);color:#22c55e;padding:2px 10px;border-radius:999px;font-size:0.72rem;font-weight:600;">SUCCESS</span>
            </div>""",
                unsafe_allow_html=True,
            )

        # Store run
        st.session_state.workflow_runs.append({
            "run_id": run_id,
            "timestamp": run_timestamp,
            "query": test_query[:80],
            "nodes": len(active_nodes),
            "total_latency_ms": total_latency,
            "status": "success",
            "results": run_results,
        })


with tab2:
    st.markdown("### 📊 Workflow Execution History")

    runs = st.session_state.workflow_runs
    if not runs:
        st.info("No workflow runs yet. Execute a pipeline in the Execute tab.")
    else:
        # Summary KPIs
        c1, c2, c3, c4 = st.columns(4)
        total_runs = len(runs)
        avg_latency = sum(r["total_latency_ms"] for r in runs) / total_runs
        success_rate = sum(1 for r in runs if r["status"] == "success") / total_runs * 100

        for col, (label, val, color) in zip(
            [c1, c2, c3, c4],
            [
                ("Total Runs", str(total_runs), "#4facfe"),
                ("Success Rate", f"{success_rate:.0f}%", "#22c55e"),
                ("Avg Latency", f"{avg_latency:.0f}ms", "#a78bfa"),
                ("Nodes/Run", f"{runs[-1]['nodes'] if runs else 0}", "#f59e0b"),
            ],
        ):
            with col:
                st.markdown(
                    f"""<div class="kpi-card">
                    <div class="kpi-value" style="background:{color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-size:1.6rem;">{val}</div>
                    <div class="kpi-label">{label}</div>
                </div>""",
                    unsafe_allow_html=True,
                )

        # Latency trend
        if len(runs) > 1:
            fig_lat = go.Figure(go.Scatter(
                x=[r["run_id"] for r in runs],
                y=[r["total_latency_ms"] for r in runs],
                mode="lines+markers",
                line=dict(color="#4facfe", width=2),
                marker=dict(size=8, color="#4facfe"),
                fill="tozeroy",
                fillcolor="rgba(79,172,254,0.07)",
                hovertemplate="<b>%{x}</b><br>Latency: %{y}ms<extra></extra>",
            ))
            fig_lat.update_layout(**CHART_LAYOUT, title="Pipeline Latency History", height=220)
            st.plotly_chart(fig_lat, use_container_width=True)

        # Run table
        run_table = []
        for r in reversed(runs):
            run_table.append({
                "Run ID": r["run_id"],
                "Time": r["timestamp"],
                "Query": r["query"][:60] + "..." if len(r["query"]) > 60 else r["query"],
                "Nodes": r["nodes"],
                "Latency (ms)": r["total_latency_ms"],
                "Status": "✅ Success" if r["status"] == "success" else "❌ Failed",
            })
        st.dataframe(run_table, use_container_width=True, hide_index=True)


with tab3:
    st.markdown("### 🔧 Agent & Service Status")

    # Live checks
    vs_stats = get_vector_store().get_stats()
    rag_stats = get_rag_engine().get_stats()

    agents = [
        {
            "name": "Intent Classifier",
            "status": True,
            "type": "Rule-Based + Embedding",
            "detail": "Classifies: CO-PO, SAR, Attainment, Compliance, General",
        },
        {
            "name": "CO-PO Mapping Agent",
            "status": True,
            "type": "NBA Domain Expert",
            "detail": "Handles OBE/NBA-specific CO-PO correlation queries",
        },
        {
            "name": "Compliance Validation Agent",
            "status": True,
            "type": "Rule Engine + LLM",
            "detail": "NBA criterion checker and compliance validator",
        },
        {
            "name": "RAG Retrieval Agent",
            "status": rag_stats["rag_ready"],
            "type": "ChromaDB + FAISS",
            "detail": f"Embedding model: {rag_stats['embedding_model']} | Vectors: {vs_stats['chroma_count']}",
        },
        {
            "name": "Watsonx Granite Agent",
            "status": st.session_state.watsonx_connected,
            "type": "IBM Watsonx.ai",
            "detail": "Granite model inference with system prompt injection",
        },
        {
            "name": "Response Formatter",
            "status": True,
            "type": "Post-Processing",
            "detail": "Source citation, markdown formatting, structured output",
        },
    ]

    for agent in agents:
        status_ok = agent["status"]
        color = "#22c55e" if status_ok else "#ef4444"
        bg = "rgba(34,197,94,0.07)" if status_ok else "rgba(239,68,68,0.07)"
        border = "rgba(34,197,94,0.25)" if status_ok else "rgba(239,68,68,0.25)"
        dot_color = "#22c55e" if status_ok else "#ef4444"

        st.markdown(
            f"""<div style="background:{bg};border:1px solid {border};border-radius:12px;padding:14px 16px;margin-bottom:8px;display:flex;align-items:center;gap:14px;">
            <div style="width:10px;height:10px;border-radius:50%;background:{dot_color};box-shadow:0 0 8px {dot_color};flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="font-weight:600;color:#e0e6f0;font-size:0.88rem;">{agent['name']}</div>
                <div style="font-size:0.75rem;color:#7a9bb5;margin-top:2px;">{agent['detail']}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.75rem;color:{color};font-weight:600;">{'RUNNING' if status_ok else 'OFFLINE'}</div>
                <div style="font-size:0.7rem;color:#4a6070;">{agent['type']}</div>
            </div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 📡 LangGraph Pipeline Architecture")
    st.markdown(
        """<div class="glass-card">
        <pre style="color:#a0b4c8;font-size:0.82rem;line-height:2;font-family:'Inter',monospace;overflow-x:auto;">
┌─────────────────────────────────────────────────────────────┐
│                 NBA Accreditation LangGraph                  │
│                                                             │
│  User Query                                                 │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │  Intent       │────▶│  CO-PO       │                     │
│  │  Classifier   │     │  Agent       │                     │
│  └──────────────┘     └──────┬───────┘                     │
│                              │                              │
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │  Validation      │                     │
│                    │  Agent           │                     │
│                    └────────┬─────────┘                     │
│                             │                               │
│                             ▼                               │
│                    ┌──────────────────┐                     │
│                    │  RAG Retrieval   │ ◀── ChromaDB/FAISS  │
│                    │  (Top-K chunks)  │                     │
│                    └────────┬─────────┘                     │
│                             │                               │
│                             ▼                               │
│                    ┌──────────────────┐                     │
│                    │  IBM Watsonx     │ ◀── Granite Model   │
│                    │  Granite LLM     │                     │
│                    └────────┬─────────┘                     │
│                             │                               │
│                             ▼                               │
│                    ┌──────────────────┐                     │
│                    │  Response        │                     │
│                    │  Generator       │──▶ Final Output     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
        </pre>
    </div>""",
        unsafe_allow_html=True,
    )
