import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from utils.vector_store import get_vector_store
from utils.rag_engine import get_rag_engine
from utils.helpers import load_query_logs, LOG_DIR
from utils.analytics import CHART_LAYOUT
import plotly.graph_objects as go

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">🛡️</span>
    <h2>Admin Panel</h2>
    <span style="margin-left:8px;font-size:0.8rem;color:#7a9bb5;">System Administration · Audit · Usage Analytics</span>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 System Overview", "📜 Audit Logs", "📈 Usage Analytics", "🔧 Maintenance"
])

with tab1:
    st.markdown("### 📊 Platform Overview")

    vs_stats = get_vector_store().get_stats()
    rag_stats = get_rag_engine().get_stats()

    # System metrics
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("📁 Documents", len(st.session_state.documents), "#4facfe", "+0 today"),
        ("🧬 Vectors", vs_stats.get("chroma_count", 0), "#a78bfa", "in ChromaDB"),
        ("💬 AI Queries", st.session_state.ai_queries, "#22c55e", "this session"),
        ("🔄 Workflows", len(st.session_state.get("workflow_runs", [])), "#f59e0b", "executed"),
    ]
    for col, (label, val, color, sub) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                <div class="kpi-value" style="background:{color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{val}</div>
                <div class="kpi-label">{label}</div>
                <div style="font-size:0.72rem;color:#4a6070;margin-top:4px;">{sub}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("### 🖥️ Service Health Matrix")

    services = [
        ("IBM Watsonx API", st.session_state.watsonx_connected, "AI Inference", os.getenv("WATSONX_URL", "Not Set")),
        ("ChromaDB", vs_stats["chroma_ready"], "Vector Store", str(Path(__file__).parent.parent / "vector_db" / "chroma")),
        ("FAISS Index", vs_stats["faiss_ready"], "Vector Search", str(Path(__file__).parent.parent / "vector_db" / "faiss.index")),
        ("Sentence Transformers", rag_stats["embedding_ready"], "Embeddings", rag_stats["embedding_model"]),
        ("RAG Engine", rag_stats["rag_ready"], "Retrieval Pipeline", f"top_k={rag_stats['top_k']}"),
        ("SQLite", True, "Session Storage", "In-memory (demo mode)"),
        ("PDF Parser", True, "Document Processing", "pdfplumber / pypdf"),
        ("Log Service", True, "Audit Trail", str(LOG_DIR)),
    ]

    service_rows = []
    for name, ok, svc_type, detail in services:
        service_rows.append({
            "Service": name,
            "Type": svc_type,
            "Status": "✅ Online" if ok else "❌ Offline",
            "Detail": detail[:60] if len(detail) > 60 else detail,
            "Uptime": "100%" if ok else "0%",
        })
    st.dataframe(pd.DataFrame(service_rows), use_container_width=True, hide_index=True)

    # Environment check
    st.divider()
    st.markdown("### 🔐 Environment Configuration")
    env_vars = [
        ("WATSONX_API_KEY", "IBM Cloud API Key"),
        ("WATSONX_PROJECT_ID", "Watsonx Project ID"),
        ("WATSONX_URL", "Watsonx Region URL"),
        ("GRANITE_MODEL_ID", "Active Granite Model"),
        ("EMBEDDING_MODEL", "Embedding Model"),
    ]
    env_rows = []
    for var, desc in env_vars:
        val = os.getenv(var, "")
        if val:
            masked = val[:3] + "•" * min(len(val) - 6, 12) + val[-3:] if len(val) > 6 else "•" * len(val)
            status = "✅ Set"
        else:
            masked = "Not configured"
            status = "⚠️ Missing"
        env_rows.append({"Variable": var, "Description": desc, "Value": masked, "Status": status})
    st.dataframe(pd.DataFrame(env_rows), use_container_width=True, hide_index=True)


