import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
from utils.metrics import (
    calculate_co_attainment, calculate_po_attainment,
    generate_copo_matrix, compute_coverage,
    generate_recommendations, NBA_TARGET_ATTAINMENT, NBA_POS,
)
from utils.analytics import co_attainment_bar, po_attainment_bar, readiness_gauge

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">📈</span>
    <h2>Attainment Calculator</h2>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["📝 Input Data", "📊 CO Attainment", "🎓 PO Attainment", "💡 Recommendations"])

# ── Shared state ──────────────────────────────────────────────────────────────
if "att_co_attainment" not in st.session_state:
    np.random.seed(21)
    default_cos = [f"CO{i}" for i in range(1, 7)]
    default_pos = list(NBA_POS.keys())[:8]
    st.session_state.att_direct = {co: round(np.random.uniform(55, 88), 1) for co in default_cos}
    st.session_state.att_indirect = {co: round(np.random.uniform(60, 82), 1) for co in default_cos}
    st.session_state.att_cos = default_cos
    st.session_state.att_pos = default_pos
    st.session_state.att_matrix = generate_copo_matrix(default_cos, default_pos)
    st.session_state.att_co_attainment = calculate_co_attainment(
        st.session_state.att_direct,
        st.session_state.att_indirect,
    )
    st.session_state.att_po_attainment = calculate_po_attainment(
        st.session_state.att_co_attainment,
        st.session_state.att_matrix,
    )

with tab1:
    st.markdown("### ⚙️ Assessment Configuration")

    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        target = st.number_input("Target Attainment (%)", min_value=40, max_value=90, value=60, step=5)
    with col_cfg2:
        direct_weight = st.number_input("Direct Assessment Weight", min_value=0.5, max_value=1.0, value=0.8, step=0.05)
    with col_cfg3:
        indirect_weight = st.number_input("Indirect Assessment Weight", min_value=0.0, max_value=0.5, value=0.2, step=0.05)

    st.caption(f"Note: Direct + Indirect weights should sum to 1.0. Current: {direct_weight + indirect_weight:.2f}")

    st.divider()
    st.markdown("### 📊 Direct Assessment Scores")
    st.caption("Enter percentage of students achieving ≥ target marks in each CO assessment.")

    cos = st.session_state.att_cos
    direct_data = []
    for co in cos:
        direct_data.append({
            "CO": co,
            "Mid-term (%)": round(np.random.uniform(55, 90), 1),
            "End-term (%)": round(np.random.uniform(58, 88), 1),
            "Assignment (%)": round(np.random.uniform(65, 95), 1),
            "Quiz (%)": round(np.random.uniform(60, 92), 1),
        })

    direct_df = st.data_editor(
        pd.DataFrame(direct_data),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="direct_editor",
    )

    st.divider()
    st.markdown("### 📋 Indirect Assessment Scores")
    st.caption("Enter scores from surveys, exit interviews, alumni feedback, etc.")

    indirect_data = []
    for co in cos:
        indirect_data.append({
            "CO": co,
            "Student Survey (%)": round(np.random.uniform(65, 90), 1),
            "Exit Survey (%)": round(np.random.uniform(60, 88), 1),
            "Alumni Survey (%)": round(np.random.uniform(62, 85), 1),
        })

    indirect_df = st.data_editor(
        pd.DataFrame(indirect_data),
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="indirect_editor",
    )

    if st.button("🔢 Calculate Attainment", type="primary", use_container_width=True):
        direct_scores = {}
        indirect_scores = {}
        for _, row in direct_df.iterrows():
            co = row["CO"]
            direct_scores[co] = np.mean([
                row["Mid-term (%)"], row["End-term (%)"],
                row["Assignment (%)"], row["Quiz (%)"]
            ])

        for _, row in indirect_df.iterrows():
            co = row["CO"]
            indirect_scores[co] = np.mean([
                row["Student Survey (%)"], row["Exit Survey (%)"], row["Alumni Survey (%)"]
            ])

        st.session_state.att_direct = direct_scores
        st.session_state.att_indirect = indirect_scores
        st.session_state.att_co_attainment = calculate_co_attainment(
            direct_scores, indirect_scores,
            direct_weight=direct_weight, indirect_weight=indirect_weight, target=target,
        )
        st.session_state.att_po_attainment = calculate_po_attainment(
            st.session_state.att_co_attainment,
            st.session_state.att_matrix,
        )
        st.success("✅ Attainment calculated successfully! View results in other tabs.")


