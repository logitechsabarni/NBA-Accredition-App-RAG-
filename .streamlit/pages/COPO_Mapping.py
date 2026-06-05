import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
from utils.metrics import generate_copo_matrix, compute_coverage, NBA_POS
from utils.analytics import copo_heatmap, CHART_LAYOUT
import plotly.graph_objects as go

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">🗺️</span>
    <h2>CO-PO Mapping</h2>
</div>
""",
    unsafe_allow_html=True,
)

# ── Initialize session data ───────────────────────────────────────────────────
if "copo_matrix" not in st.session_state:
    default_cos = [f"CO{i}" for i in range(1, 7)]
    default_pos = list(NBA_POS.keys())[:8]
    st.session_state.copo_matrix = generate_copo_matrix(default_cos, default_pos)
    st.session_state.cos_list = default_cos
    st.session_state.pos_list = default_pos

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📐 Matrix Editor", "🔥 Heatmap", "📊 Analytics", "📤 Export"])

with tab1:
    st.markdown("### Configure COs & POs")

    col_co, col_po = st.columns(2)
    with col_co:
        st.markdown("**Course Outcomes (COs)**")
        cos_input = st.text_area(
            "Enter CO IDs (one per line)",
            value="\n".join(st.session_state.cos_list),
            height=160,
            label_visibility="collapsed",
        )

    with col_po:
        st.markdown("**Program Outcomes (POs)**")
        pos_input = st.text_area(
            "Enter PO IDs (one per line)",
            value="\n".join(st.session_state.pos_list),
            height=160,
            label_visibility="collapsed",
        )

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🔄 Auto-Generate Mapping", use_container_width=True):
            new_cos = [c.strip() for c in cos_input.split("\n") if c.strip()]
            new_pos = [p.strip() for p in pos_input.split("\n") if p.strip()]
            st.session_state.cos_list = new_cos
            st.session_state.pos_list = new_pos
            st.session_state.copo_matrix = generate_copo_matrix(new_cos, new_pos)
            st.success(f"✅ Matrix generated: {len(new_cos)} COs × {len(new_pos)} POs")
            st.rerun()

    with col_btn2:
        if st.button("🗑️ Clear Matrix", use_container_width=True):
            new_cos = [c.strip() for c in cos_input.split("\n") if c.strip()]
            new_pos = [p.strip() for p in pos_input.split("\n") if p.strip()]
            st.session_state.copo_matrix = generate_copo_matrix(new_cos, new_pos, manual_values={})
            st.rerun()

    st.divider()

    # ── Editable matrix ───────────────────────────────────────────────────────
    st.markdown("### ✏️ Edit Mapping Matrix (0=None, 1=Low, 2=Medium, 3=High)")
    st.caption("Edit values directly in the table below. Valid values: 0, 1, 2, 3")

    matrix = st.session_state.copo_matrix.copy()
    edited_df = st.data_editor(
        matrix,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            col: st.column_config.SelectboxColumn(
                col,
                options=[0, 1, 2, 3],
                default=0,
            )
            for col in matrix.columns
        },
        key="matrix_editor",
    )

    if st.button("💾 Save Changes", use_container_width=True):
        st.session_state.copo_matrix = edited_df.clip(0, 3).astype(int)
        st.success("✅ Matrix saved successfully!")

    st.divider()

    # NBA PO reference
    st.markdown("### 📚 NBA Program Outcomes Reference")
    po_ref = [{"PO": k, "Description": v} for k, v in NBA_POS.items()]
    st.dataframe(pd.DataFrame(po_ref), use_container_width=True, hide_index=True)


with tab2:
    st.markdown("### 🔥 CO-PO Mapping Heatmap")
    matrix = st.session_state.copo_matrix

    fig = copo_heatmap(matrix)
    st.plotly_chart(fig, use_container_width=True)

    # Legend
    st.markdown(
        """
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:0.5rem;">
        <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#a0b4c8;">
            <div style="width:16px;height:16px;background:rgba(255,255,255,0.04);border:1px solid rgba(99,179,237,0.2);border-radius:4px;"></div>0 — No Correlation
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#a0b4c8;">
            <div style="width:16px;height:16px;background:rgba(79,172,254,0.25);border-radius:4px;"></div>1 — Low
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#a0b4c8;">
            <div style="width:16px;height:16px;background:rgba(79,172,254,0.55);border-radius:4px;"></div>2 — Medium
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#a0b4c8;">
            <div style="width:16px;height:16px;background:rgba(79,172,254,0.9);border-radius:4px;"></div>3 — High
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


