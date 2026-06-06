"""
components/metric_cards.py
Animated KPI cards, agent cards, and summary stat widgets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import streamlit as st


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _delta_html(delta: Optional[Union[float, str]], unit: str = "") -> str:
    if delta is None:
        return ""
    if isinstance(delta, (int, float)):
        sign   = "+" if delta >= 0 else ""
        cls    = "positive" if delta >= 0 else "negative"
        arrow  = "↑" if delta >= 0 else "↓"
        return (
            f'<div class="kpi-delta {cls}">'
            f'{arrow} {sign}{delta:g}{unit} vs last period'
            f'</div>'
        )
    return f'<div class="kpi-delta neutral">{delta}</div>'


def _icon_bg(color: str) -> str:
    bg_map = {
        "blue":   "rgba(15,98,254,0.15)",
        "cyan":   "rgba(51,177,255,0.15)",
        "purple": "rgba(190,149,255,0.15)",
        "green":  "rgba(66,190,101,0.15)",
        "yellow": "rgba(241,194,27,0.15)",
        "red":    "rgba(250,77,86,0.15)",
        "orange": "rgba(255,131,43,0.15)",
    }
    return bg_map.get(color, "rgba(255,255,255,0.08)")


# ─────────────────────────────────────────────────────────────
# Single KPI card
# ─────────────────────────────────────────────────────────────

def render_kpi_card(
    label: str,
    value: Union[int, float, str],
    *,
    unit: str = "",
    delta: Optional[Union[float, str]] = None,
    delta_unit: str = "",
    icon: str = "◆",
    color: str = "blue",
    description: Optional[str] = None,
    loading: bool = False,
) -> None:
    """
    Render a single animated KPI card.

    Args:
        label: Card label (uppercase small caps).
        value: Primary metric value.
        unit: Unit appended to value (e.g. "%", "ms").
        delta: Change vs previous period (float) or custom string.
        delta_unit: Unit for delta (e.g. "%").
        icon: Emoji or symbol displayed top-right.
        color: Accent color key (blue|cyan|purple|green|yellow|red).
        description: Optional faint description below delta.
        loading: Show skeleton shimmer instead of value.
    """
    if loading:
        st.markdown('<div class="kpi-skeleton"></div>', unsafe_allow_html=True)
        return

    display_value = (
        f"{value:,.0f}" if isinstance(value, (int, float)) and unit != "%" and abs(value) >= 1000
        else f"{value:g}" if isinstance(value, (int, float))
        else str(value)
    )
    delta_html   = _delta_html(delta, delta_unit)
    icon_bg      = _icon_bg(color)
    desc_html    = (
        f'<div style="font-size:0.75rem;color:var(--text-disabled);margin-top:4px;">'
        f'{description}</div>'
        if description else ""
    )

    st.markdown(
        f"""
        <div class="kpi-card {color}">
          <div class="kpi-icon" style="background:{icon_bg};">{icon}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{display_value}<span style="font-size:1.1rem;
            color:var(--text-secondary);font-weight:400;margin-left:3px;">{unit}</span>
          </div>
          {delta_html}
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Grid of KPI cards
# ─────────────────────────────────────────────────────────────

def render_kpi_row(cards: List[Dict[str, Any]], loading: bool = False) -> None:
    """
    Render a responsive grid of KPI cards.

    Each dict in `cards` accepts the same kwargs as render_kpi_card().
    """
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            render_kpi_card(**card, loading=loading)


# ─────────────────────────────────────────────────────────────
# Compact stat row
# ─────────────────────────────────────────────────────────────

