"""
components/sidebar.py
Enterprise sidebar navigation with IBM Watsonx branding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import streamlit as st


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class NavItem:
    key: str
    label: str
    icon: str
    page: str
    badge: Optional[str] = None
    badge_type: str = "blue"  # blue | green | red | yellow


@dataclass
class NavSection:
    title: str
    items: List[NavItem] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Navigation structure
# ─────────────────────────────────────────────────────────────

_NAV_STRUCTURE: List[NavSection] = [
    NavSection(
        title="Overview",
        items=[
            NavItem("dashboard", "Dashboard", "⬛", "Dashboard"),
        ],
    ),
    NavSection(
        title="AI Agents",
        items=[
            NavItem("ai_chat",   "AI Assistant",  "◆", "AI_Chat",   badge="LIVE", badge_type="green"),
            NavItem("copo",      "CO-PO Mapping", "⬡", "COPO_Mapping"),
            NavItem("attain",    "Attainment",     "◈", "Attainment_Calculator"),
            NavItem("sar",       "SAR Builder",    "◉", "SAR_Builder"),
        ],
    ),
    NavSection(
        title="Analytics",
        items=[
            NavItem("analytics", "Analytics",    "◇", "Analytics"),
            NavItem("kb",        "Knowledge Base","⬟", "Knowledge_Base"),
        ],
    ),
    NavSection(
        title="Operations",
        items=[
            NavItem("workflow",  "Workflow",      "⬢", "Workflow_Monitor"),
            NavItem("settings",  "Settings",      "⊙", "Settings"),
            NavItem("admin",     "Admin Panel",   "⊛", "Admin_Panel", badge="ADMIN", badge_type="purple"),
        ],
    ),
]


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _badge_html(text: str, kind: str) -> str:
    return (
        f'<span class="badge badge-{kind}" '
        f'style="font-size:0.6rem;padding:1px 6px;margin-left:auto;">'
        f'{text}</span>'
    )


def _init_session() -> None:
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Dashboard"
    if "wx_status" not in st.session_state:
        st.session_state.wx_status = "online"
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False


def _status_block() -> None:
    """Watsonx service status indicator at sidebar bottom."""
    status = st.session_state.get("wx_status", "online")
    dot_class = {
        "online":  "online",
        "offline": "offline",
        "warning": "warning",
    }.get(status, "idle")

    label_map = {
        "online":  "Watsonx · Connected",
        "offline": "Watsonx · Offline",
        "warning": "Watsonx · Degraded",
    }
    label = label_map.get(status, "Unknown")

    model = st.session_state.get("selected_model", "ibm/granite-13b-chat-v2")
    short_model = model.split("/")[-1] if "/" in model else model

    st.markdown(
        f"""
        <div class="sidebar-footer">
          <div class="status-indicator" style="margin-bottom:6px;">
            <span class="status-dot {dot_class}"></span>
            <span style="color:var(--text-secondary);font-size:0.75rem;">{label}</span>
          </div>
          <div style="font-size:0.6875rem;color:var(--text-helper);font-family:var(--font-mono);
                      margin-bottom:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            {short_model}
          </div>
          <div class="watsonx-logo-badge" style="font-size:0.6875rem;">watsonx</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    """
    Render the full sidebar and return the currently active page key.

    Usage in app.py:
        from components.sidebar import render_sidebar
        active_page = render_sidebar()
    """
    _init_session()

    with st.sidebar:
        # ── Logo / brand ─────────────────────────────────────
        st.markdown(
            """
            <div class="sidebar-logo">
              <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;border-radius:8px;
                            background:linear-gradient(135deg,#0f62fe,#33b1ff);
                            display:flex;align-items:center;justify-content:center;
                            font-size:1.1rem;font-weight:700;color:white;">N</div>
                <div>
                  <div class="sidebar-logo-text">NBA Accredit</div>
                  <div class="sidebar-logo-sub">Enterprise AI Platform</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Navigation sections ───────────────────────────────
        for section in _NAV_STRUCTURE:
            st.markdown(
                f'<div class="sidebar-section-label">{section.title}</div>',
                unsafe_allow_html=True,
            )
            for item in section.items:
                is_active = st.session_state.active_page == item.page
                active_cls = " active" if is_active else ""
                badge_html = _badge_html(item.badge, item.badge_type) if item.badge else ""

                clicked = st.button(
                    f"{item.icon}  {item.label}",
                    key=f"nav_{item.key}",
                    use_container_width=True,
                )
                if clicked:
                    st.session_state.active_page = item.page
                    st.rerun()

                # Inject active styling after render
                if is_active:
                    st.markdown(
                        f"""
                        <style>
                        [data-testid="stSidebar"] div[data-testid="stButton"]:has(button[kind="secondary"]:nth-of-type(1)) + div {{
                            display: none;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

        # Spacer pushes footer down
        st.markdown(
            '<div style="flex:1;min-height:40px;"></div>',
            unsafe_allow_html=True,
        )

        # ── Version / build info ─────────────────────────────
        st.markdown(
            """
            <div style="padding:0.5rem 1.25rem;font-size:0.6875rem;
                        font-family:var(--font-mono);color:var(--text-disabled);">
              v2.4.1 · build 20250115
            </div>
            """,
            unsafe_allow_html=True,
        )

        _status_block()

    return st.session_state.active_page


def render_sidebar_html_only() -> str:
    """
    Return a pure HTML string for the sidebar navigation
    (useful for embedding in custom multi-page layouts).
    """
    _init_session()
    active = st.session_state.active_page
    sections_html: List[str] = []

    sections_html.append(
        """
        <div class="sidebar-logo">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;border-radius:8px;
                        background:linear-gradient(135deg,#0f62fe,#33b1ff);
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.1rem;font-weight:700;color:white;">N</div>
            <div>
              <div class="sidebar-logo-text">NBA Accredit</div>
              <div class="sidebar-logo-sub">Enterprise AI Platform</div>
            </div>
          </div>
        </div>
        """
    )

    for section in _NAV_STRUCTURE:
        sections_html.append(
            f'<div class="sidebar-section-label">{section.title}</div>'
        )
        for item in section.items:
            is_active = active == item.page
            cls = "nav-item active" if is_active else "nav-item"
            badge_part = _badge_html(item.badge, item.badge_type) if item.badge else ""
            sections_html.append(
                f"""
                <div class="{cls}" data-page="{item.page}">
                  <span class="nav-icon">{item.icon}</span>
                  <span style="flex:1;">{item.label}</span>
                  {badge_part}
                </div>
                """
            )

    sections_html.append(
        """
        <div class="sidebar-footer" style="margin-top:auto;">
          <div class="watsonx-logo-badge">watsonx</div>
        </div>
        """
    )

    return "\n".join(sections_html)


def get_active_page() -> str:
    """Return the currently active page without re-rendering."""
    _init_session()
    return st.session_state.active_page


def set_active_page(page: str) -> None:
    """Programmatically navigate to a page."""
    _init_session()
    st.session_state.active_page = page
