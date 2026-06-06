"""
components/chat_components.py
ChatGPT-style streaming chat interface with source citations,
model selector, and Watsonx status panel.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generator, List, Optional

import streamlit as st


# ─────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────

Message = Dict[str, Any]
# {
#   "role": "user" | "assistant",
#   "content": str,
#   "timestamp": str (ISO),
#   "sources": List[Dict],       # optional
#   "model": str,                # optional, for assistant msgs
#   "latency_ms": int,           # optional
# }


# ─────────────────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────────────────

def init_chat_session() -> None:
    """Initialize chat session state."""
    defaults = {
        "chat_history":        [],
        "chat_input_disabled": False,
        "is_streaming":        False,
        "selected_model":      "ibm/granite-13b-chat-v2",
        "temperature":         0.7,
        "max_tokens":          1024,
        "show_sources":        True,
        "chat_session_id":     f"chat-{int(time.time())}",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def clear_chat_history() -> None:
    """Clear all messages from the chat."""
    st.session_state.chat_history = []
    st.session_state.chat_session_id = f"chat-{int(time.time())}"


def add_message(role: str, content: str, **kwargs: Any) -> None:
    """Append a message to chat history."""
    st.session_state.chat_history.append({
        "role":      role,
        "content":   content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    })


# ─────────────────────────────────────────────────────────────
# Message renderers
# ─────────────────────────────────────────────────────────────

def _format_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def _source_tags(sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return ""
    tags = "".join(
        f'<span class="source-tag">📄 {s.get("title","Source")[:28]}</span>'
        for s in sources[:5]
    )
    return (
        f'<div class="message-sources">'
        f'<div style="font-size:0.6875rem;color:var(--text-helper);'
        f'margin-bottom:4px;font-family:var(--font-mono);">SOURCES</div>'
        f'{tags}</div>'
    )


def _model_tag(model: str, latency_ms: Optional[int] = None) -> str:
    short = model.split("/")[-1] if "/" in model else model
    lat   = f" · {latency_ms}ms" if latency_ms else ""
    return (
        f'<div style="font-size:0.6rem;font-family:var(--font-mono);'
        f'color:var(--text-disabled);margin-top:4px;">◆ {short}{lat}</div>'
    )


def render_message(msg: Message) -> None:
    """Render a single chat message bubble."""
    role      = msg.get("role", "user")
    content   = msg.get("content", "")
    ts        = _format_ts(msg.get("timestamp", ""))
    sources   = msg.get("sources", []) if st.session_state.get("show_sources", True) else []
    model     = msg.get("model", "")
    latency   = msg.get("latency_ms")

    is_user = role == "user"
    row_dir  = "row-reverse" if is_user else "row"
    av_class = "avatar-user" if is_user else "avatar-ai"
    av_icon  = "U" if is_user else "◆"
    bub_class = "user" if is_user else "ai"
    align    = "flex-end" if is_user else "flex-start"

    src_html   = _source_tags(sources) if not is_user else ""
    model_html = _model_tag(model, latency) if model and not is_user else ""

    # Escape HTML in content
    safe_content = (
        content
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )

    st.markdown(
        f"""
        <div class="message-row" style="flex-direction:{row_dir};
             align-items:flex-start;">
          <div class="avatar {av_class}">{av_icon}</div>
          <div style="max-width:75%;display:flex;flex-direction:column;
                      align-items:{align};">
            <div class="message-bubble {bub_class}">{safe_content}</div>
            {src_html}
            {model_html}
            <div class="message-timestamp" style="margin-top:3px;">{ts}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    """Render the full chat message history."""
    history: List[Message] = st.session_state.get("chat_history", [])
    if not history:
        _render_empty_state()
        return
    for msg in history:
        render_message(msg)


