import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import json
from datetime import datetime
from utils.helpers import generate_sar_sections
from utils.watsonx_client import get_watsonx_client
from utils.analytics import sar_progress_donut

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">📄</span>
    <h2>SAR Builder</h2>
    <span style="margin-left:8px;font-size:0.8rem;color:#7a9bb5;">Self Assessment Report Generator</span>
</div>
""",
    unsafe_allow_html=True,
)

# ── Initialize SAR state ───────────────────────────────────────────────────────
SECTIONS = generate_sar_sections()

if "sar_data" not in st.session_state:
    st.session_state.sar_data = {s["id"]: "" for s in SECTIONS}
if "sar_completion" not in st.session_state:
    st.session_state.sar_completion = {s["id"]: 0 for s in SECTIONS}
if "sar_institute" not in st.session_state:
    st.session_state.sar_institute = {
        "name": "",
        "department": "",
        "program": "",
        "academic_year": f"{datetime.now().year-1}-{datetime.now().year}",
        "accreditation_cycle": "NBA Tier-I",
    }


def compute_overall_completion() -> float:
    total = sum(s["weight"] for s in SECTIONS)
    scored = sum(
        s["weight"] * (st.session_state.sar_completion.get(s["id"], 0) / 100)
        for s in SECTIONS
    )
    return (scored / total * 100) if total > 0 else 0.0


tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Institute Details", "✍️ Content Editor", "📊 Progress", "📤 Export"])

with tab1:
    st.markdown("### 🏛️ Institute & Program Details")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sar_institute["name"] = st.text_input(
            "Institute Name", value=st.session_state.sar_institute["name"],
            placeholder="e.g., ABC Engineering College"
        )
        st.session_state.sar_institute["department"] = st.text_input(
            "Department", value=st.session_state.sar_institute["department"],
            placeholder="e.g., Computer Science & Engineering"
        )
        st.session_state.sar_institute["program"] = st.text_input(
            "Program Name", value=st.session_state.sar_institute["program"],
            placeholder="e.g., B.Tech in CSE"
        )

    with col2:
        st.session_state.sar_institute["academic_year"] = st.text_input(
            "Academic Year", value=st.session_state.sar_institute["academic_year"]
        )
        st.session_state.sar_institute["accreditation_cycle"] = st.selectbox(
            "Accreditation Type",
            ["NBA Tier-I", "NBA Tier-II", "NBA Re-accreditation"],
            index=0,
        )

        naac_grade = st.selectbox("NAAC Grade (if applicable)", ["Not Accredited", "A++", "A+", "A", "B++", "B+", "B", "C"])

    st.divider()
    st.markdown("### 🎯 Vision, Mission & PEOs")

    vision = st.text_area(
        "Department Vision",
        placeholder="e.g., To be a globally recognized department producing competent engineers...",
        height=100,
    )

    mission = st.text_area(
        "Department Mission",
        placeholder="M1: To provide quality education...\nM2: To foster research...\nM3: To develop industry-ready graduates...",
        height=120,
    )

    peos = st.text_area(
        "Program Educational Objectives (PEOs)",
        placeholder="PEO1: Graduates will demonstrate technical proficiency...\nPEO2: Graduates will pursue professional development...",
        height=120,
    )

    if st.button("💾 Save Institute Details", use_container_width=True):
        st.session_state.sar_data["1"] = f"Vision:\n{vision}\n\nMission:\n{mission}\n\nPEOs:\n{peos}"
        st.session_state.sar_completion["1"] = 80 if (vision and mission and peos) else 40
        st.success("✅ Institute details saved!")


with tab2:
    st.markdown("### ✍️ SAR Section Editor")

    section_names = {s["id"]: f"Section {s['id']}: {s['title']}" for s in SECTIONS}
    selected_section_id = st.selectbox(
        "Select Section to Edit",
        options=[s["id"] for s in SECTIONS],
        format_func=lambda x: section_names[x],
    )

    selected_section = next(s for s in SECTIONS if s["id"] == selected_section_id)

    st.markdown(
        f"""<div class="glass-card" style="margin-bottom:1rem;">
        <div style="font-weight:700;color:#e8f0fe;font-size:1rem;">{selected_section['title']}</div>
        <div style="color:#7a9bb5;font-size:0.82rem;margin-top:4px;">Weight: {selected_section['weight']}% | Subsections: {', '.join(selected_section['subsections'])}</div>
    </div>""",
        unsafe_allow_html=True,
    )

    col_edit, col_ai = st.columns([3, 1])

    with col_edit:
        content = st.text_area(
            "Section Content",
            value=st.session_state.sar_data.get(selected_section_id, ""),
            height=300,
            placeholder=f"Write content for {selected_section['title']}...",
            key=f"sar_content_{selected_section_id}",
        )

    with col_ai:
        st.markdown("**🤖 AI Assist**")
        if st.button("✨ Generate Draft", use_container_width=True, key="ai_draft"):
            if st.session_state.watsonx_connected:
                with st.spinner("Generating with Watsonx..."):
                    try:
                        wc = get_watsonx_client()
                        prompt = f"""Write a professional NBA SAR section for "{selected_section['title']}" for an engineering college.
