import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv, set_key
from utils.watsonx_client import get_watsonx_client, WatsonxClient

load_dotenv()

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">⚙️</span>
    <h2>Settings & Configuration</h2>
</div>
""",
    unsafe_allow_html=True,
)

ENV_PATH = Path(__file__).parent.parent / ".env"

tab1, tab2, tab3, tab4 = st.tabs([
    "🔑 Watsonx Credentials", "🤖 Model Settings", "📐 RAG Configuration", "🎨 UI Preferences"
])

# ── TAB 1 — Watsonx Credentials ───────────────────────────────────────────────
with tab1:
    st.markdown("### 🔑 IBM Watsonx Credentials")
    st.markdown(
        """<div class="glass-card" style="background:rgba(79,172,254,0.04);border-color:rgba(79,172,254,0.2);">
        <div style="display:flex;gap:10px;align-items:flex-start;">
            <span style="font-size:1.2rem;">ℹ️</span>
            <div style="font-size:0.85rem;color:#a0b4c8;line-height:1.7;">
                Credentials are stored in your <code style="color:#4facfe;background:rgba(79,172,254,0.1);padding:1px 6px;border-radius:4px;">.env</code> file and never hardcoded.
                Obtain your API key and Project ID from <a href="https://cloud.ibm.com/watsonx" target="_blank" style="color:#4facfe;">IBM Cloud → Watsonx</a>.
            </div>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )

    current_key = os.getenv("WATSONX_API_KEY", "")
    current_project = os.getenv("WATSONX_PROJECT_ID", "")
    current_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    col1, col2 = st.columns(2)
    with col1:
        api_key = st.text_input(
            "Watsonx API Key",
            value=current_key,
            type="password",
            placeholder="Enter your IBM Cloud API key",
            help="Your IBM Cloud API key for Watsonx authentication",
        )
        project_id = st.text_input(
            "Watsonx Project ID",
            value=current_project,
            placeholder="e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            help="Your Watsonx project ID from IBM Cloud",
        )

    with col2:
        watsonx_url = st.selectbox(
            "Watsonx Region URL",
            [
                "https://us-south.ml.cloud.ibm.com",
                "https://eu-de.ml.cloud.ibm.com",
                "https://eu-gb.ml.cloud.ibm.com",
                "https://jp-tok.ml.cloud.ibm.com",
                "https://au-syd.ml.cloud.ibm.com",
            ],
            index=0 if current_url not in [
                "https://us-south.ml.cloud.ibm.com",
                "https://eu-de.ml.cloud.ibm.com",
                "https://eu-gb.ml.cloud.ibm.com",
                "https://jp-tok.ml.cloud.ibm.com",
                "https://au-syd.ml.cloud.ibm.com",
            ] else [
                "https://us-south.ml.cloud.ibm.com",
                "https://eu-de.ml.cloud.ibm.com",
                "https://eu-gb.ml.cloud.ibm.com",
                "https://jp-tok.ml.cloud.ibm.com",
                "https://au-syd.ml.cloud.ibm.com",
            ].index(current_url),
        )

        # Masked display of current values
        if current_key:
            masked = current_key[:4] + "•" * 16 + current_key[-4:] if len(current_key) > 8 else "•" * 20
            st.markdown(f'<div style="font-size:0.78rem;color:#7a9bb5;margin-top:4px;">Current key: <code style="color:#22c55e;">{masked}</code></div>', unsafe_allow_html=True)
        if current_project:
            st.markdown(f'<div style="font-size:0.78rem;color:#7a9bb5;">Project ID: <code style="color:#4facfe;">{current_project}</code></div>', unsafe_allow_html=True)

    col_save, col_test, col_clear = st.columns(3)

    with col_save:
        if st.button("💾 Save Credentials", type="primary", use_container_width=True):
            if api_key and project_id:
                try:
                    ENV_PATH.touch(exist_ok=True)
                    set_key(str(ENV_PATH), "WATSONX_API_KEY", api_key)
                    set_key(str(ENV_PATH), "WATSONX_PROJECT_ID", project_id)
                    set_key(str(ENV_PATH), "WATSONX_URL", watsonx_url)
                    os.environ["WATSONX_API_KEY"] = api_key
                    os.environ["WATSONX_PROJECT_ID"] = project_id
                    os.environ["WATSONX_URL"] = watsonx_url

                    # Reset client so it picks up new creds
                    import utils.watsonx_client as wc_module
                    wc_module._watsonx_client = None

                    st.success("✅ Credentials saved to .env and applied.")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            else:
                st.warning("Please fill in both API Key and Project ID.")

    with col_test:
        if st.button("🔌 Test Connection", use_container_width=True):
            with st.spinner("Testing Watsonx connection..."):
                # Use current env values
                if api_key:
                    os.environ["WATSONX_API_KEY"] = api_key
                if project_id:
                    os.environ["WATSONX_PROJECT_ID"] = project_id
                os.environ["WATSONX_URL"] = watsonx_url

                import utils.watsonx_client as wc_module
                wc_module._watsonx_client = None
                wc = get_watsonx_client()
                result = wc.test_connection()

            st.session_state.watsonx_connected = result["connected"]
            if result["connected"]:
                st.success(f"✅ Connected! Response time: {result['response_time_ms']}ms")
                st.markdown(
                    f"""<div class="glass-card" style="margin-top:0.5rem;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.82rem;">
                        <div><span style="color:#7a9bb5;">Provider:</span> <span style="color:#e0e6f0;">{result['provider']}</span></div>
                        <div><span style="color:#7a9bb5;">Model:</span> <span style="color:#4facfe;">{result['model_id']}</span></div>
                        <div><span style="color:#7a9bb5;">Project ID:</span> <span style="color:#4facfe;">{str(result['project_id'])[:20]}...</span></div>
                        <div><span style="color:#7a9bb5;">Latency:</span> <span style="color:#22c55e;">{result['response_time_ms']}ms</span></div>
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.error("❌ Connection failed. Check credentials and try again.")

    with col_clear:
        if st.button("🗑️ Clear Credentials", use_container_width=True):
            try:
                set_key(str(ENV_PATH), "WATSONX_API_KEY", "")
                set_key(str(ENV_PATH), "WATSONX_PROJECT_ID", "")
                os.environ.pop("WATSONX_API_KEY", None)
                os.environ.pop("WATSONX_PROJECT_ID", None)
                st.session_state.watsonx_connected = False
                import utils.watsonx_client as wc_module
                wc_module._watsonx_client = None
                st.success("Credentials cleared.")
                st.rerun()
            except Exception as e:
                st.error(f"Clear failed: {e}")


# ── TAB 2 — Model Settings ────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🤖 Granite Model Configuration")

    GRANITE_MODELS = {
        "ibm/granite-13b-instruct-v2": "Granite 13B Instruct v2 (Recommended)",
        "ibm/granite-13b-chat-v2": "Granite 13B Chat v2",
        "ibm/granite-3-8b-instruct": "Granite 3 8B Instruct",
        "ibm/granite-3-2b-instruct": "Granite 3 2B Instruct (Fast)",
        "ibm/granite-20b-multilingual": "Granite 20B Multilingual",
        "ibm/granite-34b-code-instruct": "Granite 34B Code Instruct",
    }

    current_model = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        model_id = st.selectbox(
            "Active Granite Model",
            options=list(GRANITE_MODELS.keys()),
            format_func=lambda x: GRANITE_MODELS[x],
            index=list(GRANITE_MODELS.keys()).index(current_model)
            if current_model in GRANITE_MODELS else 0,
        )

        temperature = st.slider(
            "🌡️ Temperature",
            min_value=0.0, max_value=1.0,
            value=st.session_state.get("temperature", 0.7),
            step=0.05,
            help="Higher = more creative; lower = more deterministic",
        )
        st.session_state.temperature = temperature

    with col_m2:
        max_new_tokens = st.slider(
            "📏 Max New Tokens",
            min_value=128, max_value=4096,
            value=1024, step=128,
        )

        top_p = st.slider("🎯 Top-P (nucleus sampling)", 0.1, 1.0, 1.0, 0.05)
        repetition_penalty = st.slider("🔁 Repetition Penalty", 1.0, 2.0, 1.1, 0.05)

    st.divider()
    st.markdown("### 🎛️ Decoding Strategy")
    decoding_method = st.radio(
        "Method",
        ["greedy", "sample"],
        horizontal=True,
        help="Greedy = deterministic best token; Sample = probabilistic",
    )

    if st.button("💾 Save Model Settings", type="primary", use_container_width=True):
        set_key(str(ENV_PATH), "GRANITE_MODEL_ID", model_id)
        os.environ["GRANITE_MODEL_ID"] = model_id
        st.session_state.temperature = temperature

        import utils.watsonx_client as wc_module
        wc_module._watsonx_client = None

        st.success(f"✅ Model settings saved. Active model: {GRANITE_MODELS.get(model_id, model_id)}")

    st.markdown(
        f"""<div class="glass-card" style="margin-top:1rem;">
        <div style="font-size:0.75rem;color:#7a9bb5;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Active Model Card</div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:0.85rem;">
            <div><span style="color:#7a9bb5;">Model:</span> <span style="color:#4facfe;font-weight:600;">{model_id}</span></div>
            <div><span style="color:#7a9bb5;">Provider:</span> <span style="color:#e0e6f0;">IBM Watsonx.ai</span></div>
            <div><span style="color:#7a9bb5;">Temperature:</span> <span style="color:#a78bfa;">{temperature}</span></div>
            <div><span style="color:#7a9bb5;">Max Tokens:</span> <span style="color:#22c55e;">{max_new_tokens}</span></div>
            <div><span style="color:#7a9bb5;">Decoding:</span> <span style="color:#f59e0b;">{decoding_method}</span></div>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )


# ── TAB 3 — RAG Configuration ─────────────────────────────────────────────────
with tab3:
    st.markdown("### 🧠 RAG & Vector Database Configuration")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        top_k = st.slider(
            "🔍 Retrieval Top-K",
            min_value=1, max_value=20,
            value=st.session_state.get("top_k", 5),
            help="Number of chunks to retrieve per query",
        )
        st.session_state.top_k = top_k

        chunk_size = st.slider(
            "📦 Chunk Size (chars)",
            min_value=256, max_value=2048,
            value=st.session_state.get("chunk_size", 1000),
            step=128,
        )
        st.session_state.chunk_size = chunk_size

    with col_r2:
        embedding_models = {
            "all-MiniLM-L6-v2": "all-MiniLM-L6-v2 (384d, Fast)",
            "all-mpnet-base-v2": "all-mpnet-base-v2 (768d, Accurate)",
            "multi-qa-MiniLM-L6-cos-v1": "multi-qa-MiniLM-L6 (QA-optimized)",
        }
        embedding_model = st.selectbox(
            "🧬 Embedding Model",
            options=list(embedding_models.keys()),
            format_func=lambda x: embedding_models[x],
            index=list(embedding_models.keys()).index(
                st.session_state.get("embedding_model", "all-MiniLM-L6-v2")
            ) if st.session_state.get("embedding_model", "all-MiniLM-L6-v2") in embedding_models else 0,
        )
        st.session_state.embedding_model = embedding_model

        chunk_overlap = st.slider(
            "🔗 Chunk Overlap (chars)",
            min_value=0, max_value=400,
            value=st.session_state.get("chunk_overlap", 200),
            step=50,
        )
        st.session_state.chunk_overlap = chunk_overlap

    st.divider()
    st.markdown("### 🗄️ Vector Database Status")

    from utils.vector_store import get_vector_store
    vs_stats = get_vector_store().get_stats()

    vc1, vc2, vc3, vc4 = st.columns(4)
    vstats_list = [
        ("ChromaDB", "✅ Ready" if vs_stats["chroma_ready"] else "❌ Offline", "#22c55e" if vs_stats["chroma_ready"] else "#ef4444"),
        ("FAISS", "✅ Ready" if vs_stats["faiss_ready"] else "❌ Offline", "#22c55e" if vs_stats["faiss_ready"] else "#ef4444"),
        ("Vectors", str(vs_stats["chroma_count"]), "#4facfe"),
        ("FAISS Vecs", str(vs_stats["faiss_count"]), "#a78bfa"),
    ]
    for col, (label, val, color) in zip([vc1, vc2, vc3, vc4], vstats_list):
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                <div style="font-size:0.9rem;font-weight:600;color:{color};">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    if st.button("💾 Save RAG Settings", type="primary", use_container_width=True):
        st.session_state.top_k = top_k
        st.session_state.chunk_size = chunk_size
        st.session_state.chunk_overlap = chunk_overlap
        st.session_state.embedding_model = embedding_model

        import utils.rag_engine as rag_module
        rag_module._rag_engine = None

        set_key(str(ENV_PATH), "EMBEDDING_MODEL", embedding_model)
        st.success("✅ RAG settings saved!")


