import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.metrics import (
    calculate_co_attainment, calculate_po_attainment,
    generate_copo_matrix, compute_coverage,
    calculate_readiness_score, NBA_POS,
)
from utils.analytics import (
    co_attainment_bar, po_attainment_bar, department_comparison,
    readiness_trend, readiness_gauge, sar_progress_donut, CHART_LAYOUT, COLORS,
)
from utils.helpers import department_benchmarks, generate_sar_sections, load_query_logs

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">📉</span>
    <h2>Analytics & Insights</h2>
</div>
""",
    unsafe_allow_html=True,
)

# ── Seed data ─────────────────────────────────────────────────────────────────
np.random.seed(7)
cos = [f"CO{i}" for i in range(1, 7)]
pos = list(NBA_POS.keys())[:8]
co_direct = {co: np.random.uniform(55, 90) for co in cos}
co_indirect = {co: np.random.uniform(58, 85) for co in cos}
co_attainment = calculate_co_attainment(co_direct, co_indirect)
matrix = generate_copo_matrix(cos, pos)
po_attainment = calculate_po_attainment(co_attainment, matrix)
coverage = compute_coverage(matrix)
readiness = calculate_readiness_score(co_attainment, po_attainment, 68.0, 72.0)
benchmarks = department_benchmarks()
sections = generate_sar_sections()
sar_completion = {s["id"]: np.random.randint(40, 100) for s in sections}

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔧 Filters & Configuration", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        dept_filter = st.multiselect("Departments", list(benchmarks.keys()), default=list(benchmarks.keys())[:4])
    with col2:
        target_filter = st.slider("Target Attainment (%)", 50, 80, 60)
    with col3:
        year_filter = st.selectbox("Academic Year", ["2024-25", "2023-24", "2022-23", "2021-22"])

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Readiness", "📊 CO Analysis", "🎓 PO Analysis", "🏢 Departments", "📋 SAR Progress"
])

with tab1:
    st.markdown("### 🎯 Accreditation Readiness Overview")

    c1, c2, c3, c4 = st.columns(4)
    comps = [
        ("CO Score", f"{readiness['co_score']}%", "#4facfe"),
        ("PO Score", f"{readiness['po_score']}%", "#a78bfa"),
        ("SAR Progress", f"{readiness['sar_score']}%", "#22c55e"),
        ("Docs Score", f"{readiness['doc_score']}%", "#f59e0b"),
    ]
    for col, (label, val, color) in zip([c1, c2, c3, c4], comps):
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                <div class="kpi-value" style="background:{color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    col_g, col_t = st.columns([1, 2])
    with col_g:
        st.plotly_chart(readiness_gauge(readiness["score"]), use_container_width=True)
    with col_t:
        st.plotly_chart(readiness_trend(18), use_container_width=True)

    # Readiness component breakdown
    st.markdown("### 📐 Readiness Component Breakdown")
    categories = ["CO Attainment", "PO Attainment", "SAR Completion", "Documentation"]
    scores = [readiness["co_score"], readiness["po_score"], readiness["sar_score"], readiness["doc_score"]]
    weights = [30, 30, 25, 15]

    fig_radar = go.Figure(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(79,172,254,0.12)",
        line=dict(color="#4facfe", width=2),
        marker=dict(color="#4facfe", size=8),
        name="Current Score",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[60] * 5,
        theta=categories + [categories[0]],
        line=dict(color="#f59e0b", width=1.5, dash="dash"),
        name="Target (60%)",
        marker=dict(color="#f59e0b"),
    ))
    fig_radar.update_layout(
        **CHART_LAYOUT,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#7a9bb5"),
            angularaxis=dict(color="#7a9bb5"),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=380,
        title="Readiness Radar Chart",
    )
    st.plotly_chart(fig_radar, use_container_width=True)


with tab2:
    st.markdown("### 📊 CO Attainment Deep Dive")
    st.plotly_chart(co_attainment_bar(co_attainment, target_filter), use_container_width=True)

    col_box, col_scatter = st.columns(2)

    with col_box:
        att_vals = [v["attainment"] for v in co_attainment.values()]
        fig_box = go.Figure(go.Box(
            y=att_vals,
            name="CO Attainment",
            marker_color=COLORS["primary"],
            boxmean=True,
            hoverinfo="y",
        ))
        fig_box.add_hline(y=target_filter, line_dash="dash", line_color="#f59e0b")
        fig_box.update_layout(**CHART_LAYOUT, title="Attainment Distribution", height=300)
        st.plotly_chart(fig_box, use_container_width=True)

    with col_scatter:
        direct_vals = [v["direct"] for v in co_attainment.values()]
        indirect_vals = [v["indirect"] for v in co_attainment.values()]
        fig_sc = go.Figure(go.Scatter(
            x=direct_vals,
            y=indirect_vals,
            mode="markers+text",
            text=list(co_attainment.keys()),
            textposition="top center",
            marker=dict(color=COLORS["accent"], size=12, line=dict(color="#0a0e1a", width=2)),
            hovertemplate="<b>%{text}</b><br>Direct: %{x}%<br>Indirect: %{y}%<extra></extra>",
        ))
        fig_sc.update_layout(
            **CHART_LAYOUT,
            title="Direct vs Indirect Assessment",
            xaxis_title="Direct (%)", yaxis_title="Indirect (%)",
            height=300,
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    # CO trend simulation (multi-year)
    years = ["2021-22", "2022-23", "2023-24", "2024-25"]
    fig_trend = go.Figure()
    for co in cos:
        base = np.random.uniform(52, 70)
        vals = [min(base + np.random.uniform(0, 6) * i, 95) for i in range(len(years))]
        fig_trend.add_trace(go.Scatter(
            x=years, y=[round(v, 1) for v in vals],
            mode="lines+markers", name=co,
            hovertemplate=f"<b>{co}</b><br>Year: %{{x}}<br>Attainment: %{{y}}%<extra></extra>",
        ))
    fig_trend.add_hline(y=target_filter, line_dash="dash", line_color="#f59e0b",
                        annotation_text="Target", annotation_font_color="#f59e0b")
    fig_trend.update_layout(**CHART_LAYOUT, title="CO Attainment Trend (Multi-Year)", height=340)
    st.plotly_chart(fig_trend, use_container_width=True)


with tab3:
    st.markdown("### 🎓 PO Attainment Analysis")
    st.plotly_chart(po_attainment_bar(po_attainment, target_filter), use_container_width=True)

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        po_vals = [v["attainment"] for v in po_attainment.values()]
        po_labels = list(po_attainment.keys())
        colors_po = [COLORS["success"] if v >= target_filter else COLORS["warning"] for v in po_vals]

        fig_pie = go.Figure(go.Pie(
            labels=po_labels,
            values=[max(v, 1) for v in po_vals],
            marker=dict(colors=px.colors.sequential.Blues[2:], line=dict(color="#0a0e1a", width=1)),
            hole=0.45,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Attainment: %{value:.1f}%<extra></extra>",
        ))
        fig_pie.update_layout(**CHART_LAYOUT, title="PO Distribution", height=320, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_p2:
        # PO heatmap across years
        years = ["2021-22", "2022-23", "2023-24", "2024-25"]
        po_trend_data = {}
        for po in pos:
            base = np.random.uniform(50, 72)
            po_trend_data[po] = [round(min(base + i * np.random.uniform(1, 4), 95), 1) for i in range(len(years))]

        po_trend_df = pd.DataFrame(po_trend_data, index=years)
        fig_ph = go.Figure(go.Heatmap(
            z=po_trend_df.values,
            x=po_trend_df.columns.tolist(),
            y=po_trend_df.index.tolist(),
            colorscale=[[0, "#1a1a2e"], [0.5, "#4facfe55"], [1, "#4facfe"]],
            text=po_trend_df.values,
            texttemplate="%{text}",
            textfont=dict(color="white", size=11),
            hovertemplate="<b>%{x}</b><br>Year: %{y}<br>Attainment: %{z}%<extra></extra>",
        ))
        fig_ph.update_layout(**CHART_LAYOUT, title="PO Attainment Heatmap (Multi-Year)", height=320)
        st.plotly_chart(fig_ph, use_container_width=True)

    # PO summary table
    po_summary = []
    for po, data in po_attainment.items():
        po_summary.append({
            "PO": po,
            "Description": NBA_POS.get(po, "")[:45] + "...",
            "Attainment (%)": f"{data['attainment']:.1f}",
            "Status": "✅ Attained" if data["attainment"] >= target_filter else "⚠️ Below Target",
        })
    st.dataframe(pd.DataFrame(po_summary), use_container_width=True, hide_index=True)


with tab4:
    st.markdown("### 🏢 Department Benchmark Analysis")
    filtered_benchmarks = {k: v for k, v in benchmarks.items() if k in dept_filter} if dept_filter else benchmarks

    st.plotly_chart(department_comparison(filtered_benchmarks), use_container_width=True)

    # Department comparison table
    dept_rows = []
    for dept, score in filtered_benchmarks.items():
        attained_cos = round(score / 100 * 6)
        attained_pos = round(score / 100 * 8)
        dept_rows.append({
            "Department": dept,
            "Readiness (%)": f"{score}",
            "COs Attained": f"{attained_cos}/6",
            "POs Attained": f"{attained_pos}/8",
            "Status": "✅ Ready" if score >= 60 else "⚠️ In Progress",
            "Trend": "📈 Improving" if score > 65 else "📊 Stable",
        })
    st.dataframe(pd.DataFrame(dept_rows), use_container_width=True, hide_index=True)

    # Bubble chart
    names = list(filtered_benchmarks.keys())
    x = [filtered_benchmarks[n] for n in names]
    y = [np.random.uniform(55, 90) for _ in names]
    sizes = [np.random.randint(200, 800) for _ in names]

    fig_bubble = go.Figure(go.Scatter(
        x=x, y=y, mode="markers+text",
        text=names,
        textposition="top center",
        textfont=dict(color="#e0e6f0", size=10),
        marker=dict(
            size=[s / 40 for s in sizes],
            color=x,
            colorscale="Blues",
            showscale=True,
            colorbar=dict(title="Readiness", tickfont=dict(color="#a0b4c8")),
            line=dict(color="#0a0e1a", width=1),
        ),
        hovertemplate="<b>%{text}</b><br>Readiness: %{x}%<br>CO Avg: %{y:.1f}%<extra></extra>",
    ))
    fig_bubble.update_layout(
        **CHART_LAYOUT,
        title="Department Readiness vs CO Performance",
        xaxis_title="Readiness Score (%)",
        yaxis_title="Average CO Attainment (%)",
        height=360,
    )
    st.plotly_chart(fig_bubble, use_container_width=True)


with tab5:
    st.markdown("### 📋 SAR Completion & Progress")
    st.plotly_chart(sar_progress_donut(sections, sar_completion), use_container_width=True)

    # Section breakdown
    for section in sections:
        pct = sar_completion.get(section["id"], 0)
        color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(99,179,237,0.08);border-radius:10px;margin-bottom:6px;">
            <div style="min-width:80px;font-weight:600;color:#e0e6f0;font-size:0.85rem;">Section {section['id']}</div>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#a0b4c8;font-size:0.82rem;">{section['title']}</span>
                    <span style="color:{color};font-size:0.82rem;font-weight:700;">{pct}%</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:999px;height:5px;overflow:hidden;">
                    <div style="background:{color};width:{pct}%;height:100%;border-radius:999px;"></div>
                </div>
            </div>
            <div style="min-width:50px;text-align:right;font-size:0.75rem;color:#7a9bb5;">wt: {section['weight']}%</div>
        </div>""",
            unsafe_allow_html=True,
        )

    # Usage analytics from logs
    st.divider()
    st.markdown("### 💬 AI Query Analytics")
    logs = load_query_logs()
    if logs:
        df_logs = pd.DataFrame(logs)
        st.markdown(f"**Total queries logged: {len(df_logs)}**")
        st.dataframe(df_logs.tail(20)[["timestamp", "query", "response_length", "source"]], use_container_width=True, hide_index=True)
    else:
        st.info("No query logs yet. Interact with the AI assistant to generate analytics.")