Subsections to cover: {', '.join(selected_section['subsections'])}.
Institute: {st.session_state.sar_institute.get('name', 'Engineering College')}
Department: {st.session_state.sar_institute.get('department', 'Engineering')}
Write 3-4 paragraphs with specific NBA-compliant content."""
                        draft = wc.generate_response(prompt, max_tokens=600)
                        st.session_state.sar_data[selected_section_id] = draft
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI generation failed: {e}")
            else:
                st.warning("Configure Watsonx credentials in Settings first.")

        if st.button("🔍 Compliance Check", use_container_width=True, key="compliance"):
            text = st.session_state.sar_data.get(selected_section_id, "")
            if text:
                word_count = len(text.split())
                if word_count > 100:
                    st.success(f"✅ {word_count} words — Adequate length")
                else:
                    st.warning(f"⚠️ {word_count} words — Consider expanding")
            else:
                st.info("No content yet.")

        completion_pct = st.slider(
            "Completion %",
            0, 100,
            st.session_state.sar_completion.get(selected_section_id, 0),
            key=f"completion_{selected_section_id}",
        )

    if st.button("💾 Save Section", use_container_width=True, type="primary"):
        st.session_state.sar_data[selected_section_id] = content
        st.session_state.sar_completion[selected_section_id] = completion_pct
        st.success(f"✅ Section '{selected_section['title']}' saved!")


with tab3:
    overall = compute_overall_completion()
    st.markdown("### 📊 SAR Completion Progress")

    col_gauge, col_info = st.columns([1, 2])

    with col_gauge:
        from utils.analytics import readiness_gauge
        st.plotly_chart(readiness_gauge(overall, "SAR Completion"), use_container_width=True)

    with col_info:
        st.markdown("**Section Progress**")
        for section in SECTIONS:
            pct = st.session_state.sar_completion.get(section["id"], 0)
            color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 40 else "#ef4444"
            st.markdown(
                f"""<div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="font-size:0.82rem;color:#e0e6f0;">{section['title']}</span>
                    <span style="font-size:0.8rem;color:{color};font-weight:600;">{pct}%</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:999px;height:6px;overflow:hidden;">
                    <div style="background:{color};width:{pct}%;height:100%;border-radius:999px;transition:width 0.5s;"></div>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.plotly_chart(sar_progress_donut(SECTIONS, st.session_state.sar_completion), use_container_width=True)


with tab4:
    st.markdown("### 📤 Export SAR Document")

    overall = compute_overall_completion()
    institute = st.session_state.sar_institute

    if overall < 30:
        st.warning("⚠️ SAR is less than 30% complete. Consider filling more sections before export.")

    col_txt, col_json = st.columns(2)

    with col_txt:
        # Compile full SAR text
        sar_text_parts = [
            f"SELF ASSESSMENT REPORT (SAR)",
            f"{'=' * 60}",
            f"Institute: {institute.get('name', 'N/A')}",
            f"Department: {institute.get('department', 'N/A')}",
            f"Program: {institute.get('program', 'N/A')}",
            f"Academic Year: {institute.get('academic_year', 'N/A')}",
            f"Accreditation Type: {institute.get('accreditation_cycle', 'N/A')}",
            f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            f"Overall Completion: {overall:.1f}%",
            f"{'=' * 60}\n",
        ]

        for section in SECTIONS:
            content = st.session_state.sar_data.get(section["id"], "")
            sar_text_parts.append(f"\nSECTION {section['id']}: {section['title'].upper()}")
            sar_text_parts.append("-" * 50)
            sar_text_parts.append(content if content else "[Section not yet completed]")
            sar_text_parts.append("")

        sar_text = "\n".join(sar_text_parts)

        st.download_button(
            "⬇️ Download SAR (TXT)",
            data=sar_text,
            file_name=f"SAR_{institute.get('department','Dept').replace(' ', '_')}_{datetime.now().year}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_json:
        sar_json = json.dumps({
            "institute": institute,
            "sections": {s["id"]: {"title": s["title"], "content": st.session_state.sar_data.get(s["id"], ""), "completion": st.session_state.sar_completion.get(s["id"], 0)} for s in SECTIONS},
            "overall_completion": round(overall, 1),
            "generated_at": datetime.now().isoformat(),
        }, indent=2)

        st.download_button(
            "⬇️ Download SAR (JSON)",
            data=sar_json,
            file_name=f"SAR_{datetime.now().year}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.info("💡 For PDF/DOCX export, integrate python-docx or reportlab library with the SAR text above.")

    # Preview
    with st.expander("👁️ Preview SAR Document"):
        st.code(sar_text[:3000] + ("\n...[truncated]" if len(sar_text) > 3000 else ""), language=None)