def _render_empty_state() -> None:
    st.markdown(
        """
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:300px;gap:12px;opacity:0.6;">
          <div style="font-size:3rem;">◆</div>
          <div style="font-size:1.0625rem;font-weight:600;
                      color:var(--text-primary);">How can I help today?</div>
          <div style="font-size:0.875rem;color:var(--text-helper);text-align:center;
                      max-width:380px;">
            Ask anything about NBA accreditation, CO-PO mapping,
            attainment calculations, or SAR generation.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_streaming_indicator() -> None:
    """Show animated typing / streaming indicator."""
    st.markdown(
        """
        <div class="message-row" style="flex-direction:row;align-items:flex-start;">
          <div class="avatar avatar-ai">◆</div>
          <div class="message-bubble ai" style="padding:0.875rem 1.25rem;">
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Control panel
# ─────────────────────────────────────────────────────────────

_MODELS: List[Dict[str, str]] = [
    {"id": "ibm/granite-13b-chat-v2",      "label": "Granite 13B Chat v2",     "badge": "DEFAULT"},
    {"id": "ibm/granite-34b-code-instruct", "label": "Granite 34B Code",        "badge": "CODE"},
    {"id": "ibm/granite-7b-instruct",       "label": "Granite 7B Instruct",     "badge": "FAST"},
    {"id": "meta-llama/llama-3-70b-instruct","label": "Llama 3 70B Instruct",   "badge": "LARGE"},
    {"id": "mistralai/mixtral-8x7b-instruct","label": "Mixtral 8×7B Instruct",  "badge": "MoE"},
]


def render_model_selector() -> None:
    """Render the model selector dropdown in the sidebar/panel."""
    options = [m["id"] for m in _MODELS]
    labels  = [f"{m['label']}  [{m['badge']}]" for m in _MODELS]

    current  = st.session_state.get("selected_model", options[0])
    cur_idx  = options.index(current) if current in options else 0

    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:var(--text-helper);margin-bottom:6px;">'
        'Model</div>',
        unsafe_allow_html=True,
    )
    choice = st.selectbox(
        "model_select",
        options=labels,
        index=cur_idx,
        label_visibility="collapsed",
        key="model_selectbox",
    )
    chosen_idx = labels.index(choice)
    st.session_state.selected_model = options[chosen_idx]


def render_generation_controls() -> None:
    """Render temperature and max_tokens sliders."""
    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:var(--text-helper);margin:12px 0 6px;">'
        'Temperature</div>',
        unsafe_allow_html=True,
    )
    st.session_state.temperature = st.slider(
        "temperature_slider",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("temperature", 0.7),
        step=0.05,
        label_visibility="collapsed",
        key="temp_slider",
    )

    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:var(--text-helper);margin:12px 0 6px;">'
        'Max Tokens</div>',
        unsafe_allow_html=True,
    )
    st.session_state.max_tokens = st.slider(
        "max_tokens_slider",
        min_value=128,
        max_value=4096,
        value=st.session_state.get("max_tokens", 1024),
        step=128,
        label_visibility="collapsed",
        key="tok_slider",
    )


