import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import time
from datetime import datetime
import json
from utils.rag_engine import get_rag_engine
from utils.watsonx_client import get_watsonx_client
from utils.helpers import log_query

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">🤖</span>
    <h2>AI Assistant</h2>
    <span class="ibm-badge" style="margin-left:8px;">IBM Watsonx · Granite</span>
</div>
""",
    unsafe_allow_html=True,
)

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 Model Configuration")

    st.markdown(
        """
    <div class="glass-card" style="margin-bottom:1rem;">
        <div style="font-size:0.75rem;color:#7a9bb5;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.08em;">Model Info</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#a0b4c8;font-size:0.82rem;">Provider</span>
            <span style="color:#4facfe;font-size:0.82rem;font-weight:600;">IBM Watsonx</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#a0b4c8;font-size:0.82rem;">Model</span>
            <span style="color:#4facfe;font-size:0.82rem;font-weight:600;">Granite</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#a0b4c8;font-size:0.82rem;">RAG</span>
            <span style="color:#22c55e;font-size:0.82rem;font-weight:600;">Enabled</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    temperature = st.slider("🌡️ Temperature", 0.0, 1.0, st.session_state.get("temperature", 0.7), 0.05)
    top_k = st.slider("🔍 Top-K Retrieval", 1, 15, st.session_state.get("top_k", 5))
    use_rag = st.toggle("🧠 Enable RAG", value=True)

    st.session_state.temperature = temperature
    st.session_state.top_k = top_k

    st.divider()

    # Connection status
    wc = get_watsonx_client()
    if st.session_state.watsonx_connected:
        st.markdown('<span class="status-connected">✓ Watsonx Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-error">✗ Not Connected — Configure in Settings</span>', unsafe_allow_html=True)

    st.divider()

    # Suggested queries
    st.markdown("### 💡 Suggested Questions")
    suggestions = [
        "What is CO-PO mapping in NBA?",
        "How to calculate CO attainment?",
        "Explain direct vs indirect assessment",
        "What are NBA Tier-I criteria?",
        "How to prepare SAR for NBA?",
        "What is the target attainment level?",
    ]
    for suggestion in suggestions:
        if st.button(suggestion, key=f"sug_{suggestion[:20]}", use_container_width=True):
            st.session_state.pending_query = suggestion

    st.divider()
    col_clear, col_dl = st.columns(2)
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    with col_dl:
        if st.session_state.chat_history:
            chat_text = "\n\n".join(
                f"[{msg['role'].upper()}] {msg['content']}" for msg in st.session_state.chat_history
            )
            st.download_button(
                "⬇️ Export",
                data=chat_text,
                file_name=f"nba_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ── Chat history display ──────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_history:
        st.markdown(
            """
        <div style="text-align:center;padding:3rem 1rem;">
            <div style="font-size:3rem;margin-bottom:1rem;">🎓</div>
            <div style="font-size:1.2rem;font-weight:600;color:#e8f0fe;margin-bottom:0.5rem;">NBA AI Assistant</div>
            <div style="color:#7a9bb5;font-size:0.9rem;max-width:480px;margin:0 auto;line-height:1.6;">
                Ask me anything about NBA accreditation, CO-PO mapping, attainment calculation, SAR preparation, or compliance requirements.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "")
            sources = msg.get("sources", [])

            if role == "user":
                st.markdown(
                    f"""
                <div class="chat-user">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <span style="font-size:1rem;">👤</span>
                        <span style="font-weight:600;color:#e8f0fe;font-size:0.85rem;">You</span>
                        <span style="margin-left:auto;font-size:0.72rem;color:#4a6070;">{timestamp}</span>
                    </div>
                    <div style="color:#c8d8e8;line-height:1.6;">{content}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div class="chat-ai">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <span style="font-size:1rem;">🤖</span>
                        <span style="font-weight:600;color:#4facfe;font-size:0.85rem;">NBA AI</span>
                        <span class="ibm-badge" style="font-size:0.65rem;padding:2px 6px;">Watsonx</span>
                        <span style="margin-left:auto;font-size:0.72rem;color:#4a6070;">{timestamp}</span>
                    </div>
                    <div style="color:#c8d8e8;line-height:1.7;white-space:pre-wrap;">{content}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if sources:
                    with st.expander(f"📚 {len(sources)} Source(s) Retrieved", expanded=False):
                        for src in sources:
                            st.markdown(f"<div style='color:#7a9bb5;font-size:0.8rem;'>{src}</div>", unsafe_allow_html=True)

# ── Input area ────────────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_query", None)
user_input = st.chat_input("Ask about NBA accreditation, CO-PO mapping, SAR, attainment...", key="chat_input")

query = pending or user_input

if query:
    timestamp = datetime.now().strftime("%H:%M")

    # Add user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": query,
        "timestamp": timestamp,
    })

    # Generate AI response
    with st.spinner("🤖 Generating response with IBM Watsonx..."):
        try:
            rag = get_rag_engine(
                top_k=top_k,
                temperature=temperature,
            )
            result = rag.generate(
                query=query,
                chat_history=st.session_state.chat_history[:-1],
                use_rag=use_rag,
            )
            response = result["response"]
            sources = result.get("sources", [])
            context_used = result.get("context_used", False)

            rag_note = ""
            if context_used:
                rag_note = f"\n\n*📚 {result.get('chunks_retrieved', 0)} context chunks retrieved from knowledge base.*"

        except Exception as e:
            response = f"⚠️ **Connection Error**: {str(e)}\n\nPlease configure IBM Watsonx credentials in the **Settings** page to enable AI responses."
            sources = []
            rag_note = ""

    st.session_state.ai_queries = st.session_state.get("ai_queries", 0) + 1
    log_query(query, len(response))

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response + rag_note,
        "timestamp": datetime.now().strftime("%H:%M"),
        "sources": sources,
    })
    st.rerun()
