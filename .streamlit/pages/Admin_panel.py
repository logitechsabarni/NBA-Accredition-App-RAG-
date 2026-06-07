"""
pages/Admin_Panel.py
NBA Enterprise AI Platform — Admin Panel
Enterprise user management, audit logs, system health, and usage analytics.
IBM Watsonx enterprise styling.
"""

from __future__ import annotations

import io
import random
import time
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Internal imports with graceful fallback
# ---------------------------------------------------------------------------
try:
    from components import navbar as _navbar_mod
    from components import metric_cards as _mc_mod
    from components import charts as _charts_mod
    from services import auth_service as _auth_svc

    _IMPORTS_OK = True
except ImportError:
    _IMPORTS_OK = False


# ---------------------------------------------------------------------------
# Global IBM Watsonx CSS (mirrors Workflow Monitor palette)
# ---------------------------------------------------------------------------

_ADMIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ibm-blue-70:  #0043ce;
    --ibm-blue-60:  #0f62fe;
    --ibm-blue-50:  #4589ff;
    --ibm-blue-40:  #78a9ff;
    --ibm-gray-100: #161616;
    --ibm-gray-90:  #262626;
    --ibm-gray-80:  #393939;
    --ibm-gray-70:  #525252;
    --ibm-gray-60:  #6f6f6f;
    --ibm-gray-30:  #c6c6c6;
    --ibm-gray-10:  #f4f4f4;
    --ibm-green-40: #42be65;
    --ibm-green-50: #24a148;
    --ibm-red-50:   #da1e28;
    --ibm-red-40:   #fa4d56;
    --ibm-yellow-30:#f1c21b;
    --ibm-purple-50:#8a3ffc;
    --ibm-teal-40:  #3ddbd9;
    --card-bg:      #1e1e1e;
    --card-border:  #333333;
    --surface:      #262626;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: var(--ibm-gray-100) !important;
    color: var(--ibm-gray-10) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

[data-testid="stSidebar"] {
    background: var(--ibm-gray-90) !important;
    border-right: 1px solid var(--card-border);
}
[data-testid="stSidebar"] * { color: var(--ibm-gray-10) !important; }

[data-testid="metric-container"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}
[data-testid="stMetricValue"] { color: var(--ibm-blue-40) !important; font-weight: 600; }
[data-testid="stMetricLabel"] { color: var(--ibm-gray-30) !important; font-size: 0.75rem; }

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--card-border);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--ibm-gray-30) !important;
    border-radius: 0 !important;
    font-size: 0.875rem !important;
    padding: 0.6rem 1.25rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--ibm-blue-40) !important;
    border-bottom: 2px solid var(--ibm-blue-60) !important;
    font-weight: 600 !important;
}

.stButton > button {
    background: var(--ibm-blue-60) !important;
    color: white !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.25rem !important;
    transition: background 0.15s;
}
.stButton > button:hover { background: var(--ibm-blue-70) !important; }

.stTextInput > div > div,
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 0 !important;
    color: var(--ibm-gray-10) !important;
}

hr { border-color: var(--card-border) !important; }

.ibm-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 1px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.pill-active    { background: #0e2a1a; color: var(--ibm-green-40); border: 1px solid var(--ibm-green-50); }
.pill-inactive  { background: var(--ibm-gray-80); color: var(--ibm-gray-30); border: 1px solid var(--card-border); }
.pill-suspended { background: #2a0a0b; color: var(--ibm-red-40); border: 1px solid var(--ibm-red-50); }
.pill-pending   { background: #2a2400; color: var(--ibm-yellow-30); border: 1px solid var(--ibm-yellow-30); }
.pill-admin     { background: #1a0a2a; color: #be95ff; border: 1px solid var(--ibm-purple-50); }
.pill-faculty   { background: #001a40; color: var(--ibm-blue-40); border: 1px solid var(--ibm-blue-60); }
.pill-hod       { background: #001e1e; color: var(--ibm-teal-40); border: 1px solid var(--ibm-teal-40); }
.pill-viewer    { background: var(--ibm-gray-80); color: var(--ibm-gray-30); border: 1px solid var(--card-border); }

.section-header {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ibm-gray-60);
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--card-border);
}

.page-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--ibm-gray-10);
    letter-spacing: -0.01em;
}
.page-subtitle { font-size: 0.8rem; color: var(--ibm-gray-60); margin-top: 0.15rem; }

/* Health status strip */
.health-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-left: 3px solid var(--ibm-green-40);
    padding: 0.85rem 1rem;
    border-radius: 1px;
    margin-bottom: 0.5rem;
}
.health-card.warning { border-left-color: var(--ibm-yellow-30); }
.health-card.error   { border-left-color: var(--ibm-red-50); }

/* Audit log row */
.audit-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--card-border);
    font-size: 0.78rem;
}
.audit-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }

/* Watsonx status card */
.watsonx-card {
    background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 100%);
    border: 1px solid #1e3a6e;
    border-radius: 2px;
    padding: 1.25rem;
}

/* Role badge grid */
.role-grid { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
</style>
"""

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------

_ROLES: list[dict[str, Any]] = [
    {
        "role": "admin",
        "label": "Administrator",
        "description": "Full platform access — user management, system config, audit logs",
        "permissions": [
            "user.create", "user.update", "user.delete", "user.view",
            "audit.view", "system.config", "analytics.view", "workflow.manage",
        ],
        "colour": "#8a3ffc",
    },
    {
        "role": "hod",
        "label": "Head of Department",
        "description": "Department-level access — course data, attainment, SAR generation",
        "permissions": [
            "course.create", "course.update", "attainment.view",
            "sar.generate", "analytics.view", "workflow.execute",
        ],
        "colour": "#3ddbd9",
    },
    {
        "role": "faculty",
        "label": "Faculty Member",
        "description": "Course-level access — CO entry, attainment upload, chat",
        "permissions": [
            "course.view", "co.entry", "attainment.upload", "chat.use",
        ],
        "colour": "#4589ff",
    },
    {
        "role": "viewer",
        "label": "Viewer",
        "description": "Read-only access — dashboards and analytics",
        "permissions": ["analytics.view", "dashboard.view"],
        "colour": "#6f6f6f",
    },
]

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict[str, Any] = {
        "ap_user_search":    "",
        "ap_user_filter":    "All",
        "ap_audit_filter":   "All",
        "ap_confirm_delete": None,
        "ap_active_section": "users",
        "ap_mock_tick":      0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _get_users() -> list[dict[str, Any]]:
    if _IMPORTS_OK:
        try:
            return _auth_svc.list_users()  # type: ignore[attr-defined]
        except Exception:
            pass

    roles   = ["admin", "hod", "faculty", "faculty", "faculty", "viewer"]
    statuses = ["active", "active", "active", "inactive", "suspended"]
    institutes = [
        "IIT Bombay", "NIT Trichy", "VIT Vellore", "BITS Pilani",
        "Anna University", "Jadavpur University", "RVCE Bangalore",
    ]
    users = []
    for i in range(1, 22):
        role = random.choice(roles)
        name = random.choice([
            "Arjun Sharma", "Priya Patel", "Ravi Kumar", "Sunita Reddy",
            "Anil Gupta", "Meena Nair", "Suresh Iyer", "Kavita Joshi",
            "Deepak Singh", "Lalitha Menon", "Vijay Rao", "Ananya Das",
        ])
        users.append({
            "id":           f"usr_{i:04d}",
            "name":         name,
            "email":        f"{name.lower().replace(' ', '.')}_{i}@{random.choice(['nba.edu', 'ac.in', 'edu.in'])}",
            "role":         role,
            "status":       random.choice(statuses),
            "institute":    random.choice(institutes),
            "last_login":   (datetime.now() - timedelta(minutes=random.randint(5, 10080))).strftime("%Y-%m-%d %H:%M"),
            "created_at":   (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d"),
            "workflows_run": random.randint(0, 320),
            "tokens_used":   random.randint(0, 48000),
            "mfa_enabled":   random.choice([True, True, False]),
        })
    return users


def _get_audit_logs(limit: int = 40) -> list[dict[str, Any]]:
    if _IMPORTS_OK:
        try:
            return _auth_svc.get_audit_logs(limit=limit)  # type: ignore[attr-defined]
        except Exception:
            pass

    actions = [
        ("user.login", "User authenticated via JWT", "info"),
        ("user.logout", "User session terminated", "info"),
        ("workflow.execute", "LangGraph workflow triggered", "info"),
        ("user.create", "New user account provisioned", "success"),
        ("user.update", "User role updated", "warning"),
        ("user.delete", "User account deleted", "danger"),
        ("config.change", "System configuration modified", "warning"),
        ("export.csv", "Data export initiated", "info"),
        ("auth.failed", "Authentication failure — invalid credentials", "danger"),
        ("rag.query", "RAG retrieval executed", "info"),
        ("watsonx.request", "Watsonx Granite API call", "info"),
        ("attainment.upload", "Attainment data file uploaded", "success"),
        ("sar.generate", "SAR document generation initiated", "success"),
        ("audit.view", "Audit log accessed", "info"),
    ]
    users = ["admin@nba.edu", "faculty@nit.ac.in", "hod@vit.edu", "dean@iit.ac.in", "viewer@bits.ac.in"]
    logs = []
    for i in range(limit):
        action, description, level = random.choice(actions)
        ts = datetime.now() - timedelta(minutes=i * random.randint(1, 25))
        logs.append({
            "id":          f"log_{9000 - i}",
            "timestamp":   ts.strftime("%Y-%m-%d %H:%M:%S"),
            "user":        random.choice(users),
            "action":      action,
            "description": description,
            "level":       level,
            "ip_address":  f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "resource":    f"/api/v1/{action.split('.')[0]}/{random.randint(1,100)}",
            "status_code": random.choice([200, 200, 200, 201, 403, 500]) if level == "danger" else 200,
        })
    return logs


def _get_system_health() -> list[dict[str, Any]]:
    if _IMPORTS_OK:
        try:
            return _auth_svc.get_system_health()  # type: ignore[attr-defined]
        except Exception:
            pass

    return [
        {
            "service":     "FastAPI Backend",
            "status":      "healthy",
            "latency_ms":  random.randint(12, 35),
            "uptime_pct":  99.97,
            "version":     "2.0.1",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "PostgreSQL",
            "status":      "healthy",
            "latency_ms":  random.randint(2, 8),
            "uptime_pct":  99.99,
            "version":     "15.4",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "MongoDB",
            "status":      "healthy",
            "latency_ms":  random.randint(3, 12),
            "uptime_pct":  99.95,
            "version":     "7.0.2",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "Redis Cache",
            "status":      "healthy",
            "latency_ms":  random.randint(1, 3),
            "uptime_pct":  100.0,
            "version":     "7.2",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "FAISS Vector DB",
            "status":      random.choice(["healthy", "healthy", "warning"]),
            "latency_ms":  random.randint(18, 80),
            "uptime_pct":  99.82,
            "version":     "1.7.4",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "LangGraph Orchestrator",
            "status":      "healthy",
            "latency_ms":  random.randint(5, 20),
            "uptime_pct":  99.90,
            "version":     "0.1.14",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "Watsonx.ai (Granite-13B)",
            "status":      random.choice(["healthy", "healthy", "warning"]),
            "latency_ms":  random.randint(400, 1800),
            "uptime_pct":  99.50,
            "version":     "granite-13b-instruct-v2",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
        {
            "service":     "OpenAI GPT-4o Router",
            "status":      "healthy",
            "latency_ms":  random.randint(600, 2200),
            "uptime_pct":  99.60,
            "version":     "gpt-4o-2024-05-13",
            "last_check":  datetime.now().strftime("%H:%M:%S"),
        },
    ]


def _get_usage_analytics() -> dict[str, Any]:
    if _IMPORTS_OK:
        try:
            return _auth_svc.get_usage_analytics()  # type: ignore[attr-defined]
        except Exception:
            pass

    today = datetime.now()
    daily = []
    for d in range(29, -1, -1):
        dt = today - timedelta(days=d)
        daily.append({
            "date":           dt.strftime("%b %d"),
            "queries":        random.randint(40, 280),
            "tokens":         random.randint(8000, 65000),
            "active_users":   random.randint(8, 45),
            "workflow_runs":  random.randint(20, 140),
        })

    return {
        "total_users":          21,
        "active_users_today":   random.randint(8, 18),
        "total_queries":        random.randint(12000, 15000),
        "total_tokens_used":    random.randint(2_000_000, 4_200_000),
        "total_workflow_runs":  random.randint(3000, 4500),
        "avg_session_min":      round(random.uniform(8.5, 22.0), 1),
        "daily_breakdown":      daily,
    }


# ---------------------------------------------------------------------------
# Sub-renders
# ---------------------------------------------------------------------------

def _render_top_kpis(users: list[dict[str, Any]], analytics: dict[str, Any]) -> None:
    cols = st.columns(6)
    active = sum(1 for u in users if u["status"] == "active")
    kpis = [
        ("Total Users",        str(len(users)),                     None),
        ("Active Users",       str(active),                         None),
        ("Active Today",       str(analytics["active_users_today"]), None),
        ("Total Queries",      f"{analytics['total_queries']:,}",    None),
        ("Tokens Consumed",    f"{analytics['total_tokens_used'] // 1000:,}K", None),
        ("Workflow Runs",      f"{analytics['total_workflow_runs']:,}", None),
    ]
    for col, (label, val, delta) in zip(cols, kpis):
        with col:
            st.metric(label, val, delta)


def _render_user_management(users: list[dict[str, Any]]) -> None:
    """User management tab content."""
    st.markdown("<div class='section-header'>User Management</div>", unsafe_allow_html=True)

    # Search + filter bar
    f1, f2, f3 = st.columns([3, 2, 1])
    with f1:
        search = st.text_input("Search users", placeholder="Name, email or institute…", key="ap_user_search_input")
    with f2:
        role_filter = st.selectbox("Filter by role", ["All", "admin", "hod", "faculty", "viewer"], key="ap_role_filter")
    with f3:
        status_filter = st.selectbox("Status", ["All", "active", "inactive", "suspended"], key="ap_status_filter")

    # Apply filters
    filtered = users
    if search:
        s = search.lower()
        filtered = [u for u in filtered if s in u["name"].lower() or s in u["email"].lower() or s in u["institute"].lower()]
    if role_filter != "All":
        filtered = [u for u in filtered if u["role"] == role_filter]
    if status_filter != "All":
        filtered = [u for u in filtered if u["status"] == status_filter]

    st.markdown(
        f"<div style='font-size:0.75rem; color:#6f6f6f; margin-bottom:0.75rem;'>"
        f"Showing {len(filtered)} of {len(users)} users</div>",
        unsafe_allow_html=True,
    )

    # Render user table header
    header = st.columns([2, 2.5, 1.2, 1.2, 1.5, 1.2, 0.8])
    for col, label in zip(header, ["Name", "Email / Institute", "Role", "Status", "Last Login", "Workflows", "MFA"]):
        with col:
            st.markdown(
                f"<div style='font-size:0.7rem; font-weight:700; letter-spacing:0.06em; "
                f"text-transform:uppercase; color:#6f6f6f;'>{label}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("<hr style='margin:0.3rem 0 0.5rem;'/>", unsafe_allow_html=True)

    for user in filtered:
        role_pill = f"pill-{user['role']}"
        status_pill = f"pill-{user['status']}"
        mfa_badge = (
            '<span style="color:#42be65; font-size:0.8rem;">✓</span>' if user["mfa_enabled"]
            else '<span style="color:#6f6f6f; font-size:0.8rem;">—</span>'
        )
        cols = st.columns([2, 2.5, 1.2, 1.2, 1.5, 1.2, 0.8])
        with cols[0]:
            st.markdown(
                f"<div style='font-size:0.82rem; font-weight:600; color:#f4f4f4;'>{user['name']}</div>"
                f"<div style='font-size:0.7rem; font-family:\"IBM Plex Mono\",monospace; color:#6f6f6f;'>{user['id']}</div>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(
                f"<div style='font-size:0.78rem; color:#c6c6c6;'>{user['email']}</div>"
                f"<div style='font-size:0.7rem; color:#6f6f6f;'>{user['institute']}</div>",
                unsafe_allow_html=True,
            )
        with cols[2]:
            st.markdown(f"<span class='ibm-pill {role_pill}'>{user['role']}</span>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<span class='ibm-pill {status_pill}'>{user['status']}</span>", unsafe_allow_html=True)
        with cols[4]:
            st.markdown(
                f"<div style='font-size:0.75rem; color:#6f6f6f; font-family:\"IBM Plex Mono\",monospace;'>{user['last_login']}</div>",
                unsafe_allow_html=True,
            )
        with cols[5]:
            st.markdown(
                f"<div style='font-size:0.78rem; color:#c6c6c6;'>{user['workflows_run']:,}</div>",
                unsafe_allow_html=True,
            )
        with cols[6]:
            st.markdown(mfa_badge, unsafe_allow_html=True)
        st.markdown("<hr style='margin:0.3rem 0;'/>", unsafe_allow_html=True)

    # Export
    import pandas as pd
    export_df = pd.DataFrame([
        {k: v for k, v in u.items() if k != "mfa_enabled"} for u in filtered
    ])
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Export Users CSV",
        data=csv_bytes,
        file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="ap_export_users",
    )


def _render_role_management() -> None:
    """Role management section."""
    st.markdown("<div class='section-header'>Role Definitions</div>", unsafe_allow_html=True)
    for role in _ROLES:
        pill_cls = f"pill-{role['role']}"
        perm_html = " ".join(
            f"<code style='background:#262626; border:1px solid #333; border-radius:1px; "
            f"padding:1px 6px; font-size:0.68rem; color:#c6c6c6;'>{p}</code>"
            for p in role["permissions"]
        )
        st.markdown(
            f"""<div style="background:var(--card-bg, #1e1e1e); border:1px solid #333;
                           border-left:3px solid {role['colour']}; padding:1rem; border-radius:1px; margin-bottom:0.6rem;">
                  <div style="display:flex; align-items:center; gap:10px; margin-bottom:0.4rem;">
                    <span class="ibm-pill {pill_cls}">{role['role']}</span>
                    <span style="font-size:0.85rem; font-weight:600; color:#f4f4f4;">{role['label']}</span>
                  </div>
                  <div style="font-size:0.75rem; color:#6f6f6f; margin-bottom:0.5rem;">{role['description']}</div>
                  <div class="role-grid">{perm_html}</div>
                </div>""",
            unsafe_allow_html=True,
        )


def _render_audit_logs(logs: list[dict[str, Any]], level_filter: str) -> None:
    """Audit log viewer."""
    st.markdown("<div class='section-header'>Audit Log Viewer</div>", unsafe_allow_html=True)

    f1, f2 = st.columns([3, 1])
    with f1:
        audit_search = st.text_input(
            "Search audit logs", placeholder="Action, user, resource…",
            key="ap_audit_search",
        )
    with f2:
        level_sel = st.selectbox(
            "Level", ["All", "info", "success", "warning", "danger"],
            key="ap_audit_level_sel",
        )

    filtered = logs
    if audit_search:
        s = audit_search.lower()
        filtered = [
            lg for lg in filtered
            if s in lg["action"].lower()
            or s in lg["user"].lower()
            or s in lg["description"].lower()
            or s in lg["resource"].lower()
        ]
    if level_sel != "All":
        filtered = [lg for lg in filtered if lg["level"] == level_sel]

    level_colours = {
        "info":    "#4589ff",
        "success": "#42be65",
        "warning": "#f1c21b",
        "danger":  "#fa4d56",
    }

    st.markdown(
        f"<div style='font-size:0.75rem; color:#6f6f6f; margin-bottom:0.5rem;'>"
        f"{len(filtered)} events shown</div>",
        unsafe_allow_html=True,
    )

    for log in filtered[:35]:
        colour = level_colours.get(log["level"], "#6f6f6f")
        code_colour = "#42be65" if log["status_code"] == 200 else "#fa4d56"
        st.markdown(
            f"""<div class="audit-row">
                  <div class="audit-dot" style="background:{colour};"></div>
                  <span style="color:#6f6f6f; font-family:'IBM Plex Mono',monospace; font-size:0.7rem; flex-shrink:0; width:140px;">{log['timestamp']}</span>
                  <span style="color:#c6c6c6; flex-shrink:0; width:160px; overflow:hidden; text-overflow:ellipsis;">{log['user']}</span>
                  <span style="color:#78a9ff; font-family:'IBM Plex Mono',monospace; flex-shrink:0; width:180px;">{log['action']}</span>
                  <span style="color:#6f6f6f; flex:1; overflow:hidden; text-overflow:ellipsis;">{log['description']}</span>
                  <span style="color:#6f6f6f; font-family:'IBM Plex Mono',monospace; font-size:0.7rem; flex-shrink:0; width:110px;">{log['ip_address']}</span>
                  <span style="color:{code_colour}; font-family:'IBM Plex Mono',monospace; font-size:0.7rem; flex-shrink:0; width:40px;">{log['status_code']}</span>
               </div>""",
            unsafe_allow_html=True,
        )

    import pandas as pd
    export_df = pd.DataFrame(filtered)
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Export Audit CSV",
        data=csv_bytes,
        file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="ap_export_audit",
    )


def _render_system_health(health: list[dict[str, Any]]) -> None:
    """System health dashboard."""
    st.markdown("<div class='section-header'>System Health Dashboard</div>", unsafe_allow_html=True)

    healthy = sum(1 for h in health if h["status"] == "healthy")
    warning = sum(1 for h in health if h["status"] == "warning")
    down    = sum(1 for h in health if h["status"] == "error")

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Services Total", len(health))
    with sc2:
        st.metric("Healthy", healthy)
    with sc3:
        st.metric("Warning", warning)
    with sc4:
        st.metric("Down", down)

    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    for svc in health:
        status  = svc["status"]
        colour  = {"healthy": "#42be65", "warning": "#f1c21b", "error": "#fa4d56"}.get(status, "#6f6f6f")
        card_cls = {"healthy": "", "warning": "warning", "error": "error"}.get(status, "")
        icon    = {"healthy": "●", "warning": "▲", "error": "✕"}.get(status, "●")

        st.markdown(
            f"""<div class="health-card {card_cls}">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:10px;">
                      <span style="color:{colour}; font-size:0.8rem;">{icon}</span>
                      <div>
                        <div style="font-size:0.82rem; font-weight:600; color:#f4f4f4;">{svc['service']}</div>
                        <div style="font-size:0.7rem; color:#6f6f6f; font-family:'IBM Plex Mono',monospace;">{svc['version']}</div>
                      </div>
                    </div>
                    <div style="display:flex; gap:2rem; font-size:0.75rem; text-align:right;">
                      <div>
                        <div style="color:#6f6f6f;">Latency</div>
                        <div style="color:#c6c6c6; font-family:'IBM Plex Mono',monospace;">{svc['latency_ms']} ms</div>
                      </div>
                      <div>
                        <div style="color:#6f6f6f;">Uptime</div>
                        <div style="color:#c6c6c6;">{svc['uptime_pct']}%</div>
                      </div>
                      <div>
                        <div style="color:#6f6f6f;">Last check</div>
                        <div style="color:#6f6f6f; font-family:'IBM Plex Mono',monospace;">{svc['last_check']}</div>
                      </div>
                    </div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )


def _render_watsonx_status_card(health: list[dict[str, Any]], analytics: dict[str, Any]) -> None:
    """Dedicated Watsonx status card."""
    wx_health = next((h for h in health if "Watsonx" in h["service"]), None)
    status_label = wx_health["status"].upper() if wx_health else "UNKNOWN"
    status_colour = {"HEALTHY": "#42be65", "WARNING": "#f1c21b", "ERROR": "#fa4d56"}.get(status_label, "#6f6f6f")
    latency = wx_health["latency_ms"] if wx_health else "—"
    uptime  = wx_health["uptime_pct"] if wx_health else "—"

    token_budget = 50_000
    tokens_used  = random.randint(18_000, 44_000)
    token_pct    = tokens_used / token_budget * 100

    st.markdown(
        f"""<div class="watsonx-card">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem;">
                <div>
                  <div style="font-size:0.7rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#78a9ff; margin-bottom:0.2rem;">
                    IBM Watsonx.ai
                  </div>
                  <div style="font-size:1rem; font-weight:700; color:#f4f4f4;">Granite-13B Instruct v2</div>
                  <div style="font-size:0.72rem; color:#525252; font-family:'IBM Plex Mono',monospace; margin-top:3px;">
                    granite-13b-instruct-v2 &nbsp;·&nbsp; us-south region
                  </div>
                </div>
                <span style="background:#0e2a1a; color:{status_colour}; border:1px solid {status_colour};
                             padding:3px 12px; font-size:0.7rem; font-weight:700; letter-spacing:0.06em;
                             border-radius:1px;">{status_label}</span>
              </div>
              <div style="display:flex; gap:2.5rem; margin-bottom:1rem; font-size:0.78rem;">
                <div><div style="color:#525252;">API Latency</div><div style="color:#78a9ff; font-family:'IBM Plex Mono',monospace;">{latency} ms</div></div>
                <div><div style="color:#525252;">Uptime (30d)</div><div style="color:#c6c6c6;">{uptime}%</div></div>
                <div><div style="color:#525252;">Tokens Used</div><div style="color:#c6c6c6; font-family:'IBM Plex Mono',monospace;">{tokens_used:,}</div></div>
                <div><div style="color:#525252;">Budget</div><div style="color:#c6c6c6; font-family:'IBM Plex Mono',monospace;">{token_budget:,}</div></div>
              </div>
              <div style="background:#0a1628; height:6px; border-radius:3px; overflow:hidden;">
                <div style="height:100%; width:{token_pct:.1f}%; background:{'#0f62fe' if token_pct < 80 else '#f1c21b' if token_pct < 90 else '#fa4d56'}; border-radius:3px; transition:width 0.4s;"></div>
              </div>
              <div style="display:flex; justify-content:space-between; font-size:0.68rem; color:#525252; margin-top:4px;">
                <span>Token budget utilisation: {token_pct:.1f}%</span>
                <span>{token_budget - tokens_used:,} remaining</span>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )


def _render_vector_db_status(health: list[dict[str, Any]]) -> None:
    """Vector database status card."""
    faiss_health = next((h for h in health if "FAISS" in h["service"]), None)
    status  = faiss_health["status"] if faiss_health else "unknown"
    colour  = {"healthy": "#42be65", "warning": "#f1c21b", "error": "#fa4d56"}.get(status, "#6f6f6f")
    latency = faiss_health["latency_ms"] if faiss_health else "—"

    total_docs = random.randint(45_000, 62_000)
    index_size = round(total_docs * 0.0024, 1)   # approximate MB

    st.markdown(
        f"""<div style="background:#1e1e1e; border:1px solid #333; border-left:3px solid {colour};
                       padding:1.1rem; border-radius:1px; margin-top:0.75rem;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div>
                  <div style="font-size:0.7rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#6f6f6f;">Vector Database</div>
                  <div style="font-size:0.95rem; font-weight:600; color:#f4f4f4;">FAISS + SentenceTransformers</div>
                </div>
                <span style="background:#0e2a1a; color:{colour}; border:1px solid {colour};
                             padding:2px 10px; font-size:0.7rem; font-weight:700; border-radius:1px; letter-spacing:0.05em;">
                  {status.upper()}</span>
              </div>
              <div style="display:flex; gap:2rem; font-size:0.78rem;">
                <div><div style="color:#6f6f6f;">Documents</div><div style="color:#c6c6c6; font-family:'IBM Plex Mono',monospace;">{total_docs:,}</div></div>
                <div><div style="color:#6f6f6f;">Index size</div><div style="color:#c6c6c6; font-family:'IBM Plex Mono',monospace;">{index_size} MB</div></div>
                <div><div style="color:#6f6f6f;">Query latency</div><div style="color:#c6c6c6; font-family:'IBM Plex Mono',monospace;">{latency} ms</div></div>
                <div><div style="color:#6f6f6f;">Embedding model</div><div style="color:#c6c6c6;">all-MiniLM-L6-v2</div></div>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )


def _render_usage_analytics(analytics: dict[str, Any]) -> None:
    """Usage analytics charts."""
    st.markdown("<div class='section-header'>Usage Analytics — Last 30 Days</div>", unsafe_allow_html=True)
    daily = analytics["daily_breakdown"]

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd

        df = pd.DataFrame(daily)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=["Daily Queries", "Token Consumption", "Active Users", "Workflow Runs"],
            vertical_spacing=0.14,
            horizontal_spacing=0.1,
        )

        colour_map = ["#4589ff", "#8a3ffc", "#42be65", "#3ddbd9"]
        metrics    = ["queries", "tokens", "active_users", "workflow_runs"]
        for idx, (metric, colour) in enumerate(zip(metrics, colour_map)):
            row = (idx // 2) + 1
            col = (idx % 2) + 1
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[metric],
                    mode="lines+markers",
                    line=dict(color=colour, width=2),
                    marker=dict(size=4, color=colour),
                    fill="tozeroy",
                    fillcolor=colour.replace(")", ", 0.08)").replace("rgb", "rgba") if colour.startswith("rgb") else colour + "15",
                    name=metric.replace("_", " ").title(),
                ),
                row=row, col=col,
            )

        fig.update_layout(
            paper_bgcolor="#161616",
            plot_bgcolor="#1e1e1e",
            font=dict(family="IBM Plex Sans", color="#c6c6c6", size=10),
            margin=dict(l=40, r=20, t=50, b=40),
            showlegend=False,
            height=400,
        )
        for ax in fig.layout:
            if ax.startswith("xaxis") or ax.startswith("yaxis"):
                fig.layout[ax].update(gridcolor="#333", linecolor="#333", showgrid=True)

        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        import pandas as pd
        df = pd.DataFrame(daily).set_index("date")
        st.line_chart(df[["queries", "active_users"]], height=200)

    # Summary row
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Queries (30d)", f"{sum(d['queries'] for d in daily):,}")
    with s2:
        st.metric("Total Tokens (30d)", f"{sum(d['tokens'] for d in daily) // 1000:,}K")
    with s3:
        st.metric("Peak Active Users", f"{max(d['active_users'] for d in daily)}")
    with s4:
        st.metric("Avg Workflows/Day", f"{sum(d['workflow_runs'] for d in daily) // len(daily)}")

    # Export
    import pandas as pd
    df_exp = pd.DataFrame(daily)
    csv_bytes = df_exp.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇  Export Usage CSV",
        data=csv_bytes,
        file_name=f"usage_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="ap_export_usage",
    )