# ── TAB 4 — UI Preferences ────────────────────────────────────────────────────
with tab4:
    st.markdown("### 🎨 UI & Display Preferences")

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        theme = st.selectbox("Color Theme", ["Dark (Default)", "Dark Blue", "Dark Purple"], index=0)
        st.session_state.theme = theme

        date_format = st.selectbox("Date Format", ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"], index=0)

        items_per_page = st.slider("Items per Page (tables)", 5, 50, 20, 5)

    with col_u2:
        show_tooltips = st.toggle("Show Tooltips", value=True)
        auto_refresh = st.toggle("Auto-refresh Dashboard (30s)", value=False)
        compact_mode = st.toggle("Compact View Mode", value=False)
        show_source_citations = st.toggle("Show Source Citations in Chat", value=True)

    st.divider()
    st.markdown("### 🗂️ Export Defaults")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        default_export = st.selectbox("Default Export Format", ["CSV", "JSON", "XLSX", "TXT"])
    with col_e2:
        include_charts = st.toggle("Include Charts in Exports", value=True)

    if st.button("💾 Save Preferences", use_container_width=True):
        prefs = {
            "theme": theme, "date_format": date_format,
            "items_per_page": items_per_page, "show_tooltips": show_tooltips,
            "auto_refresh": auto_refresh, "compact_mode": compact_mode,
            "show_source_citations": show_source_citations,
            "default_export": default_export, "include_charts": include_charts,
        }
        try:
            prefs_path = Path(__file__).parent.parent / "data" / "preferences.json"
            prefs_path.parent.mkdir(exist_ok=True)
            with open(prefs_path, "w") as f:
                json.dump(prefs, f, indent=2)
            st.success("✅ Preferences saved!")
        except Exception as e:
            st.error(f"Save failed: {e}")

    st.divider()
    st.markdown("### 🔄 System Reset")
    st.warning("⚠️ Danger Zone: These actions are irreversible.")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🗑️ Clear Knowledge Base", use_container_width=True):
            from utils.vector_store import get_vector_store
            vs = get_vector_store()
            vs.delete_collection()
            st.session_state.documents = []
            st.session_state.total_chunks = 0
            st.session_state.vector_count = 0
            st.session_state.rag_ready = False
            st.session_state.chromadb_ready = False
            st.success("Knowledge base cleared.")
    with col_r2:
        if st.button("💬 Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.ai_queries = 0
            st.success("Chat history cleared.")
