import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import time
from utils.metrics import (
    calculate_co_attainment, calculate_po_attainment,
    generate_copo_matrix, compute_coverage,
    calculate_readiness_score, NBA_POS,
)
from utils.analytics import (
    readiness_gauge, co_attainment_bar, po_attainment_bar,
    readiness_trend, department_comparison, CHART_LAYOUT,
)
from utils.helpers import department_benchmarks, format_timestamp
from utils.watsonx_client import get_watsonx_client
from utils.vector_store import get_vector_store
from utils.rag_engine import get_rag_engine

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">📊</span>
    <h2>Executive Dashboard</h2>
    <div style="margin-left:auto;font-size:0.8rem;color:#7a9bb5;">
        Live · Updated every session
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Auto-generate demo data ──────────────────────────────────────────────────
np.random.seed(42)
cos = [f"CO{i}" for i in range(1, 7)]
pos = list(NBA_POS.keys())[:8]

co_direct = {co: np.random.uniform(55, 88) for co in cos}
co_indirect = {co: np.random.uniform(60, 85) for co in cos}
co_attainment = calculate_co_attainment(co_direct, co_indirect)

matrix = generate_copo_matrix(cos, pos)
po_attainment = calculate_po_attainment(co_attainment, matrix)
coverage = compute_coverage(matrix)
readiness = calculate_readiness_score(co_attainment, po_attainment, sar_completion=68.0, doc_score=72.0)

benchmarks = department_benchmarks()
rag_stats = get_rag_engine().get_stats()
vs_stats = get_vector_store().get_stats()

# ── System Health Check ───────────────────────────────────────────────────────
if st.button("🔄 Refresh Health Status", key="refresh_health"):
    with st.spinner("Checking system health..."):
        wc = get_watsonx_client()
        result = wc.test_connection()
        st.session_state.watsonx_connected = result["connected"]
        st.session_state.chromadb_ready = vs_stats["chroma_ready"]
        st.session_state.rag_ready = rag_stats["rag_ready"]
        st.session_state.last_health_check = format_timestamp()
    st.rerun()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown("### 📌 Key Performance Indicators")

kpis = [
    ("🎯", "Readiness Score", f"{readiness['score']}%", f"+{readiness['score']-60:.1f}% vs target", readiness["color"]),
    ("📐", "CO Coverage", f"{coverage['coverage_pct']}%", f"{coverage['mapped_cells']}/{coverage['total_cells']} mapped", "#4facfe"),
    ("🎓", "PO Coverage", f"{len([p for p in po_attainment.values() if p['attainment']>=60])}/{len(pos)}", "POs attained", "#a78bfa"),
    ("📋", "SAR Completion", "68%", "+5% this month", "#22c55e"),
    ("📁", "Documents", str(len(st.session_state.documents)), "in knowledge base", "#f59e0b"),
    ("🔢", "Vector Chunks", str(vs_stats.get("chroma_count", 0)), "indexed embeddings", "#4facfe"),
    ("💬", "AI Queries", str(st.session_state.ai_queries), "total queries", "#a78bfa"),
    ("⚡", "System Health", "98%", "all systems operational", "#22c55e"),
]

rows = [kpis[:4], kpis[4:]]
for row in rows:
    cols = st.columns(4)
    for col, (icon, label, value, delta, color) in zip(cols, row):
        with col:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div style="font-size:1.5rem;margin-bottom:0.25rem;">{icon}</div>
                <div class="kpi-value" style="background:linear-gradient(135deg,{color},{color}aa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{value}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-delta">{delta}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

st.divider()

# ── System Health Panel ───────────────────────────────────────────────────────
st.markdown("### ⚡ System Health")

health_items = [
    ("IBM Watsonx", st.session_state.watsonx_connected, "AI inference engine"),
    ("Granite Model", st.session_state.watsonx_connected, "ibm/granite-13b-instruct-v2"),
    ("ChromaDB", vs_stats.get("chroma_ready", False), f"{vs_stats.get('chroma_count', 0)} vectors stored"),
    ("FAISS Index", vs_stats.get("faiss_ready", False), f"{vs_stats.get('faiss_count', 0)} vectors indexed"),
    ("RAG Engine", rag_stats.get("rag_ready", False), f"top-k={rag_stats.get('top_k', 5)}"),
    ("Knowledge Base", len(st.session_state.documents) > 0, f"{len(st.session_state.documents)} documents"),
]

cols = st.columns(3)
for i, (name, status, detail) in enumerate(health_items):
    with cols[i % 3]:
        icon = "✅" if status else "❌"
        color = "#22c55e" if status else "#ef4444"
        bg = "rgba(34,197,94,0.08)" if status else "rgba(239,68,68,0.08)"
        border = "rgba(34,197,94,0.25)" if status else "rgba(239,68,68,0.25)"
        st.markdown(
            f"""
        <div style="background:{bg};border:1px solid {border};border-radius:12px;padding:12px 16px;margin-bottom:8px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:1rem;">{icon}</span>
                <span style="font-weight:600;color:#e0e6f0;font-size:0.88rem;">{name}</span>
                <span style="margin-left:auto;font-size:0.7rem;color:{color};background:rgba(0,0,0,0.2);padding:2px 8px;border-radius:10px;">{'ONLINE' if status else 'OFFLINE'}</span>
            </div>
            <div style="font-size:0.75rem;color:#7a9bb5;">{detail}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

if st.session_state.last_health_check:
    st.caption(f"Last health check: {st.session_state.last_health_check}")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("### 📈 Performance Analytics")

col1, col2 = st.columns([1, 2])

with col1:
    st.plotly_chart(readiness_gauge(readiness["score"]), use_container_width=True)

with col2:
    st.plotly_chart(readiness_trend(12), use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.plotly_chart(co_attainment_bar(co_attainment), use_container_width=True)

with col4:
    st.plotly_chart(po_attainment_bar(po_attainment), use_container_width=True)

st.plotly_chart(department_comparison(benchmarks), use_container_width=True)

# ── CO/PO Summary Tables ──────────────────────────────────────────────────────
st.markdown("### 📋 Attainment Summary")

tab1, tab2 = st.tabs(["CO Attainment", "PO Attainment"])

with tab1:
    co_rows = []
    for co, data in co_attainment.items():
        emoji = "✅" if data["attainment"] >= 60 else "❌"
        co_rows.append({
            "CO": co,
            "Direct (%)": data["direct"],
            "Indirect (%)": data["indirect"],
            "Attainment (%)": data["attainment"],
            "Target (%)": data["target"],
            "Gap": data["gap"],
            "Status": f"{emoji} {data['level']}",
        })
    co_df = pd.DataFrame(co_rows)
    st.dataframe(co_df, use_container_width=True, hide_index=True)

with tab2:
    po_rows = []
    for po, data in po_attainment.items():
        emoji = "✅" if data["attainment"] >= 60 else "⚠️"
        po_rows.append({
            "PO": po,
            "Description": NBA_POS.get(po, ""),
            "Attainment (%)": data["attainment"],
            "Status": f"{emoji} {data['level']}",
        })
    po_df = pd.DataFrame(po_rows)
    st.dataframe(po_df, use_container_width=True, hide_index=True)