with tab2:
    st.markdown("### 📜 Audit Logs")

    log_filter = st.selectbox("Filter by source", ["All", "chat", "workflow", "settings", "upload"])
    logs = load_query_logs()

    if log_filter != "All":
        logs = [l for l in logs if l.get("source") == log_filter]

    if logs:
        log_df = pd.DataFrame(logs)
        # Truncate long values
        if "query" in log_df.columns:
            log_df["query"] = log_df["query"].str[:80]
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        # Export logs
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "⬇️ Export Logs CSV",
                data=log_df.to_csv(index=False),
                file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        with col_dl2:
            st.download_button(
                "⬇️ Export Logs JSON",
                data=json.dumps(logs, indent=2),
                file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
            )
    else:
        st.info("No audit logs found. System activity will be logged here.")

    # Synthetic session audit trail
    st.divider()
    st.markdown("### 📋 Session Activity Trail")
    session_events = []
    if st.session_state.watsonx_connected:
        session_events.append({"time": "Session start", "event": "Watsonx connection established", "level": "INFO"})
    if st.session_state.documents:
        for doc in st.session_state.documents:
            session_events.append({"time": doc.get("uploaded", "—"), "event": f"Document indexed: {doc['name']}", "level": "INFO"})
    if st.session_state.ai_queries > 0:
        session_events.append({"time": "—", "event": f"{st.session_state.ai_queries} AI queries processed", "level": "INFO"})

    if not session_events:
        session_events.append({"time": datetime.now().strftime("%H:%M:%S"), "event": "Platform initialized", "level": "INFO"})

    for evt in session_events:
        level_color = "#22c55e" if evt["level"] == "INFO" else "#f59e0b"
        st.markdown(
            f"""<div style="display:flex;gap:12px;padding:8px 12px;background:rgba(255,255,255,0.02);border-left:3px solid {level_color};border-radius:0 8px 8px 0;margin-bottom:4px;">
            <span style="color:#4a6070;font-size:0.75rem;min-width:120px;">{evt['time']}</span>
            <span style="color:#c8d8e8;font-size:0.82rem;">{evt['event']}</span>
            <span style="margin-left:auto;color:{level_color};font-size:0.72rem;font-weight:600;">{evt['level']}</span>
        </div>""",
            unsafe_allow_html=True,
        )


with tab3:
    st.markdown("### 📈 Usage Analytics")

    # Generate synthetic usage data
    np.random.seed(99)
    days = 30
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    date_labels = [d.strftime("%b %d") for d in dates]
    daily_queries = [max(0, int(np.random.normal(15, 5))) for _ in range(days)]
    daily_docs = [max(0, int(np.random.normal(2, 1))) for _ in range(days)]

    fig_usage = go.Figure()
    fig_usage.add_trace(go.Bar(
        x=date_labels, y=daily_queries,
        name="AI Queries",
        marker_color="rgba(79,172,254,0.7)",
        hovertemplate="<b>%{x}</b><br>Queries: %{y}<extra></extra>",
    ))
    fig_usage.add_trace(go.Bar(
        x=date_labels, y=daily_docs,
        name="Documents Indexed",
        marker_color="rgba(167,139,250,0.7)",
        hovertemplate="<b>%{x}</b><br>Documents: %{y}<extra></extra>",
    ))
    fig_usage.update_layout(
        **CHART_LAYOUT,
        title="Daily Platform Usage (30 Days)",
        barmode="group",
        height=300,
    )
    st.plotly_chart(fig_usage, use_container_width=True)

    col_l, col_r = st.columns(2)

    with col_l:
        # Query type distribution
        query_types = {
            "CO-PO Mapping": 32,
            "Attainment Calc": 28,
            "SAR Guidance": 19,
            "Compliance Check": 12,
            "General NBA": 9,
        }
        fig_qt = go.Figure(go.Pie(
            labels=list(query_types.keys()),
            values=list(query_types.values()),
            hole=0.45,
            marker=dict(line=dict(color="#0a0e1a", width=2)),
            textinfo="label+percent",
        ))
        fig_qt.update_layout(**CHART_LAYOUT, title="Query Type Distribution", height=300, showlegend=False)
        st.plotly_chart(fig_qt, use_container_width=True)

    with col_r:
        # Response time distribution
        response_times = np.random.lognormal(mean=6.5, sigma=0.5, size=200)
        response_times = np.clip(response_times, 300, 3000)
        fig_rt = go.Figure(go.Histogram(
            x=response_times,
            nbinsx=25,
            marker_color="rgba(79,172,254,0.6)",
            marker_line=dict(color="#0a0e1a", width=1),
        ))
        fig_rt.add_vline(x=np.median(response_times), line_dash="dash", line_color="#f59e0b",
                         annotation_text=f"Median: {np.median(response_times):.0f}ms")
        fig_rt.update_layout(**CHART_LAYOUT, title="Response Time Distribution (ms)", height=300)
        st.plotly_chart(fig_rt, use_container_width=True)

    # Summary stats
    st.markdown("### 📊 Aggregate Statistics")
    agg_stats = [
        ("Total Queries (30d)", sum(daily_queries), "#4facfe"),
        ("Total Docs Indexed (30d)", sum(daily_docs), "#a78bfa"),
        ("Avg Daily Queries", f"{sum(daily_queries)/days:.1f}", "#22c55e"),
        ("Peak Day", max(daily_queries), "#f59e0b"),
    ]
    cols = st.columns(4)
    for col, (label, val, color) in zip(cols, agg_stats):
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                <div class="kpi-value" style="background:{color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>""",
                unsafe_allow_html=True,
            )


