import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.pdf_loader import process_pdf_document
from utils.rag_engine import get_rag_engine
from utils.vector_store import get_vector_store
from utils.helpers import format_timestamp, file_hash

st.markdown(
    """
<div class="section-header">
    <span style="font-size:1.6rem;">📚</span>
    <h2>Knowledge Base</h2>
    <span style="margin-left:8px;font-size:0.8rem;color:#7a9bb5;">NBA Document Repository · RAG-Powered</span>
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "📋 Document Library", "🔍 Semantic Search"])

with tab1:
    st.markdown("### 📤 Upload NBA Documents")
    st.markdown(
        """<div class="glass-card" style="background:rgba(79,172,254,0.04);border-color:rgba(79,172,254,0.2);">
        <div style="font-size:0.85rem;color:#a0b4c8;line-height:1.8;">
        Upload NBA documentation, accreditation guidelines, SAR templates, OBE handbooks, or any PDF relevant
        to NBA accreditation. Documents will be chunked, embedded, and indexed in ChromaDB + FAISS
        for semantic retrieval by the AI assistant.
        </div>
    </div>""",
        unsafe_allow_html=True,
    )

    col_up, col_cfg = st.columns([3, 1])
    with col_cfg:
        chunk_size = st.number_input("Chunk Size (chars)", 500, 2000, st.session_state.get("chunk_size", 1000), 100)
        chunk_overlap = st.number_input("Chunk Overlap", 0, 500, st.session_state.get("chunk_overlap", 200), 50)
        st.session_state.chunk_size = chunk_size
        st.session_state.chunk_overlap = chunk_overlap

    with col_up:
        uploaded_files = st.file_uploader(
            "Drag and drop PDFs here",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
            for f in uploaded_files:
                size_kb = len(f.getvalue()) / 1024
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:rgba(255,255,255,0.03);border:1px solid rgba(99,179,237,0.1);border-radius:8px;margin-bottom:4px;"><span style="font-size:1rem;">📄</span><span style="color:#e0e6f0;font-size:0.85rem;">{f.name}</span><span style="margin-left:auto;font-size:0.75rem;color:#7a9bb5;">{size_kb:.1f} KB</span></div>',
                    unsafe_allow_html=True,
                )

    if uploaded_files and st.button("🚀 Process & Index Documents", type="primary", use_container_width=True):
        rag = get_rag_engine()
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Processing: {file.name}...")
            content = file.getvalue()
            doc_hash = file_hash(content)

            # Check for duplicates
            existing_names = [d["name"] for d in st.session_state.documents]
            if file.name in existing_names:
                st.warning(f"⚠️ {file.name} already indexed. Skipping.")
                continue

            try:
                doc_data = process_pdf_document(
                    file_input=content,
                    source_name=file.name,
                    chunk_size=chunk_size,
                    overlap=chunk_overlap,
                )

                result = rag.ingest_document(doc_data["chunks"], file.name)

                if result["success"]:
                    st.session_state.documents.append({
                        "name": file.name,
                        "pages": doc_data["pages"],
                        "chunks": result["count"],
                        "uploaded": format_timestamp(),
                        "size_kb": round(len(content) / 1024, 1),
                        "hash": doc_hash,
                    })
                    st.session_state.total_chunks += result["count"]
                    st.session_state.chromadb_ready = True
                    st.session_state.rag_ready = True
                    st.success(f"✅ {file.name}: {doc_data['pages']} pages, {result['count']} chunks indexed.")
                else:
                    st.error(f"❌ {file.name}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"❌ {file.name}: {str(e)}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.text("✅ All documents processed!")
        vs_stats = get_vector_store().get_stats()
        st.session_state.vector_count = vs_stats.get("chroma_count", 0)

    # Stats cards
    st.divider()
    st.markdown("### 📊 Knowledge Base Statistics")

    vs_stats = get_vector_store().get_stats()
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("📁", "Total Files", len(st.session_state.documents), "#4facfe"),
        ("🔢", "Total Chunks", st.session_state.total_chunks, "#a78bfa"),
        ("🧬", "Vector Count", vs_stats.get("chroma_count", 0), "#22c55e"),
        ("⏱️", "Last Upload", st.session_state.documents[-1]["uploaded"][:10] if st.session_state.documents else "—", "#f59e0b"),
    ]
    for col, (icon, label, val, color) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(
                f"""<div class="kpi-card">
                <div style="font-size:1.4rem;">{icon}</div>
                <div class="kpi-value" style="background:{color};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-size:1.5rem;">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>""",
                unsafe_allow_html=True,
            )


with tab2:
    st.markdown("### 📋 Indexed Document Library")

    if not st.session_state.documents:
        st.markdown(
            """<div style="text-align:center;padding:3rem 1rem;color:#7a9bb5;">
            <div style="font-size:3rem;margin-bottom:1rem;">📂</div>
            <div style="font-size:1rem;">No documents indexed yet.</div>
            <div style="font-size:0.85rem;margin-top:0.5rem;">Upload PDFs in the Upload tab to build your knowledge base.</div>
        </div>""",
            unsafe_allow_html=True,
        )
    else:
        docs_df = pd.DataFrame(st.session_state.documents)[
            ["name", "uploaded", "pages", "chunks", "size_kb"]
        ].rename(columns={
            "name": "Document Name",
            "uploaded": "Uploaded At",
            "pages": "Pages",
            "chunks": "Chunks",
            "size_kb": "Size (KB)",
        })
        st.dataframe(docs_df, use_container_width=True, hide_index=True)

        if st.button("🗑️ Clear All Documents", type="secondary"):
            if st.session_state.documents:
                vs = get_vector_store()
                vs.delete_collection()
                st.session_state.documents = []
                st.session_state.total_chunks = 0
                st.session_state.vector_count = 0
                st.session_state.rag_ready = False
                st.session_state.chromadb_ready = False
                st.success("✅ All documents cleared from knowledge base.")
                st.rerun()

    # Suggested NBA docs
    st.divider()
    st.markdown("### 💡 Suggested NBA Documents to Upload")
    suggested_docs = [
        ("NBA Accreditation Manual", "Core accreditation guidelines and criteria"),
        ("OBE Handbook", "Outcome-Based Education implementation guide"),
        ("SAR Template", "Standard Self Assessment Report format"),
        ("CO-PO Mapping Guidelines", "Methodology for mapping Course to Program Outcomes"),
        ("Attainment Calculation Manual", "Direct and indirect assessment computation"),
        ("NBA Criterion Descriptions", "Detailed criterion-wise requirements"),
    ]
    for doc_name, desc in suggested_docs:
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(99,179,237,0.1);border-radius:10px;margin-bottom:6px;">
            <span style="font-size:1.1rem;">📄</span>
            <div>
                <div style="font-weight:600;color:#e0e6f0;font-size:0.85rem;">{doc_name}</div>
                <div style="color:#7a9bb5;font-size:0.75rem;">{desc}</div>
            </div>
        </div>""",
            unsafe_allow_html=True,
        )


