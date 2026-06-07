"""
app.py
NBA Enterprise AI Accreditation Platform – Main Entry Point.
Handles authentication, theme loading, sidebar navigation, and page routing.
"""

import streamlit as st

# ── Page config must be FIRST st call ─────────────────────────
st.set_page_config(
    page_title="NBA Accreditation Platform",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports after page config ──────────────────────────────────
from assets.custom_css import get_css
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from services.auth_service import auth_service, render_login_page, Permission


# ─────────────────────────────────────────────────────────────
# Theme injection
# ─────────────────────────────────────────────────────────────

def _inject_theme() -> None:
    st.markdown(get_css(), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Global session defaults
# ─────────────────────────────────────────────────────────────

def _init_global_session() -> None:
    defaults = {
        "wx_status":          "online",
        "selected_model":     "ibm/granite-13b-chat-v2",
        "temperature":        0.7,
        "max_tokens":         1024,
        "notification_count": 2,
        "active_page":        "Dashboard",
        "show_sources":       True,
        "vector_db_status":   "online",
        "vector_doc_count":   1247,
        "chat_history":       [],
        "is_streaming":       False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────
# Page router
# ─────────────────────────────────────────────────────────────

def _route_page(page: str) -> None:
    """Import and render the requested page module."""
    try:
        if page == "Dashboard":
            from pages.Dashboard import render
            render()

        elif page == "AI_Chat":
            if not auth_service.check_permission(Permission.USE_AI_CHAT):
                st.error("🔒 You do not have permission to access AI Chat.")
                return
            from pages.AI_Chat import render
            render()

        elif page == "COPO_Mapping":
            if not auth_service.check_permission(Permission.VIEW_COPO):
                st.error("🔒 Access denied.")
                return
            _stub_page("CO-PO Mapping", "⬡",
                       "Generate and analyse CO-PO correlation matrices using AI.")

        elif page == "Attainment_Calculator":
            if not auth_service.check_permission(Permission.VIEW_ATTAINMENT):
                st.error("🔒 Access denied.")
                return
            _stub_page("Attainment Calculator", "◈",
                       "Compute direct and indirect PO attainment with analytics.")

        elif page == "SAR_Builder":
            if not auth_service.check_permission(Permission.VIEW_SAR):
                st.error("🔒 Access denied.")
                return
            _stub_page("SAR Builder", "◉",
                       "Generate NBA SAR sections with evidence recommendations.")

        elif page == "Analytics":
            if not auth_service.check_permission(Permission.VIEW_ANALYTICS):
                st.error("🔒 Access denied.")
                return
            _stub_page("Analytics", "◇",
                       "KPI dashboards, trends, department benchmarking and risk scoring.")

        elif page == "Knowledge_Base":
            if not auth_service.check_permission(Permission.VIEW_KB):
                st.error("🔒 Access denied.")
                return
            _stub_page("Knowledge Base", "⬟",
                       "RAG-powered accreditation document store. Upload and query PDFs.")

        elif page == "Workflow_Monitor":
            if not auth_service.check_permission(Permission.VIEW_WORKFLOW):
                st.error("🔒 Access denied.")
                return
            from pages.Workflow_Monitor import render
            render()

        elif page == "Settings":
            _render_settings()

        elif page == "Admin_Panel":
            if not auth_service.check_permission(Permission.VIEW_ADMIN):
                st.error("🔒 Administrator access required.")
                return
            from pages.Admin_Panel import render
            render()

        else:
            st.warning(f"Page '{page}' not found.")

    except ImportError as e:
        _stub_page(page, "◆", f"Page module not yet implemented.\n\n`{e}`")


def _stub_page(title: str, icon: str, description: str) -> None:
    """Placeholder for pages not yet implemented."""
    render_navbar(st.session_state.get("active_page", "Dashboard"))
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;min-height:60vh;gap:1rem;
                    animation:pageFadeIn 0.4s ease both;">
          <div style="font-size:3rem;">{icon}</div>
          <h2 style="margin:0;font-size:1.5rem;color:var(--text-primary);">{title}</h2>
          <p style="color:var(--text-helper);text-align:center;max-width:480px;">
            {description}
          </p>
          <div class="badge badge-blue">Coming in next sprint</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_settings() -> None:
    """Inline Settings page."""
    render_navbar("Settings")
    sess = auth_service.get_session()

    st.markdown('<div class="page-content" style="padding:1.5rem 1.75rem;">', unsafe_allow_html=True)
    st.markdown("## ⊙ Settings")

    tab_model, tab_display, tab_account = st.tabs(["Model", "Display", "Account"])

    with tab_model:
        st.markdown("### Watsonx Model Configuration")
        models = [
            "ibm/granite-13b-chat-v2",
            "ibm/granite-34b-code-instruct",
            "ibm/granite-7b-instruct",
            "meta-llama/llama-3-70b-instruct",
        ]
        st.session_state.selected_model = st.selectbox(
            "Active Model", options=models,
            index=models.index(st.session_state.selected_model)
            if st.session_state.selected_model in models else 0,
        )
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0,
                                                  st.session_state.temperature, 0.05)
        st.session_state.max_tokens = st.slider("Max Tokens", 128, 4096,
                                                 st.session_state.max_tokens, 128)

    with tab_display:
        st.markdown("### Display Preferences")
        st.session_state.show_sources = st.toggle(
            "Show source citations in chat", value=st.session_state.show_sources
        )
        st.info("Dark theme is always active in this platform.")

    with tab_account:
        st.markdown("### Account")
        if sess:
            st.markdown(
                f"""
                <div class="glass-card" style="padding:1.25rem;max-width:400px;">
                  <div style="font-size:1rem;font-weight:600;color:var(--text-primary);
                               margin-bottom:0.75rem;">{sess.display_name}</div>
                  <div style="font-size:0.875rem;color:var(--text-secondary);
                               line-height:2;font-family:var(--font-mono);">
                    <div>Username: {sess.username}</div>
                    <div>Role: {sess.role.value}</div>
                    <div>Department: {sess.department}</div>
                    <div>Email: {sess.email}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.button("🔓 Sign Out", key="settings_logout"):
            auth_service.logout()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Logout handler in sidebar
# ─────────────────────────────────────────────────────────────

def _handle_logout_button() -> None:
    """Add logout button at bottom of sidebar."""
    with st.sidebar:
        st.markdown("<hr style='border-color:var(--border-subtle);margin:0 0 0.5rem;'>",
                    unsafe_allow_html=True)
        if st.button("🔓 Sign Out", key="sidebar_logout", use_container_width=True):
            auth_service.logout()
            st.rerun()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> None:
    _inject_theme()
    _init_global_session()

    # Authentication gate
    if not auth_service.is_authenticated():
        render_login_page()
        st.stop()
        return

    # Sidebar navigation (returns active page key)
    active_page = render_sidebar()
    _handle_logout_button()

    # Route to page
    _route_page(active_page)


if __name__ == "__main__":
    main()
else:
    # Streamlit runs app.py as a module; execute main at import time
    main()
