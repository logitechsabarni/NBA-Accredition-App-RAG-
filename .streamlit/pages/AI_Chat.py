"""
pages/AI_Chat.py
NBA Enterprise AI Platform – AI Assistant Chat.
ChatGPT-style interface with streaming, citations, model selector,
temperature/token controls, and Watsonx status.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Generator, List, Optional

import streamlit as st

from components.navbar import render_navbar, render_page_hero
from components.chat_components import (
    init_chat_session,
    clear_chat_history,
    add_message,
    render_chat_history,
    render_streaming_indicator,
    render_model_selector,
    render_generation_controls,
    render_watsonx_status_panel,
    render_suggested_prompts,
)
from components.workflow_visualizer import (
    get_nba_workflow,
    render_workflow_pipeline,
    simulate_workflow_step,
    NodeStatus as VizNodeStatus,
)
from services.auth_service import auth_service
from services.workflow_service import workflow_service, WorkflowStatus


# ─────────────────────────────────────────────────────────────
# Simulated streaming response generator
# ─────────────────────────────────────────────────────────────

_SAMPLE_RESPONSES: Dict[str, str] = {
    "default": (
        "Based on the NBA Tier-I accreditation guidelines, I'll address your query using "
        "the platform's knowledge base and AI analysis.\n\n"
        "The outcome-based education (OBE) framework requires systematic mapping between "
        "Course Outcomes (COs) and Program Outcomes (POs). The attainment computation "
        "integrates both direct assessment (internal tests, end-semester exams, lab evaluations) "
        "and indirect assessment (exit surveys, alumni feedback).\n\n"
        "**Key recommendations:**\n"
        "1. Ensure all COs map to at least 2 POs with correlation level ≥ 2\n"
        "2. Maintain attainment records for 3 consecutive years\n"
        "3. Review and update PEOs annually with stakeholder input\n\n"
        "Would you like me to generate a specific report or run a detailed analysis?"
    ),
    "copo": (
        "Generating CO-PO Mapping analysis…\n\n"
        "A CO-PO correlation matrix maps each Course Outcome to relevant Program Outcomes "
        "using levels 1 (Low), 2 (Medium), and 3 (High) correlation.\n\n"
        "For a typical CSE program:\n"
        "- CO1 (Apply data structures) → PO1:3, PO2:2, PO5:1\n"
        "- CO2 (Design algorithms) → PO1:3, PO2:3, PO3:2\n"
        "- CO3 (Analyse complexity) → PO1:2, PO2:3, PO4:1\n\n"
        "The average correlation across all COs should ideally be ≥ 1.5. "
        "Low-correlation POs may indicate gaps requiring curriculum revision."
    ),
    "attainment": (
        "Attainment Calculation Summary:\n\n"
        "**Direct Attainment** is computed from assessment scores:\n"
        "- Internal tests (40% weightage)\n"
        "- End-semester exam (60% weightage)\n"
        "- Target threshold: 60%\n\n"
        "**Indirect Attainment** uses perception surveys:\n"
        "- Student exit survey\n"
        "- Alumni feedback\n"
        "- Target threshold: 60%\n\n"
        "**Final Attainment** = 0.8 × Direct + 0.2 × Indirect\n\n"
        "Current cycle: Direct avg 67.4%, Indirect avg 72.1%, Combined 68.3%"
    ),
}


def _get_response_text(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["co-po", "copo", "mapping", "correlation"]):
        return _SAMPLE_RESPONSES["copo"]
    if any(w in q for w in ["attainment", "compute", "calculate", "score"]):
        return _SAMPLE_RESPONSES["attainment"]
    return _SAMPLE_RESPONSES["default"]


def _stream_response(query: str) -> Generator[str, None, None]:
    """Simulate token-by-token streaming response."""
    response = _get_response_text(query)
    words = response.split(" ")
    chunk_size = 3
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]) + " "
        yield chunk
        time.sleep(0.04)


def _mock_sources(query: str) -> List[Dict[str, Any]]:
    """Return mock source citations relevant to the query."""
    return [
        {"title": "NBA Tier-I Criteria Manual 2022", "score": 0.94, "page": 42},
        {"title": "OBE Framework Implementation Guide", "score": 0.89, "page": 17},
        {"title": "CO-PO Mapping Best Practices", "score": 0.85, "page": 8},
    ]


# ─────────────────────────────────────────────────────────────
# Workflow trace panel
# ─────────────────────────────────────────────────────────────

def _render_workflow_trace(query: str) -> None:
    """Show a simplified workflow trace for the last query."""
    wf = get_nba_workflow()
    wf = simulate_workflow_step(wf, "intent_classifier", VizNodeStatus.COMPLETED,
                                 240, "Intent classified")
    wf = simulate_workflow_step(wf, "copo_agent", VizNodeStatus.COMPLETED,
                                 1100, "Agent processed")
    wf = simulate_workflow_step(wf, "validation_agent", VizNodeStatus.COMPLETED,
                                 320, "Validated")
    wf = simulate_workflow_step(wf, "rag_retrieval", VizNodeStatus.COMPLETED,
                                 680, "3 docs retrieved")
    wf = simulate_workflow_step(wf, "watsonx_granite", VizNodeStatus.COMPLETED,
                                 2100, "Response generated")
    wf = simulate_workflow_step(wf, "response_gen", VizNodeStatus.COMPLETED,
                                 180, "Formatted output")
    render_workflow_pipeline(wf, title="Execution Trace", show_summary=True)


# ─────────────────────────────────────────────────────────────
# Main render
# ─────────────────────────────────────────────────────────────

def render() -> None:
    init_chat_session()

    render_navbar(
        "AI_Chat",
        extra_actions_html=(
            '<div class="badge badge-green" style="font-size:0.6875rem;padding:3px 10px;">'
            '● Streaming Ready</div>'
        ),
    )
    render_page_hero(
        title="AI Assistant",
        subtitle="Powered by IBM Watsonx Granite  ·  RAG-Enhanced",
        icon="◆",
        accent_color="blue",
    )

    # ── Layout: chat | controls ────────────────────────────────
    chat_col, ctrl_col = st.columns([2.6, 1])

    # ── Control sidebar ────────────────────────────────────────
    with ctrl_col:
        render_watsonx_status_panel()

        with st.expander("⚙ Model Settings", expanded=True):
            render_model_selector()
            render_generation_controls()

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("💡 Suggested Prompts", expanded=True):
            selected = render_suggested_prompts()
            if selected and "chat_prefill" not in st.session_state:
                st.session_state.chat_prefill = selected

        st.markdown("<br>", unsafe_allow_html=True)

        # Clear chat
        if st.button("🗑 Clear Conversation", use_container_width=True, key="clear_chat_btn"):
            clear_chat_history()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Workflow trace panel
        if st.session_state.get("last_query"):
            with st.expander("⬢ Workflow Trace", expanded=False):
                _render_workflow_trace(st.session_state.last_query)

        # Show sources toggle
        st.session_state.show_sources = st.toggle(
            "Show source citations",
            value=st.session_state.get("show_sources", True),
            key="sources_toggle",
        )

    # ── Chat panel ─────────────────────────────────────────────
    with chat_col:
        st.markdown(
            '<div style="background:var(--bg-layer-01);border:1px solid var(--border-subtle);'
            'border-radius:var(--radius-xl);overflow:hidden;'
            'display:flex;flex-direction:column;min-height:70vh;">',
            unsafe_allow_html=True,
        )

        # Message history area
        with st.container():
            st.markdown(
                '<div style="padding:1.5rem;flex:1;overflow-y:auto;min-height:450px;">',
                unsafe_allow_html=True,
            )
            render_chat_history()
            if st.session_state.get("is_streaming"):
                render_streaming_indicator()
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Input row ──────────────────────────────────────────
        st.markdown(
            '<div style="padding:1rem 1.25rem;border-top:1px solid var(--border-subtle);">',
            unsafe_allow_html=True,
        )
        disabled = st.session_state.get("is_streaming", False)

        prefill = st.session_state.pop("chat_prefill", "")
        col_input, col_send = st.columns([10, 1])
        with col_input:
            user_input = st.text_input(
                "chat_input",
                value=prefill,
                placeholder="Ask about NBA accreditation, CO-PO, SAR, attainment…",
                disabled=disabled,
                label_visibility="collapsed",
                key="chat_input_field",
            )
        with col_send:
            send_btn = st.button("▶", key="chat_send_btn",
                                 disabled=disabled, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Process submission ─────────────────────────────────
        submitted = bool(user_input) and (send_btn or st.session_state.get("_chat_submit"))

        if submitted and not disabled:
            st.session_state.is_streaming   = True
            st.session_state.last_query      = user_input
            add_message("user", user_input)

            # Streaming response display
            full_response = ""
            stream_placeholder = st.empty()

            for chunk in _stream_response(user_input):
                full_response += chunk
                stream_placeholder.markdown(
                    f"""
                    <div class="message-row" style="flex-direction:row;align-items:flex-start;
                         padding:0 1.5rem;">
                      <div class="avatar avatar-ai">◆</div>
                      <div class="message-bubble ai">{full_response.replace(chr(10),'<br>')}
                        <span class="cursor-blink"></span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            stream_placeholder.empty()
            sources = _mock_sources(user_input) if st.session_state.get("show_sources", True) else []

            add_message(
                "assistant",
                full_response,
                model=st.session_state.get("selected_model", ""),
                sources=sources,
                latency_ms=int(len(full_response.split()) * 40),
            )

            # Fire workflow execution in background (non-blocking demo)
            try:
                exec_result = workflow_service.execute(
                    query=user_input,
                    triggered_by=auth_service.get_session().username
                    if auth_service.get_session() else "anonymous",
                )
                st.session_state["last_workflow_execution"] = exec_result
            except Exception:
                pass

            st.session_state.is_streaming = False
            st.rerun()