with tab3:
    st.markdown("### 🔍 Semantic Search")
    st.caption("Search your knowledge base using natural language queries.")

    search_query = st.text_input("Search knowledge base...", placeholder="e.g., How to calculate CO attainment?")

    col_top_k, col_btn = st.columns([2, 1])
    with col_top_k:
        search_k = st.slider("Number of results", 1, 10, 5)
    with col_btn:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        search_clicked = st.button("🔍 Search", use_container_width=True)

    if search_clicked and search_query:
        rag = get_rag_engine()
        with st.spinner("Searching..."):
            results = rag.retrieve(search_query, top_k=search_k)

        if results:
            st.markdown(f"**Found {len(results)} relevant passages:**")
            for i, result in enumerate(results, 1):
                source = result.get("source", "Unknown")
                page = result.get("metadata", {}).get("page", "")
                score = result.get("score", 0)
                text = result.get("text", "")

                page_str = f" · Page {page}" if page else ""
                score_color = "#22c55e" if score > 0.7 else "#f59e0b" if score > 0.4 else "#ef4444"

                with st.expander(f"#{i} — {source}{page_str} · Relevance: {score:.2f}", expanded=i == 1):
                    st.markdown(
                        f'<div style="color:#c8d8e8;font-size:0.85rem;line-height:1.7;padding:8px;">{text}</div>',
                        unsafe_allow_html=True,
                    )
        elif not st.session_state.documents:
            st.info("📂 No documents indexed yet. Upload PDFs first.")
        else:
            st.info("🔍 No relevant passages found for your query.")

    elif search_clicked and not search_query:
        st.warning("Please enter a search query.")