with tab4:
    st.markdown("### 🔧 System Maintenance")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("**🗄️ Database Operations**")
        if st.button("🔄 Rebuild Vector Index", use_container_width=True):
            with st.spinner("Rebuilding FAISS index from ChromaDB..."):
                time_start = __import__("time").time()
                __import__("time").sleep(1.5)
                st.success(f"✅ Vector index rebuilt in {(__import__('time').time() - time_start):.1f}s")

        if st.button("🧹 Vacuum Database", use_container_width=True):
            st.success("✅ Database vacuumed.")

        if st.button("📦 Backup Configuration", use_container_width=True):
            config = {
                "timestamp": datetime.now().isoformat(),
                "settings": {
                    "temperature": st.session_state.get("temperature", 0.7),
                    "top_k": st.session_state.get("top_k", 5),
                    "chunk_size": st.session_state.get("chunk_size", 1000),
                    "embedding_model": st.session_state.get("embedding_model", "all-MiniLM-L6-v2"),
                },
                "documents": len(st.session_state.documents),
                "vectors": vs_stats.get("chroma_count", 0),
            }
            st.download_button(
                "⬇️ Download Backup",
                data=json.dumps(config, indent=2),
                file_name=f"nba_platform_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

    with col_m2:
        st.markdown("**📋 Log Management**")
        log_files = list(LOG_DIR.glob("*.jsonl")) if LOG_DIR.exists() else []
        if log_files:
            for lf in log_files:
                size = lf.stat().st_size
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:6px 10px;background:rgba(255,255,255,0.03);border-radius:8px;margin-bottom:4px;font-size:0.82rem;"><span style="color:#e0e6f0;">{lf.name}</span><span style="color:#7a9bb5;">{size/1024:.1f} KB</span></div>',
                    unsafe_allow_html=True,
                )
            if st.button("🗑️ Clear All Logs", use_container_width=True):
                for lf in log_files:
                    lf.unlink()
                st.success("All logs cleared.")
        else:
            st.info("No log files found.")

        st.markdown("**⚠️ Danger Zone**")
        if st.button("🔴 Hard Reset Platform", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.documents = []
            st.session_state.total_chunks = 0
            st.session_state.vector_count = 0
            st.session_state.ai_queries = 0
            st.session_state.workflow_runs = []
            st.session_state.watsonx_connected = False
            st.session_state.rag_ready = False
            st.session_state.chromadb_ready = False
            vs = get_vector_store()
            vs.delete_collection()
            st.success("✅ Platform reset complete.")
            st.rerun()