def render_watsonx_status_panel() -> None:
    """Render the Watsonx connection status card."""
    status = st.session_state.get("wx_status", "online")
    dot_class = {"online": "online", "offline": "offline", "warning": "warning"}.get(
        status, "idle"
    )
    label_map = {
        "online":  ("Connected", "var(--wx-green)"),
        "offline": ("Disconnected", "var(--wx-red)"),
        "warning": ("Degraded", "var(--wx-yellow)"),
    }
    label, lcolor = label_map.get(status, ("Unknown", "var(--text-helper)"))

    model = st.session_state.get("selected_model", "ibm/granite-13b-chat-v2")
    temp  = st.session_state.get("temperature", 0.7)
    maxt  = st.session_state.get("max_tokens", 1024)

    st.markdown(
        f"""
        <div class="glass-card" style="padding:1rem;margin-bottom:0.75rem;">
          <div style="display:flex;align-items:center;justify-content:space-between;
                      margin-bottom:0.75rem;">
            <div class="watsonx-logo-badge">watsonx</div>
            <div class="status-indicator">
              <span class="status-dot {dot_class}"></span>
              <span style="color:{lcolor};font-size:0.75rem;">{label}</span>
            </div>
          </div>
          <div style="font-size:0.75rem;color:var(--text-helper);font-family:var(--font-mono);
                      line-height:1.8;">
            <div>Model  <span style="color:var(--text-primary);">{model.split('/')[-1]}</span></div>
            <div>Temp   <span style="color:var(--text-primary);">{temp}</span></div>
            <div>Tokens <span style="color:var(--text-primary);">{maxt}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Suggested prompts
# ─────────────────────────────────────────────────────────────

_SUGGESTED_PROMPTS = [
    "Generate CO-PO mapping for CSE curriculum",
    "Calculate attainment for PO1 using direct method",
    "Create SAR Criteria 3 narrative",
    "Identify improvement gaps for last cycle",
    "Summarize accreditation readiness score",
    "What is NBA Tier-I compliance threshold?",
]


def render_suggested_prompts() -> Optional[str]:
    """
    Render quick-prompt chips. Returns the selected prompt text or None.
    """
    st.markdown(
        '<div style="font-size:0.6875rem;color:var(--text-helper);'
        'font-family:var(--font-mono);margin-bottom:6px;">SUGGESTED</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, prompt in enumerate(_SUGGESTED_PROMPTS[:6]):
        col = cols[i % 2]
        with col:
            if st.button(
                f"↳ {prompt}",
                key=f"sugg_{i}",
                use_container_width=True,
            ):
                return prompt
    return None


# ─────────────────────────────────────────────────────────────
# Input bar
# ─────────────────────────────────────────────────────────────

def render_chat_input(
    placeholder: str = "Ask about NBA accreditation, CO-PO, SAR…",
    on_submit: Optional[Callable[[str], None]] = None,
) -> Optional[str]:
    """
    Render the chat input area with send button.

    Returns the submitted message text, or None.
    """
    disabled = st.session_state.get("is_streaming", False)

    with st.container():
        st.markdown(
            '<div class="chat-input-area"><div class="chat-input-wrapper">',
            unsafe_allow_html=True,
        )
        col_input, col_send = st.columns([9, 1])
        with col_input:
            user_input = st.text_input(
                "chat_input",
                placeholder=placeholder,
                disabled=disabled,
                label_visibility="collapsed",
                key="chat_input_field",
            )
        with col_send:
            send_clicked = st.button(
                "▶",
                disabled=disabled,
                key="chat_send_btn",
                use_container_width=True,
            )
        st.markdown("</div></div>", unsafe_allow_html=True)

    submitted = user_input and (send_clicked or st.session_state.get("_enter_submit", False))
    if submitted:
        if on_submit:
            on_submit(user_input)
        return user_input
    return None


# ─────────────────────────────────────────────────────────────
# Full chat panel (composite)
# ─────────────────────────────────────────────────────────────

def render_chat_panel(
    on_message: Optional[Callable[[str], Generator[str, None, None]]] = None,
) -> None:
    """
    Render the complete chat panel including history, streaming,
    and input. Handles streaming via generator from on_message.

    Args:
        on_message: Callable(user_msg) → Generator[str, None, None]
                    yielding token chunks for streaming display.
    """
    init_chat_session()

    # History area
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    render_chat_history()
    if st.session_state.get("is_streaming"):
        render_streaming_indicator()
    st.markdown("</div>", unsafe_allow_html=True)

    # Input
    user_text = render_chat_input()

    if user_text and on_message:
        add_message("user", user_text)
        st.session_state.is_streaming = True

        full_response = ""
        placeholder   = st.empty()
        gen = on_message(user_text)
        for chunk in gen:
            full_response += chunk
            placeholder.markdown(
                f"""
                <div class="message-row" style="flex-direction:row;">
                  <div class="avatar avatar-ai">◆</div>
                  <div class="message-bubble ai">{full_response}
                    <span class="cursor-blink"></span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        placeholder.empty()
        add_message(
            "assistant",
            full_response,
            model=st.session_state.get("selected_model", ""),
        )
        st.session_state.is_streaming = False
        st.rerun()
