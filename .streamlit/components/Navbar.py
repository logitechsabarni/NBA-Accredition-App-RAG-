"""
components/navbar.py
Top navigation bar with breadcrumbs, system status, model badge, and notifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

import streamlit as st


# ─────────────────────────────────────────────────────────────
# Page metadata registry
# ─────────────────────────────────────────────────────────────

PAGE_META: Dict[str, Dict[str, str]] = {
    "Dashboard": {
        "title": "Dashboard",
        "subtitle": "Platform Overview",
        "icon": "⬛",
        "crumbs": ["Home", "Dashboard"],
    },
    "AI_Chat": {
        "title": "AI Assistant",
        "subtitle": "Conversational Intelligence",
        "icon": "◆",
        "crumbs": ["Home", "AI Agents", "Assistant"],
    },
    "COPO_Mapping": {
        "title": "CO-PO Mapping",
        "subtitle": "Correlation & Gap Analysis",
        "icon": "⬡",
        "crumbs": ["Home", "AI Agents", "CO-PO Mapping"],
    },
    "Attainment_Calculator": {
        "title": "Attainment Calculator",
        "subtitle": "Direct & Indirect Measurement",
        "icon": "◈",
        "crumbs": ["Home", "AI Agents", "Attainment"],
    },
    "SAR_Builder": {
        "title": "SAR Builder",
        "subtitle": "Self-Assessment Report Generator",
        "icon": "◉",
        "crumbs": ["Home", "AI Agents", "SAR Builder"],
    },
    "Analytics": {
        "title": "Analytics",
        "subtitle": "KPI · Trends · Benchmarks",
        "icon": "◇",
        "crumbs": ["Home", "Analytics"],
    },
    "Knowledge_Base": {
        "title": "Knowledge Base",
        "subtitle": "RAG-Powered Document Store",
        "icon": "⬟",
        "crumbs": ["Home", "Analytics", "Knowledge Base"],
    },
    "Workflow_Monitor": {
        "title": "Workflow Monitor",
        "subtitle": "LangGraph Execution Tracing",
        "icon": "⬢",
        "crumbs": ["Home", "Operations", "Workflow"],
    },
    "Settings": {
        "title": "Settings",
        "subtitle": "Platform Configuration",
        "icon": "⊙",
        "crumbs": ["Home", "Settings"],
    },
    "Admin_Panel": {
        "title": "Admin Panel",
        "subtitle": "User & System Management",
        "icon": "⊛",
        "crumbs": ["Home", "Admin"],
    },
}


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _crumb_html(crumbs: List[str]) -> str:
    parts: List[str] = []
    for i, crumb in enumerate(crumbs):
        if i < len(crumbs) - 1:
            parts.append(
                f'<span style="color:var(--text-disabled);">{crumb}</span>'
                f'<span style="color:var(--text-disabled);margin:0 4px;">/</span>'
            )
        else:
            parts.append(f'<span style="color:var(--text-primary);font-weight:500;">{crumb}</span>')
    return "".join(parts)


def _model_badge(model: str) -> str:
    short = model.split("/")[-1] if "/" in model else model
    return (
        f'<div class="badge badge-blue" style="font-size:0.6875rem;padding:3px 10px;">'
        f'<span style="margin-right:4px;font-size:0.6rem;">◆</span>{short}</div>'
    )


def _wx_status_badge(status: str) -> str:
    cfg = {
        "online":  ("green",  "●  Connected"),
        "offline": ("red",    "●  Offline"),
        "warning": ("yellow", "●  Degraded"),
    }.get(status, ("blue", "●  Unknown"))
    kind, label = cfg
    return (
        f'<div class="badge badge-{kind}" '
        f'style="font-size:0.6875rem;padding:3px 10px;">{label}</div>'
    )


def _notification_bell(count: int = 0) -> str:
    badge = (
        f'<span style="position:absolute;top:-4px;right:-4px;'
        f'width:14px;height:14px;border-radius:50%;background:var(--wx-red);'
        f'font-size:0.5625rem;display:flex;align-items:center;'
        f'justify-content:center;color:white;font-weight:700;">{count}</span>'
        if count > 0 else ""
    )
    return (
        f'<div style="position:relative;width:28px;height:28px;display:flex;'
        f'align-items:center;justify-content:center;cursor:pointer;'
        f'border-radius:6px;background:rgba(255,255,255,0.05);'
        f'border:1px solid var(--border-subtle);font-size:0.875rem;'
        f'transition:all 0.2s ease;" title="Notifications">'
        f'🔔{badge}</div>'
    )


def _user_avatar(user: str) -> str:
    initials = "".join(w[0].upper() for w in user.split()[:2]) or "U"
    return (
        f'<div style="width:30px;height:30px;border-radius:6px;'
        f'background:linear-gradient(135deg,#0f62fe,#be95ff);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:0.6875rem;font-weight:700;color:white;'
        f'cursor:pointer;" title="{user}">{initials}</div>'
    )


def _timestamp() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%d %b %Y  %H:%M UTC")


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def render_navbar(
    page: str,
    notification_count: int = 0,
    extra_actions_html: Optional[str] = None,
) -> None:
    """
    Render the sticky top navigation bar.

    Args:
        page: Active page key (must match PAGE_META keys).
        notification_count: Badge count on the bell icon.
        extra_actions_html: Optional HTML string appended to action row.
    """
    meta = PAGE_META.get(page, {
        "title": page,
        "subtitle": "",
        "icon": "◆",
        "crumbs": ["Home", page],
    })

    model   = st.session_state.get("selected_model", "ibm/granite-13b-chat-v2")
    wx_stat = st.session_state.get("wx_status", "online")
    user    = st.session_state.get("username", "Admin User")
    notif   = notification_count or st.session_state.get("notification_count", 0)

    crumb_str = _crumb_html(meta["crumbs"])
    model_b   = _model_badge(model)
    stat_b    = _wx_status_badge(wx_stat)
    bell      = _notification_bell(notif)
    avatar    = _user_avatar(user)
    ts        = _timestamp()
    extras    = extra_actions_html or ""

    st.markdown(
        f"""
        <div class="top-navbar">
          <!-- Left: breadcrumb -->
          <div style="display:flex;flex-direction:column;gap:2px;">
            <div class="navbar-breadcrumb" style="font-size:0.8125rem;">
              {crumb_str}
            </div>
            <div style="display:flex;align-items:center;gap:8px;margin-top:1px;">
              <span style="font-size:1rem;">{meta["icon"]}</span>
              <span style="font-size:1.0625rem;font-weight:600;
                           color:var(--text-primary);">{meta["title"]}</span>
              <span style="font-size:0.8125rem;color:var(--text-helper);
                           font-family:var(--font-mono);font-size:0.75rem;">
                — {meta["subtitle"]}
              </span>
            </div>
          </div>

          <!-- Right: actions -->
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
            <span style="font-size:0.6875rem;font-family:var(--font-mono);
                         color:var(--text-disabled);white-space:nowrap;">{ts}</span>
            {stat_b}
            {model_b}
            {extras}
            {bell}
            {avatar}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_hero(
    title: str,
    subtitle: str,
    icon: str = "◆",
    accent_color: str = "blue",
    actions_html: str = "",
) -> None:
    """
    Render a page hero / header section below the navbar.

    Args:
        title: Large page title.
        subtitle: Muted subtitle / description.
        icon: Emoji or symbol displayed in the accent block.
        accent_color: CSS variable suffix (blue, cyan, purple, green).
        actions_html: Optional right-aligned action buttons HTML.
    """
    grad_map = {
        "blue":   "var(--grad-blue)",
        "cyan":   "var(--grad-cyan)",
        "purple": "var(--grad-purple)",
        "green":  "var(--grad-green)",
    }
    grad = grad_map.get(accent_color, "var(--grad-blue)")

    st.markdown(
        f"""
        <div class="page-content" style="
          display:flex;align-items:center;justify-content:space-between;
          padding:1.5rem 1.75rem 1rem;
          border-bottom:1px solid var(--border-subtle);
          background:linear-gradient(180deg,rgba(15,98,254,0.04) 0%,transparent 100%);
        ">
          <div style="display:flex;align-items:center;gap:1rem;">
            <div style="
              width:48px;height:48px;border-radius:12px;
              background:{grad};
              display:flex;align-items:center;justify-content:center;
              font-size:1.4rem;
              box-shadow:0 4px 16px rgba(15,98,254,0.30);
            ">{icon}</div>
            <div>
              <h1 style="margin:0;font-size:1.625rem;font-weight:700;
                         letter-spacing:-0.02em;">{title}</h1>
              <p style="margin:2px 0 0;font-size:0.875rem;
                        color:var(--text-helper);font-family:var(--font-mono);">{subtitle}</p>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">{actions_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tab_bar(tabs: List[Dict[str, str]], active_key: str) -> str:
    """
    Render a custom tab bar and return the active tab key.
    Each tab dict: {"key": str, "label": str, "icon": str}.

    Note: Uses st.radio internally for state management.
    """
    labels = [f"{t.get('icon','')} {t['label']}" for t in tabs]
    keys   = [t["key"] for t in tabs]
    default_idx = keys.index(active_key) if active_key in keys else 0

    choice = st.radio(
        "tab_bar",
        options=labels,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    chosen_label = choice or labels[default_idx]
    chosen_idx = labels.index(chosen_label)
    return keys[chosen_idx]