def render_stat_row(stats: List[Dict[str, Any]]) -> None:
    """
    Render a single-line compact statistics row.

    Each stat dict: {"label": str, "value": str|int|float,
                     "unit": str, "color": str (CSS var suffix)}
    """
    parts: List[str] = []
    for s in stats:
        color_map = {
            "blue":   "var(--wx-blue-light)",
            "green":  "var(--wx-green)",
            "red":    "var(--wx-red)",
            "yellow": "var(--wx-yellow)",
            "purple": "var(--wx-purple)",
            "cyan":   "var(--wx-cyan)",
        }
        c = color_map.get(s.get("color", "blue"), "var(--wx-blue-light)")
        v = s.get("value", "—")
        u = s.get("unit", "")
        display = f"{v:,}" if isinstance(v, int) and v > 999 else str(v)
        parts.append(
            f"""
            <div style="display:flex;flex-direction:column;align-items:center;
                        padding:0 1.25rem;border-right:1px solid var(--border-subtle);">
              <div style="font-size:0.625rem;letter-spacing:0.1em;text-transform:uppercase;
                          color:var(--text-helper);margin-bottom:2px;">{s['label']}</div>
              <div style="font-size:1.1rem;font-weight:600;color:{c};
                          font-variant-numeric:tabular-nums;">{display}{u}</div>
            </div>
            """
        )
    # Remove last border
    if parts:
        parts[-1] = parts[-1].replace("border-right:1px solid var(--border-subtle);", "border-right:none;")

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:center;
                    background:var(--glass-bg);backdrop-filter:var(--glass-blur);
                    border:1px solid var(--glass-border);border-radius:var(--radius-lg);
                    padding:0.875rem 0.5rem;margin-bottom:1rem;">
          {"".join(parts)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Agent card
# ─────────────────────────────────────────────────────────────

def render_agent_card(
    name: str,
    agent_id: str,
    description: str,
    capabilities: List[str],
    *,
    icon: str = "◆",
    status: str = "online",
    color: str = "blue",
    last_run: Optional[str] = None,
    run_count: int = 0,
    avg_latency_ms: Optional[int] = None,
    on_click_label: str = "Run Agent",
) -> bool:
    """
    Render an agent information card.

    Returns True if the action button was clicked.
    """
    status_dot_class = {
        "online":  "online",
        "offline": "offline",
        "running": "warning",
        "idle":    "idle",
    }.get(status, "idle")

    cap_tags = "".join(
        f'<span class="badge badge-blue" style="font-size:0.6rem;padding:1px 6px;">'
        f'{cap}</span>'
        for cap in capabilities[:6]
    )

    stats_html = ""
    if last_run or run_count or avg_latency_ms:
        lr   = last_run or "—"
        rc   = f"{run_count:,}"
        lat  = f"{avg_latency_ms}ms" if avg_latency_ms else "—"
        stats_html = f"""
        <div style="display:flex;gap:16px;margin-top:0.75rem;
                    padding-top:0.75rem;border-top:1px solid var(--border-subtle);">
          <div style="font-size:0.75rem;color:var(--text-helper);">
            <div style="color:var(--text-disabled);font-size:0.625rem;
                        text-transform:uppercase;letter-spacing:0.08em;">Last Run</div>
            <div style="font-family:var(--font-mono);color:var(--text-secondary);">{lr}</div>
          </div>
          <div style="font-size:0.75rem;color:var(--text-helper);">
            <div style="color:var(--text-disabled);font-size:0.625rem;
                        text-transform:uppercase;letter-spacing:0.08em;">Executions</div>
            <div style="font-family:var(--font-mono);color:var(--text-secondary);">{rc}</div>
          </div>
          <div style="font-size:0.75rem;color:var(--text-helper);">
            <div style="color:var(--text-disabled);font-size:0.625rem;
                        text-transform:uppercase;letter-spacing:0.08em;">Avg Latency</div>
            <div style="font-family:var(--font-mono);color:var(--text-secondary);">{lat}</div>
          </div>
        </div>
        """

    icon_bg = _icon_bg(color)
    st.markdown(
        f"""
        <div class="agent-card">
          <div class="agent-card-header">
            <div class="agent-avatar" style="background:{icon_bg};">{icon}</div>
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:8px;">
                <div class="agent-name">{name}</div>
                <div class="status-indicator">
                  <span class="status-dot {status_dot_class}"></span>
                </div>
              </div>
              <div class="agent-id">{agent_id}</div>
            </div>
          </div>
          <div class="agent-description">{description}</div>
          <div class="agent-capabilities">{cap_tags}</div>
          {stats_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.button(on_click_label, key=f"agent_btn_{agent_id}", use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Compliance score ring
# ─────────────────────────────────────────────────────────────

def render_compliance_ring(
    score: float,
    label: str = "Compliance Score",
    size: int = 120,
) -> None:
    """
    Render an SVG ring/donut chart for a compliance percentage.
    """
    pct = max(0.0, min(100.0, score))
    r   = 44
    circ = 2 * 3.14159 * r
    dash_fill = circ * pct / 100
    dash_gap  = circ - dash_fill

    color = (
        "#42be65" if pct >= 80
        else "#f1c21b" if pct >= 60
        else "#fa4d56"
    )
    label_color = color

    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    gap:4px;padding:1rem;">
          <svg width="{size}" height="{size}" viewBox="0 0 100 100"
               style="transform:rotate(-90deg);">
            <circle cx="50" cy="50" r="{r}" fill="none"
                    stroke="rgba(255,255,255,0.08)" stroke-width="8"/>
            <circle cx="50" cy="50" r="{r}" fill="none"
                    stroke="{color}" stroke-width="8"
                    stroke-linecap="round"
                    stroke-dasharray="{dash_fill:.2f} {dash_gap:.2f}"
                    style="transition:stroke-dasharray 1s ease;
                           filter:drop-shadow(0 0 4px {color}88);"/>
          </svg>
          <div style="margin-top:-{size//2 + 16}px;text-align:center;
                      font-size:1.375rem;font-weight:700;color:{label_color};
                      font-variant-numeric:tabular-nums;">{pct:.0f}%</div>
          <div style="font-size:0.75rem;color:var(--text-helper);
                      text-align:center;margin-top:{size//2 - 8}px;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Progress bar with label
# ─────────────────────────────────────────────────────────────

def render_labeled_progress(
    label: str,
    value: float,
    max_value: float = 100.0,
    *,
    color: str = "blue",
    show_value: bool = True,
    unit: str = "%",
) -> None:
    """Render a labeled horizontal progress bar."""
    pct = (value / max_value * 100) if max_value else 0
    pct = max(0.0, min(100.0, pct))
    color_map = {
        "blue":   "var(--wx-blue)",
        "green":  "var(--wx-green)",
        "red":    "var(--wx-red)",
        "yellow": "var(--wx-yellow)",
        "purple": "var(--wx-purple)",
        "cyan":   "var(--wx-cyan)",
    }
    bar_color = color_map.get(color, "var(--wx-blue)")
    value_str = f"{value:.1f}{unit}" if show_value else ""
    display_v  = f"{value:g}" if unit == "%" else f"{value:g}"

    st.markdown(
        f"""
        <div style="margin-bottom:0.625rem;">
          <div style="display:flex;justify-content:space-between;
                      align-items:center;margin-bottom:4px;">
            <span style="font-size:0.8125rem;color:var(--text-secondary);">{label}</span>
            <span style="font-size:0.8125rem;font-family:var(--font-mono);
                         color:var(--text-primary);font-weight:500;">{display_v}{unit}</span>
          </div>
          <div style="height:6px;background:rgba(255,255,255,0.06);
                      border-radius:99px;overflow:hidden;">
            <div style="height:100%;width:{pct:.1f}%;background:{bar_color};
                        border-radius:99px;
                        box-shadow:0 0 8px {bar_color}66;
                        transition:width 0.8s cubic-bezier(0.34,1.56,0.64,1);"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Risk score card
# ─────────────────────────────────────────────────────────────

def render_risk_badge(risk_level: str, score: float) -> None:
    """Render an accreditation risk badge."""
    cfg = {
        "low":      ("#42be65", "LOW RISK",      "rgba(66,190,101,0.10)"),
        "medium":   ("#f1c21b", "MEDIUM RISK",   "rgba(241,194,27,0.10)"),
        "high":     ("#ff832b", "HIGH RISK",     "rgba(255,131,43,0.10)"),
        "critical": ("#fa4d56", "CRITICAL RISK", "rgba(250,77,86,0.10)"),
    }.get(risk_level.lower(), ("#8d8d8d", "UNKNOWN", "rgba(141,141,141,0.10)"))
    color, label, bg = cfg

    st.markdown(
        f"""
        <div style="display:inline-flex;align-items:center;gap:10px;
                    padding:0.5rem 1rem;border-radius:8px;
                    background:{bg};border:1px solid {color}44;">
          <div style="font-size:1.25rem;font-weight:700;color:{color};
                      font-variant-numeric:tabular-nums;">{score:.0f}</div>
          <div>
            <div style="font-size:0.5rem;font-weight:700;letter-spacing:0.12em;
                        text-transform:uppercase;color:{color};">{label}</div>
            <div style="font-size:0.6875rem;color:var(--text-helper);">
              Accreditation Risk Score
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