def _render_activity_monitoring(logs: list[dict[str, Any]]) -> None:
    """Recent activity activity feed."""
    st.markdown("<div class='section-header'>Live Activity Feed</div>", unsafe_allow_html=True)

    level_colours = {
        "info":    "#4589ff",
        "success": "#42be65",
        "warning": "#f1c21b",
        "danger":  "#fa4d56",
    }
    for log in logs[:12]:
        colour = level_colours.get(log["level"], "#6f6f6f")
        st.markdown(
            f"""<div style="display:flex; gap:10px; align-items:flex-start; padding:0.45rem 0; border-bottom:1px solid #2a2a2a;">
                  <div style="width:8px; height:8px; border-radius:50%; background:{colour}; flex-shrink:0; margin-top:5px;"></div>
                  <div style="flex:1;">
                    <div style="font-size:0.78rem; color:#c6c6c6;">{log['description']}</div>
                    <div style="font-size:0.68rem; color:#525252; font-family:'IBM Plex Mono',monospace; margin-top:2px;">
                      {log['user']} &nbsp;·&nbsp; {log['timestamp']} &nbsp;·&nbsp; {log['action']}
                    </div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render() -> None:  # noqa: C901
    """
    Render the Admin Panel page.
    Called by the Streamlit multi-page router (app.py).
    """
    # ── Config ──────────────────────────────────────────────────────────────
    st.set_page_config(
        page_title="Admin Panel — NBA AI Platform",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_ADMIN_CSS, unsafe_allow_html=True)
    _init_state()

    # ── Navbar ───────────────────────────────────────────────────────────────
    if _IMPORTS_OK:
        try:
            _navbar_mod.render(active_page="Admin Panel")  # type: ignore[attr-defined]
        except Exception:
            pass

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='font-size:0.7rem; font-weight:700; letter-spacing:0.08em; "
            "text-transform:uppercase; color:#6f6f6f; padding:0.5rem 0 0.75rem;'>Admin Controls</div>",
            unsafe_allow_html=True,
        )

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state["ap_mock_tick"] = st.session_state.get("ap_mock_tick", 0) + 1
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.7rem; font-weight:700; letter-spacing:0.08em; "
            "text-transform:uppercase; color:#6f6f6f; margin-bottom:0.5rem;'>Danger Zone</div>",
            unsafe_allow_html=True,
        )
        st.button("🗑 Flush Redis Cache", use_container_width=True, disabled=True)
        st.button("📤 Backup Database", use_container_width=True, disabled=True)
        st.button("⏸ Maintenance Mode", use_container_width=True, disabled=True)

        st.markdown("---")
        st.markdown(
            f"""<div style='font-size:0.72rem; color:#6f6f6f; line-height:1.7;'>
              <strong style='color:#c6c6c6;'>Admin Session</strong><br/>
              admin@nba.edu<br/>
              Role: <span style='color:#be95ff;'>administrator</span><br/>
              Login: {datetime.now().strftime('%H:%M:%S')}
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Page header ─────────────────────────────────────────────────────────
    st.markdown(
        """<div class="page-title">🛡️ Admin Panel</div>
           <div class="page-subtitle">User management, system health, audit logs, and platform analytics</div>""",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='margin:0.6rem 0 1rem;'/>", unsafe_allow_html=True)

    # ── Fetch all data upfront ───────────────────────────────────────────────
    users     = _get_users()
    audit_logs = _get_audit_logs(limit=40)
    health    = _get_system_health()
    analytics = _get_usage_analytics()

    # ── Top KPI strip ────────────────────────────────────────────────────────
    _render_top_kpis(users, analytics)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ── Main tabs ────────────────────────────────────────────────────────────
    (
        tab_users,
        tab_roles,
        tab_audit,
        tab_health,
        tab_analytics,
        tab_activity,
    ) = st.tabs([
        "👥 Users",
        "🔑 Roles",
        "📋 Audit Logs",
        "💚 System Health",
        "📊 Usage Analytics",
        "⚡ Activity",
    ])

    # ── Tab: Users ────────────────────────────────────────────────────────────
    with tab_users:
        _render_user_management(users)

    # ── Tab: Roles ────────────────────────────────────────────────────────────
    with tab_roles:
        _render_role_management()

    # ── Tab: Audit Logs ───────────────────────────────────────────────────────
    with tab_audit:
        _render_audit_logs(audit_logs, st.session_state.get("ap_audit_filter", "All"))

    # ── Tab: System Health ────────────────────────────────────────────────────
    with tab_health:
        left, right = st.columns([3, 2])
        with left:
            _render_system_health(health)
        with right:
            _render_watsonx_status_card(health, analytics)
            _render_vector_db_status(health)

    # ── Tab: Usage Analytics ──────────────────────────────────────────────────
    with tab_analytics:
        _render_usage_analytics(analytics)

    # ── Tab: Activity ─────────────────────────────────────────────────────────
    with tab_activity:
        a1, a2 = st.columns([2, 1])
        with a1:
            _render_activity_monitoring(audit_logs)
        with a2:
            st.markdown("<div class='section-header'>Event Summary</div>", unsafe_allow_html=True)
            level_counts = {
                "info":    sum(1 for lg in audit_logs if lg["level"] == "info"),
                "success": sum(1 for lg in audit_logs if lg["level"] == "success"),
                "warning": sum(1 for lg in audit_logs if lg["level"] == "warning"),
                "danger":  sum(1 for lg in audit_logs if lg["level"] == "danger"),
            }
            level_colours = {"info": "#4589ff", "success": "#42be65", "warning": "#f1c21b", "danger": "#fa4d56"}

            try:
                import plotly.graph_objects as go

                fig = go.Figure(go.Pie(
                    labels=[k.title() for k in level_counts.keys()],
                    values=list(level_counts.values()),
                    hole=0.55,
                    marker=dict(colors=list(level_colours.values())),
                    textinfo="label+value",
                    textfont=dict(family="IBM Plex Sans", size=11, color="#f4f4f4"),
                ))
                fig.update_layout(
                    paper_bgcolor="#161616",
                    font=dict(family="IBM Plex Sans", color="#c6c6c6"),
                    showlegend=False,
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=220,
                    title=dict(text="Event Levels", font=dict(size=11, color="#f4f4f4")),
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                for level, count in level_counts.items():
                    colour = level_colours[level]
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;"
                        f"padding:0.3rem 0;border-bottom:1px solid #2a2a2a;'>"
                        f"<span style='color:{colour};'>{level.title()}</span>"
                        f"<span style='color:#c6c6c6;'>{count}</span></div>",
                        unsafe_allow_html=True,
                    )

            st.markdown("<div class='section-header'>Top Active Users</div>", unsafe_allow_html=True)
            from collections import Counter
            top_users = Counter(lg["user"] for lg in audit_logs).most_common(5)
            for usr, cnt in top_users:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;font-size:0.75rem;"
                    f"padding:0.3rem 0;border-bottom:1px solid #2a2a2a;'>"
                    f"<span style='color:#c6c6c6;'>{usr}</span>"
                    f"<span style='color:#4589ff;'>{cnt} events</span></div>",
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Standalone dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    render()