with tab3:
    matrix = st.session_state.copo_matrix
    coverage = compute_coverage(matrix)

    st.markdown("### 📊 Mapping Coverage Analytics")

    # Summary KPIs
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("Coverage", f"{coverage['coverage_pct']}%", "#4facfe"),
        ("Strong (3)", str(coverage["strong_mappings"]), "#22c55e"),
        ("Medium (2)", str(coverage["medium_mappings"]), "#f59e0b"),
        ("Weak (1)", str(coverage["weak_mappings"]), "#f97316"),
    ]
    for col, (label, val, color) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                <div class="kpi-value" style="background:{color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**CO Coverage (%)**")
        co_cov_df = pd.DataFrame(
            list(coverage["co_coverage"].items()), columns=["CO", "Coverage (%)"]
        )
        fig_co = go.Figure(go.Bar(
            x=co_cov_df["CO"],
            y=co_cov_df["Coverage (%)"],
            marker_color=[
                "#22c55e" if v >= 70 else "#f59e0b" if v >= 50 else "#ef4444"
                for v in co_cov_df["Coverage (%)"]
            ],
            text=[f"{v}%" for v in co_cov_df["Coverage (%)"]],
            textposition="outside",
            textfont=dict(color="#e0e6f0"),
        ))
        fig_co.update_layout(**CHART_LAYOUT, height=260, yaxis_range=[0, 115], showlegend=False)
        st.plotly_chart(fig_co, use_container_width=True)

    with col_right:
        st.markdown("**PO Coverage (%)**")
        po_cov_df = pd.DataFrame(
            list(coverage["po_coverage"].items()), columns=["PO", "Coverage (%)"]
        )
        fig_po = go.Figure(go.Bar(
            x=po_cov_df["PO"],
            y=po_cov_df["Coverage (%)"],
            marker_color=[
                "#4facfe" if v >= 70 else "#a78bfa" if v >= 50 else "#f97316"
                for v in po_cov_df["Coverage (%)"]
            ],
            text=[f"{v}%" for v in po_cov_df["Coverage (%)"]],
            textposition="outside",
            textfont=dict(color="#e0e6f0"),
        ))
        fig_po.update_layout(**CHART_LAYOUT, height=260, yaxis_range=[0, 115], showlegend=False)
        st.plotly_chart(fig_po, use_container_width=True)

    # Gap analysis
    st.markdown("### 🕳️ Gap Analysis")
    gaps = [
        f"{co} → {po}"
        for co in matrix.index
        for po in matrix.columns
        if matrix.loc[co, po] == 0
    ]
    if gaps:
        st.warning(f"⚠️ {len(gaps)} unmapped CO-PO combinations found.")
        gap_cols = st.columns(4)
        for i, gap in enumerate(gaps[:12]):
            with gap_cols[i % 4]:
                st.markdown(
                    f'<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);border-radius:8px;padding:6px 10px;font-size:0.8rem;color:#fc8181;margin-bottom:4px;">{gap}</div>',
                    unsafe_allow_html=True,
                )
        if len(gaps) > 12:
            st.caption(f"... and {len(gaps) - 12} more gaps.")
    else:
        st.success("✅ Full coverage! All COs are mapped to at least one PO.")


with tab4:
    st.markdown("### 📤 Export CO-PO Matrix")
    matrix = st.session_state.copo_matrix

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        csv_data = matrix.to_csv()
        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name="copo_mapping_matrix.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_exp2:
        # JSON export
        json_data = matrix.to_json()
        st.download_button(
            "⬇️ Download JSON",
            data=json_data,
            file_name="copo_mapping_matrix.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("**Preview:**")
    st.dataframe(matrix, use_container_width=True)
