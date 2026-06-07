"""
pages/Dashboard.py
NBA Enterprise AI Platform – Dashboard.
KPI cards, live system status, attainment overview, readiness score,
and interactive Plotly analytics.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import streamlit as st

from components.navbar import render_navbar, render_page_hero
from components.metric_cards import (
    render_kpi_row,
    render_stat_row,
    render_compliance_ring,
    render_labeled_progress,
    render_risk_badge,
)
from components.charts import (
    render_attainment_bar,
    render_trend_line,
    render_donut_chart,
    render_gauge,
    render_radar_chart,
)
from components.workflow_visualizer import (
    get_nba_workflow,
    render_workflow_pipeline,
    NodeStatus,
    simulate_workflow_step,
)
from services.auth_service import auth_service


# ─────────────────────────────────────────────────────────────
# Demo data generators
# ─────────────────────────────────────────────────────────────

def _kpi_data() -> List[Dict[str, Any]]:
    return [
        {
            "label": "Readiness Score",
            "value": 74.2,
            "unit": "%",
            "delta": 3.8,
            "delta_unit": "%",
            "icon": "◉",
            "color": "blue",
            "description": "NBA accreditation readiness",
        },
        {
            "label": "PO Attainment Avg",
            "value": 67.4,
            "unit": "%",
            "delta": 2.1,
            "delta_unit": "%",
            "icon": "◈",
            "color": "cyan",
            "description": "Direct + Indirect combined",
        },
        {
            "label": "Critical Gaps",
            "value": 3,
            "delta": -2,
            "icon": "⚠",
            "color": "yellow",
            "description": "Requires immediate action",
        },
        {
            "label": "CI Actions",
            "value": 18,
            "delta": 5,
            "icon": "🔄",
            "color": "green",
            "description": "Active corrective actions",
        },
        {
            "label": "Documents Indexed",
            "value": 1247,
            "delta": 84,
            "icon": "⬟",
            "color": "purple",
            "description": "Vector knowledge base",
        },
        {
            "label": "AI Queries Today",
            "value": 342,
            "delta": 28,
            "icon": "◆",
            "color": "blue",
            "description": "Watsonx API calls",
        },
    ]


def _po_attainment() -> Dict[str, Any]:
    labels = [f"PO{i}" for i in range(1, 13)]
    direct = [72.1, 65.3, 58.9, 78.4, 61.2, 55.7, 70.8, 63.5, 68.9, 74.2, 59.1, 66.8]
    indirect = [78.3, 70.1, 62.4, 82.1, 67.8, 60.2, 75.4, 68.9, 73.2, 79.5, 63.7, 71.0]
    return {"labels": labels, "direct": direct, "indirect": indirect}


def _trend_data() -> Dict[str, Any]:
    semesters = ["S1 23", "S2 23", "S1 24", "S2 24", "S1 25"]
    return {
        "x": semesters,
        "series": [
            {"name": "Readiness Score",   "values": [62.1, 65.8, 69.3, 72.1, 74.2], "color": "#4589ff"},
            {"name": "Direct Attainment", "values": [58.4, 61.2, 64.8, 66.9, 67.4], "color": "#33b1ff"},
        ],
    }


def _criteria_compliance() -> Dict[str, Any]:
    return {
        "labels": [f"Criteria {i}" for i in range(1, 9)],
        "values": [85, 82, 79, 76, 83, 72, 71, 78],
    }


def _radar_data() -> Dict[str, Any]:
    categories = [
        "Curriculum", "Faculty", "Infrastructure",
        "Attainment", "Student Perf", "CI Process",
    ]
    return {
        "categories": categories,
        "series": [
            {"name": "Current Year",    "values": [82, 75, 68, 67, 79, 71],  "color": "#4589ff"},
            {"name": "Previous Year",   "values": [74, 70, 62, 63, 75, 65],  "color": "#be95ff"},
        ],
    }


# ─────────────────────────────────────────────────────────────
# System status panel
# ─────────────────────────────────────────────────────────────

def _render_system_status() -> None:
    wx_status     = st.session_state.get("wx_status", "online")
    vdb_status    = st.session_state.get("vector_db_status", "online")
    vdb_docs      = st.session_state.get("vector_doc_count", 1247)
    model         = st.session_state.get("selected_model", "ibm/granite-13b-chat-v2")

    def _dot(s: str) -> str:
        c = {"online": "#42be65", "offline": "#fa4d56", "warning": "#f1c21b"}.get(s, "#525252")
        shadow = f"box-shadow:0 0 6px {c};" if s == "online" else ""
        return (f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                f'background:{c};{shadow}margin-right:6px;"></span>')

    items = [
        ("Watsonx API",    wx_status,  model.split("/")[-1]),
        ("Vector DB",      vdb_status, f"{vdb_docs:,} docs"),
        ("LangGraph",      "online",   "Idle"),
        ("MongoDB",        "online",   "Connected"),
        ("Redis Cache",    "online",   "Connected"),
        ("PostgreSQL",     "online",   "Connected"),
    ]

    rows_html = "".join(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:0.375rem 0;border-bottom:1px solid var(--border-subtle);">
          <div style="font-size:0.8125rem;color:var(--text-secondary);">{_dot(stat)}{name}</div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:0.75rem;font-family:var(--font-mono);
                          color:var(--text-helper);">{detail}</span>
            <span class="badge badge-{'green' if stat=='online' else 'red' if stat=='offline' else 'yellow'}"
                  style="font-size:0.5625rem;padding:1px 5px;">
              {stat.upper()}
            </span>
          </div>
        </div>
        """
        for name, stat, detail in items
    )

    st.markdown(
        f"""
        <div class="glass-card" style="padding:1.25rem;">
          <div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;
                      text-transform:uppercase;color:var(--text-helper);margin-bottom:0.875rem;">
            System Status
          </div>
          {rows_html}
          <div style="font-size:0.6875rem;font-family:var(--font-mono);color:var(--text-disabled);
                      margin-top:8px;text-align:right;">
            Updated {datetime.now(timezone.utc).strftime("%H:%M:%S")} UTC
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Recent activity feed
# ─────────────────────────────────────────────────────────────

_ACTIVITY = [
    ("◆", "SAR Criteria 3 generated",        "2m ago",  "blue"),
    ("⬡", "CO-PO mapping updated for CSE",   "14m ago", "cyan"),
    ("◈", "Attainment computed – PO7 gap",   "31m ago", "yellow"),
    ("🔄", "CI Action AC-014 marked complete", "1h ago",  "green"),
    ("⬟", "12 PDFs indexed to knowledge base","2h ago",  "purple"),
    ("✓", "Validation passed – Criteria 5",   "3h ago",  "green"),
]


def _render_activity_feed() -> None:
    rows = "".join(
        f"""
        <div style="display:flex;align-items:flex-start;gap:10px;
                    padding:0.5rem 0;border-bottom:1px solid var(--border-subtle);">
          <div style="width:28px;height:28px;border-radius:6px;
                      background:rgba(255,255,255,0.05);display:flex;
                      align-items:center;justify-content:center;
                      font-size:0.875rem;flex-shrink:0;">{icon}</div>
          <div style="flex:1;min-width:0;">
            <div style="font-size:0.8125rem;color:var(--text-primary);
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              {label}
            </div>
            <div style="font-size:0.6875rem;color:var(--text-helper);
                        font-family:var(--font-mono);">{age}</div>
          </div>
        </div>
        """
        for icon, label, age, color in _ACTIVITY
    )
    st.markdown(
        f"""
        <div class="glass-card" style="padding:1.25rem;">
          <div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;
                      text-transform:uppercase;color:var(--text-helper);margin-bottom:0.875rem;">
            Recent Activity
          </div>
          {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Main render
# ─────────────────────────────────────────────────────────────

def render() -> None:
    sess = auth_service.get_session()
    username = sess.display_name if sess else "User"

    # ── Navbar ─────────────────────────────────────────────────
    render_navbar("Dashboard", notification_count=st.session_state.get("notification_count", 2))

    # ── Hero ───────────────────────────────────────────────────
    render_page_hero(
        title=f"Welcome back, {username.split()[0]}",
        subtitle=f"NBA Accreditation Platform  ·  {datetime.now(timezone.utc).strftime('%A, %d %B %Y')}",
        icon="⬛",
        accent_color="blue",
        actions_html=(
            '<div class="badge badge-green" style="font-size:0.75rem;padding:4px 10px;">'
            '● Platform Healthy</div>'
        ),
    )

    content = st.container()
    with content:
        st.markdown('<div class="page-content" style="padding:1.25rem 1.75rem;">', unsafe_allow_html=True)

        # ── KPI row ────────────────────────────────────────────
        loading = st.session_state.get("dashboard_loading", False)
        render_kpi_row(_kpi_data(), loading=loading)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Stat strip ─────────────────────────────────────────
        render_stat_row([
            {"label": "Total COs",      "value": 148,  "unit": "",  "color": "blue"},
            {"label": "Total POs",      "value": 12,   "unit": "",  "color": "cyan"},
            {"label": "Courses",        "value": 42,   "unit": "",  "color": "purple"},
            {"label": "Faculty",        "value": 28,   "unit": "",  "color": "green"},
            {"label": "Placement",      "value": 76.4, "unit": "%", "color": "yellow"},
            {"label": "Pass Rate",      "value": 84.1, "unit": "%", "color": "green"},
        ])

        # ── Main charts row ────────────────────────────────────
        col_main, col_side = st.columns([2.2, 1])

        with col_main:
            # Attainment bar
            po = _po_attainment()
            st.markdown(
                '<div class="chart-wrapper" style="margin-bottom:1rem;">',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="chart-title">PO Attainment Overview</div>'
                '<div class="chart-subtitle">Direct vs Indirect · Threshold 60%</div>',
                unsafe_allow_html=True,
            )
            render_attainment_bar(
                labels=po["labels"],
                direct_values=po["direct"],
                indirect_values=po["indirect"],
                threshold=60.0,
                title="",
                key="dash_attainment",
                height=340,
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # Trend line
            trend = _trend_data()
            st.markdown(
                '<div class="chart-wrapper">',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="chart-title">Readiness & Attainment Trend</div>'
                '<div class="chart-subtitle">Semester-wise progression</div>',
                unsafe_allow_html=True,
            )
            render_trend_line(
                x_values=trend["x"],
                series=trend["series"],
                title="",
                y_label="Score (%)",
                key="dash_trend",
                height=280,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            # Readiness gauge
            st.markdown('<div class="chart-wrapper" style="margin-bottom:1rem;text-align:center;">',
                        unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Accreditation Readiness</div>', unsafe_allow_html=True)
            render_gauge(74.2, title="Overall Score", threshold=70.0,
                         key="dash_gauge", height=230)
            st.markdown("</div>", unsafe_allow_html=True)

            # Risk badge
            st.markdown('<div style="margin-bottom:1rem;">',
                        unsafe_allow_html=True)
            render_risk_badge("medium", 44.0)
            st.markdown("</div>", unsafe_allow_html=True)

            # Compliance donut
            crit = _criteria_compliance()
            st.markdown('<div class="chart-wrapper" style="margin-bottom:1rem;">',
                        unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Criteria Compliance</div>', unsafe_allow_html=True)
            render_donut_chart(
                labels=crit["labels"],
                values=crit["values"],
                title="",
                key="dash_donut",
                height=260,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Bottom row ─────────────────────────────────────────
        col_radar, col_status, col_activity = st.columns([1.6, 1.2, 1.2])

        with col_radar:
            rad = _radar_data()
            st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Multi-Dimensional Performance Radar</div>',
                        unsafe_allow_html=True)
            render_radar_chart(
                categories=rad["categories"],
                series=rad["series"],
                title="",
                key="dash_radar",
                height=340,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col_status:
            _render_system_status()

            # PO progress bars below system status
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                '<div class="glass-card" style="padding:1.25rem;">',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
                'text-transform:uppercase;color:var(--text-helper);margin-bottom:0.875rem;">'
                'Top PO Attainment</div>',
                unsafe_allow_html=True,
            )
            po_data = _po_attainment()
            for lbl, val in zip(po_data["labels"][:6], po_data["direct"][:6]):
                color = "green" if val >= 60 else "red"
                render_labeled_progress(lbl, val, color=color)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_activity:
            _render_activity_feed()

        # ── Quick workflow preview ──────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⬢ LangGraph Workflow Preview", expanded=False):
            wf = get_nba_workflow()
            # Simulate partial execution for demo
            from components.workflow_visualizer import simulate_workflow_step, NodeStatus as NS
            wf = simulate_workflow_step(wf, "intent_classifier", NS.COMPLETED, 340, "Intent: CO-PO Mapping")
            wf = simulate_workflow_step(wf, "copo_agent", NS.COMPLETED, 1240, "Matrix generated")
            wf = simulate_workflow_step(wf, "validation_agent", NS.RUNNING)
            render_workflow_pipeline(wf, title="Sample Execution Trace")

        st.markdown("</div>", unsafe_allow_html=True)