with tab2:
    co_data = st.session_state.att_co_attainment

    st.markdown("### 📊 CO Attainment Results")

    # KPIs
    attained = sum(1 for v in co_data.values() if v["attainment"] >= NBA_TARGET_ATTAINMENT)
    avg_att = np.mean([v["attainment"] for v in co_data.values()])
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{attained}/{len(co_data)}</div><div class="kpi-label">COs Attained</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{avg_att:.1f}%</div><div class="kpi-label">Average Attainment</div></div>""", unsafe_allow_html=True)
    with c3:
        not_attained = len(co_data) - attained
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="background:#ef4444;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{not_attained}</div><div class="kpi-label">COs Below Target</div></div>""", unsafe_allow_html=True)

    st.plotly_chart(co_attainment_bar(co_data), use_container_width=True)

    # Detail table
    rows = []
    for co, data in co_data.items():
        rows.append({
            "CO": co,
            "Direct (%)": f"{data['direct']:.1f}",
            "Indirect (%)": f"{data['indirect']:.1f}",
            "Attainment (%)": f"{data['attainment']:.1f}",
            "Target (%)": f"{data['target']:.1f}",
            "Gap": f"{data['gap']:.1f}",
            "Status": "✅ Attained" if data["attainment"] >= NBA_TARGET_ATTAINMENT else "❌ Not Attained",
            "Level": data["level"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Export
    csv = pd.DataFrame(rows).to_csv(index=False)
    st.download_button("⬇️ Export CO Attainment CSV", csv, "co_attainment.csv", "text/csv")


with tab3:
    po_data = st.session_state.att_po_attainment

    st.markdown("### 🎓 PO Attainment Results")

    # KPIs
    po_attained = sum(1 for v in po_data.values() if v["attainment"] >= NBA_TARGET_ATTAINMENT)
    avg_po = np.mean([v["attainment"] for v in po_data.values()])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{po_attained}/{len(po_data)}</div><div class="kpi-label">POs Attained</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{avg_po:.1f}%</div><div class="kpi-label">Average PO Score</div></div>""", unsafe_allow_html=True)
    with c3:
        readiness = avg_po
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{readiness:.1f}%</div><div class="kpi-label">OBE Readiness</div></div>""", unsafe_allow_html=True)

    st.plotly_chart(po_attainment_bar(po_data), use_container_width=True)

    po_rows = []
    for po, data in po_data.items():
        po_rows.append({
            "PO": po,
            "Description": NBA_POS.get(po, ""),
            "Attainment (%)": f"{data['attainment']:.1f}",
            "Status": "✅ Attained" if data["attainment"] >= NBA_TARGET_ATTAINMENT else "⚠️ Below Target",
        })
    st.dataframe(pd.DataFrame(po_rows), use_container_width=True, hide_index=True)

    csv = pd.DataFrame(po_rows).to_csv(index=False)
    st.download_button("⬇️ Export PO Attainment CSV", csv, "po_attainment.csv", "text/csv")


with tab4:
    st.markdown("### 💡 Improvement Recommendations")
    coverage = compute_coverage(st.session_state.att_matrix)
    recs = generate_recommendations(
        st.session_state.att_co_attainment,
        st.session_state.att_po_attainment,
        coverage,
    )

    for rec in recs:
        st.markdown(
            f"""<div class="glass-card" style="margin-bottom:0.75rem;padding:1rem 1.25rem;">
            <div style="color:#c8d8e8;line-height:1.6;font-size:0.9rem;">{rec}</div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 🔄 Continuous Quality Improvement (CQI)")
    st.markdown(
        """
    <div class="glass-card">
        <div style="font-weight:600;color:#e8f0fe;margin-bottom:0.75rem;">NBA CQI Process (3-Year Cycle)</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:rgba(79,172,254,0.08);border:1px solid rgba(79,172,254,0.2);border-radius:10px;padding:12px;">
                <div style="font-weight:600;color:#4facfe;font-size:0.85rem;margin-bottom:6px;">Year 1 — Baseline</div>
                <ul style="color:#a0b4c8;font-size:0.8rem;margin:0;padding-left:16px;line-height:1.8;">
                    <li>Define COs/POs</li>
                    <li>Establish assessment tools</li>
                    <li>Collect baseline data</li>
                </ul>
            </div>
            <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);border-radius:10px;padding:12px;">
                <div style="font-weight:600;color:#a78bfa;font-size:0.85rem;margin-bottom:6px;">Year 2 — Analysis</div>
                <ul style="color:#a0b4c8;font-size:0.8rem;margin:0;padding-left:16px;line-height:1.8;">
                    <li>Compute attainments</li>
                    <li>Identify gaps</li>
                    <li>Propose improvements</li>
                </ul>
            </div>
            <div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:12px;">
                <div style="font-weight:600;color:#22c55e;font-size:0.85rem;margin-bottom:6px;">Year 3 — Implementation</div>
                <ul style="color:#a0b4c8;font-size:0.8rem;margin:0;padding-left:16px;line-height:1.8;">
                    <li>Execute action plans</li>
                    <li>Re-assess outcomes</li>
                    <li>Document evidence</li>
                </ul>
            </div>
            <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:12px;">
                <div style="font-weight:600;color:#f59e0b;font-size:0.85rem;margin-bottom:6px;">Repeat — Sustain</div>
                <ul style="color:#a0b4c8;font-size:0.8rem;margin:0;padding-left:16px;line-height:1.8;">
                    <li>Integrate feedback</li>
                    <li>Update curriculum</li>
                    <li>Prepare SAR</li>
                </ul>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
