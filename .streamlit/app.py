import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Page configuration
st.set_page_config(
    page_title="NBA Enterprise AI Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.nba.ind.in",
        "About": "NBA Enterprise AI Accreditation Platform v1.0",
    },
)

# Global CSS
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark theme base */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1327 50%, #0a1628 100%);
        color: #e0e6f0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b3e 0%, #0a1628 100%);
        border-right: 1px solid rgba(99,179,237,0.15);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #a0b4c8;
    }

    /* Main content area */
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1400px;
    }

    /* Cards - Glassmorphism */
    .glass-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99,179,237,0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(99,179,237,0.35);
        box-shadow: 0 12px 40px rgba(99,179,237,0.1);
        transform: translateY(-2px);
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        border-radius: 16px 16px 0 0;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 48px rgba(79,172,254,0.15);
        border-color: rgba(79,172,254,0.4);
    }

    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        margin: 0.25rem 0;
    }

    .kpi-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #7a9bb5;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .kpi-delta {
        font-size: 0.8rem;
        color: #48bb78;
        margin-top: 0.25rem;
    }

    /* Status badges */
    .status-connected {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(72,187,120,0.12);
        color: #48bb78;
        border: 1px solid rgba(72,187,120,0.3);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .status-error {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(252,129,74,0.12);
        color: #fc814a;
        border: 1px solid rgba(252,129,74,0.3);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #e8f0fe;
        font-weight: 600;
    }

    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.4rem; }
    h3 { font-size: 1.1rem; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4facfe, #00b4d8);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 0.88rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(79,172,254,0.3);
        letter-spacing: 0.02em;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79,172,254,0.45);
        background: linear-gradient(135deg, #5fb6ff, #00c4e8);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(99,179,237,0.2);
        color: #e0e6f0;
        border-radius: 10px;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(79,172,254,0.5);
        box-shadow: 0 0 0 3px rgba(79,172,254,0.1);
    }

    /* Sliders */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid rgba(99,179,237,0.15);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #7a9bb5;
        font-weight: 500;
        font-size: 0.88rem;
        padding: 8px 16px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4facfe22, #00f2fe22) !important;
        color: #4facfe !important;
        border: 1px solid rgba(79,172,254,0.3);
    }

    /* Tables */
    .stDataFrame {
        border: 1px solid rgba(99,179,237,0.15);
        border-radius: 12px;
        overflow: hidden;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(99,179,237,0.15);
        border-radius: 12px;
        padding: 1rem;
    }

    [data-testid="stMetricValue"] {
        color: #4facfe;
        font-weight: 700;
    }

    /* Sidebar nav */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 10px;
        color: #a0b4c8;
        font-weight: 500;
        font-size: 0.9rem;
        margin-bottom: 4px;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
    }

    .nav-item:hover {
        background: rgba(79,172,254,0.1);
        color: #4facfe;
    }

    .nav-item.active {
        background: rgba(79,172,254,0.15);
        color: #4facfe;
        border: 1px solid rgba(79,172,254,0.25);
    }

    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        border-radius: 999px;
    }

    /* Chat messages */
    .chat-user {
        background: rgba(79,172,254,0.12);
        border: 1px solid rgba(79,172,254,0.2);
        border-radius: 16px 16px 4px 16px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: #e0e6f0;
    }

    .chat-ai {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(99,179,237,0.15);
        border-radius: 16px 16px 16px 4px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: #e0e6f0;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.03);
        border: 2px dashed rgba(79,172,254,0.3);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: rgba(79,172,254,0.6);
        background: rgba(79,172,254,0.05);
    }

    /* Sidebar logo area */
    .sidebar-logo {
        padding: 1.5rem 1rem 1rem;
        border-bottom: 1px solid rgba(99,179,237,0.1);
        margin-bottom: 1rem;
    }

    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.25rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(99,179,237,0.1);
    }

    .section-header h2 {
        margin: 0;
        font-size: 1.3rem;
        background: linear-gradient(135deg, #e8f0fe, #a0c4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Alert boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.04);
        border-radius: 10px;
        border: 1px solid rgba(99,179,237,0.15);
        color: #e0e6f0;
    }

    /* Selectbox placeholder */
    .stSelectbox [data-baseweb="select"] {
        background: rgba(255,255,255,0.04);
    }

    /* Divider */
    hr {
        border-color: rgba(99,179,237,0.1);
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
    ::-webkit-scrollbar-thumb { background: rgba(99,179,237,0.25); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(99,179,237,0.45); }

    /* Hide streamlit default elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Page transition */
    .stApp > div { animation: fadeIn 0.4s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

    /* IBM Badge */
    .ibm-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(20,122,255,0.12);
        color: #4facfe;
        border: 1px solid rgba(79,172,254,0.25);
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Heatmap cell overrides */
    .heatmap-cell {
        border-radius: 6px;
        font-weight: 600;
    }

    /* Tag / chip style */
    .tag {
        display: inline-block;
        background: rgba(79,172,254,0.12);
        color: #4facfe;
        border: 1px solid rgba(79,172,254,0.25);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.chat_history = []
    st.session_state.documents = []
    st.session_state.total_chunks = 0
    st.session_state.vector_count = 0
    st.session_state.ai_queries = 0
    st.session_state.watsonx_connected = False
    st.session_state.chromadb_ready = False
    st.session_state.rag_ready = False
    st.session_state.temperature = 0.7
    st.session_state.top_k = 5
    st.session_state.chunk_size = 1000
    st.session_state.chunk_overlap = 200
    st.session_state.embedding_model = "all-MiniLM-L6-v2"
    st.session_state.theme = "Dark"
    st.session_state.last_health_check = None

# Sidebar
with st.sidebar:
    st.markdown(
        """
    <div class="sidebar-logo">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
            <div style="width:42px;height:42px;background:linear-gradient(135deg,#4facfe,#00f2fe);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;">🎓</div>
            <div>
                <div style="font-size:0.95rem;font-weight:700;color:#e8f0fe;line-height:1.2;">NBA Enterprise</div>
                <div style="font-size:0.72rem;color:#7a9bb5;letter-spacing:0.05em;">AI ACCREDITATION PLATFORM</div>
            </div>
        </div>
        <div style="margin-top:8px;">
            <span class="ibm-badge">⚡ IBM Watsonx</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("**Navigation**")
    st.page_link("app.py", label="🏠 Home", icon=None)
    st.page_link("pages/Dashboard.py", label="📊 Dashboard")
    st.page_link("pages/AI_Chat.py", label="🤖 AI Assistant")
    st.page_link("pages/COPO_Mapping.py", label="🗺️ CO-PO Mapping")
    st.page_link("pages/Attainment_Calculator.py", label="📈 Attainment Calculator")
    st.page_link("pages/SAR_Builder.py", label="📄 SAR Builder")
    st.page_link("pages/Analytics.py", label="📉 Analytics")
    st.page_link("pages/Knowledge_Base.py", label="📚 Knowledge Base")
    st.page_link("pages/Settings.py", label="⚙️ Settings")

    st.divider()

    # Quick system status
    st.markdown("**System Status**")
    if st.session_state.watsonx_connected:
        st.markdown('<span class="status-connected">✓ Watsonx Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-error">✗ Watsonx Offline</span>', unsafe_allow_html=True)

    if st.session_state.chromadb_ready:
        st.markdown('<span class="status-connected">✓ ChromaDB Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-error">✗ ChromaDB Not Ready</span>', unsafe_allow_html=True)

    if st.session_state.rag_ready:
        st.markdown('<span class="status-connected">✓ RAG Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-error">✗ RAG Inactive</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<div style="font-size:0.72rem;color:#4a6070;text-align:center;">v1.0 · Built with IBM Watsonx</div>',
        unsafe_allow_html=True,
    )

# Home page
st.markdown(
    """
<div style="text-align:center;padding:3rem 1rem 2rem;">
    <div style="font-size:4rem;margin-bottom:1rem;">🎓</div>
    <h1 style="font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#4facfe,#00f2fe,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:0.5rem;">
        NBA Enterprise AI Platform
    </h1>
    <p style="color:#7a9bb5;font-size:1.1rem;margin-bottom:2rem;max-width:600px;margin-left:auto;margin-right:auto;">
        Powered by IBM Watsonx · Granite Models · LangChain RAG
    </p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:2.5rem;">
        <span class="tag">CO-PO Mapping</span>
        <span class="tag">Attainment Analysis</span>
        <span class="tag">SAR Generation</span>
        <span class="tag">AI Query Assistant</span>
        <span class="tag">Knowledge Base RAG</span>
        <span class="tag">Compliance Validation</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Feature cards
cols = st.columns(3)
features = [
    ("📊", "Dashboard", "Executive KPIs, readiness scores, department benchmarks, and trend analytics at a glance."),
    ("🤖", "AI Assistant", "IBM Watsonx + Granite powered chat with RAG for NBA-specific queries and guidance."),
    ("🗺️", "CO-PO Mapping", "Auto-generate CO-PO correlation matrices with heatmaps and gap analysis."),
    ("📈", "Attainment Calculator", "Compute direct & indirect CO/PO attainment with benchmarks and recommendations."),
    ("📄", "SAR Builder", "AI-assisted Self Assessment Report generation with PDF/DOCX export."),
    ("📚", "Knowledge Base", "Upload NBA documents, chunk & embed with ChromaDB + FAISS for semantic search."),
]

for i, (icon, title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(
            f"""
        <div class="glass-card" style="text-align:center;min-height:160px;">
            <div style="font-size:2.2rem;margin-bottom:0.6rem;">{icon}</div>
            <div style="font-weight:700;color:#e8f0fe;font-size:1rem;margin-bottom:0.5rem;">{title}</div>
            <div style="color:#7a9bb5;font-size:0.82rem;line-height:1.5;">{desc}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
<div class="glass-card" style="margin-top:1rem;background:linear-gradient(135deg,rgba(79,172,254,0.08),rgba(167,139,250,0.08));border-color:rgba(79,172,254,0.25);">
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <div style="font-size:1.8rem;">⚡</div>
        <div>
            <div style="font-weight:700;color:#e8f0fe;font-size:1rem;">Powered by IBM Watsonx AI</div>
            <div style="color:#7a9bb5;font-size:0.85rem;margin-top:3px;">
                Configure your Watsonx credentials in Settings → navigate to any module to begin.
            </div>
        </div>
        <div style="margin-left:auto;">
            <span class="ibm-badge">IBM Granite Model</span>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
