"""
components/charts.py
Production Plotly chart components styled with the IBM Watsonx dark theme.
All chart functions return Plotly figures and optionally call st.plotly_chart().
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

try:
    from assets.custom_css import get_plotly_theme
except ImportError:
    def get_plotly_theme() -> dict:  # type: ignore[misc]
        return {"template": "plotly_dark", "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)"}


# ─────────────────────────────────────────────────────────────
# Theme helpers
# ─────────────────────────────────────────────────────────────

_PALETTE = [
    "#4589ff", "#33b1ff", "#be95ff", "#42be65",
    "#f1c21b", "#ff832b", "#fa4d56", "#3ddbd9",
]


def _base_layout(**overrides: Any) -> Dict[str, Any]:
    base = get_plotly_theme()
    base.update(overrides)
    return base


def _apply_theme(fig: go.Figure, **layout_kwargs: Any) -> go.Figure:
    fig.update_layout(**_base_layout(**layout_kwargs))
    return fig


def _render(fig: go.Figure, key: str, height: int, use_container_width: bool) -> go.Figure:
    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        key=key,
        config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
            "displaylogo": False,
            "toImageButtonOptions": {"format": "png", "filename": key},
        },
    )
    return fig


# ─────────────────────────────────────────────────────────────
# Chart header helper
# ─────────────────────────────────────────────────────────────

def chart_header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="chart-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="chart-wrapper" style="padding-bottom:0;">'
        f'<div class="chart-title">{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# CO-PO Correlation Heatmap
# ─────────────────────────────────────────────────────────────

def render_copo_heatmap(
    correlation_matrix: List[List[float]],
    co_labels: List[str],
    po_labels: List[str],
    *,
    title: str = "CO-PO Correlation Matrix",
    key: str = "copo_heatmap",
    height: int = 400,
    show: bool = True,
) -> go.Figure:
    """
    Render a CO-PO correlation heatmap.

    Args:
        correlation_matrix: 2D list [CO][PO], values 0-3.
        co_labels: Course outcome labels (rows).
        po_labels: Program outcome labels (columns).
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix,
            x=po_labels,
            y=co_labels,
            colorscale=[
                [0.0,  "rgba(15,17,23,1)"],
                [0.33, "rgba(15,98,254,0.30)"],
                [0.67, "rgba(15,98,254,0.65)"],
                [1.0,  "rgba(15,98,254,1)"],
            ],
            zmin=0, zmax=3,
            text=[[str(int(v)) if v > 0 else "" for v in row] for row in correlation_matrix],
            texttemplate="%{text}",
            textfont={"size": 12, "color": "white", "family": "IBM Plex Mono"},
            showscale=True,
            colorbar=dict(
                title=dict(text="Level", font=dict(color="#8d8d8d", size=11)),
                tickvals=[0, 1, 2, 3],
                ticktext=["0 (None)", "1 (Low)", "2 (Med)", "3 (High)"],
                tickfont=dict(color="#8d8d8d", size=10),
                thickness=14,
                bgcolor="rgba(28,35,51,0.6)",
                bordercolor="rgba(255,255,255,0.08)",
            ),
            hovertemplate="<b>%{y}</b> → <b>%{x}</b><br>Correlation: <b>%{z}</b><extra></extra>",
        )
    )
    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        xaxis=dict(side="top", tickangle=0, **get_plotly_theme()["xaxis"]),
        yaxis=dict(**get_plotly_theme()["yaxis"]),
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Attainment bar chart
# ─────────────────────────────────────────────────────────────

def render_attainment_bar(
    labels: List[str],
    direct_values: List[float],
    indirect_values: Optional[List[float]] = None,
    threshold: float = 60.0,
    *,
    title: str = "Program Outcome Attainment",
    key: str = "attainment_bar",
    height: int = 380,
    show: bool = True,
) -> go.Figure:
    """Grouped bar chart for direct and indirect attainment by PO."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Direct",
        x=labels,
        y=direct_values,
        marker_color=[
            "#42be65" if v >= threshold else "#fa4d56"
            for v in direct_values
        ],
        marker_line_width=0,
        opacity=0.9,
        hovertemplate="<b>%{x}</b><br>Direct: <b>%{y:.1f}%</b><extra></extra>",
    ))

    if indirect_values:
        fig.add_trace(go.Bar(
            name="Indirect",
            x=labels,
            y=indirect_values,
            marker_color=[
                "rgba(66,190,101,0.4)" if v >= threshold else "rgba(250,77,86,0.4)"
                for v in indirect_values
            ],
            marker_line_width=0,
            opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Indirect: <b>%{y:.1f}%</b><extra></extra>",
        ))

    # Threshold line
    fig.add_hline(
        y=threshold,
        line_dash="dot",
        line_color="rgba(241,194,27,0.6)",
        line_width=1.5,
        annotation_text=f"Target {threshold}%",
        annotation_font=dict(color="#f1c21b", size=10),
        annotation_position="top right",
    )

    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
        yaxis=dict(range=[0, max(max(direct_values, default=0), threshold) * 1.15],
                   ticksuffix="%", **get_plotly_theme()["yaxis"]),
        legend=dict(**get_plotly_theme()["legend"]),
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Trend line chart
# ─────────────────────────────────────────────────────────────

def render_trend_line(
    x_values: List[Any],
    series: List[Dict[str, Any]],
    *,
    title: str = "Trend Analysis",
    y_label: str = "Value",
    key: str = "trend_line",
    height: int = 340,
    show: bool = True,
) -> go.Figure:
    """
    Multi-series trend line chart.

    series: [{"name": str, "values": List[float], "color": str (optional)}]
    """
    fig = go.Figure()
    for i, s in enumerate(series):
        color = s.get("color", _PALETTE[i % len(_PALETTE)])
        fig.add_trace(go.Scatter(
            name=s["name"],
            x=x_values,
            y=s["values"],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6, symbol="circle"),
            fill="tozeroy" if len(series) == 1 else "none",
            fillcolor=f"{color}18" if len(series) == 1 else None,
            hovertemplate=f"<b>{s['name']}</b><br>%{{x}}: <b>%{{y:.2f}}</b><extra></extra>",
        ))

    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        yaxis=dict(title=y_label, **get_plotly_theme()["yaxis"]),
        legend=dict(**get_plotly_theme()["legend"]),
        hovermode="x unified",
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Radar / Spider chart
# ─────────────────────────────────────────────────────────────

def render_radar_chart(
    categories: List[str],
    series: List[Dict[str, Any]],
    *,
    title: str = "Outcome Radar",
    key: str = "radar_chart",
    height: int = 380,
    show: bool = True,
) -> go.Figure:
    """
    Radar chart for multi-dimensional outcome analysis.

    series: [{"name": str, "values": List[float], "color": str}]
    """
    fig = go.Figure()
    for i, s in enumerate(series):
        color = s.get("color", _PALETTE[i % len(_PALETTE)])
        vals  = s["values"] + [s["values"][0]]  # close the polygon
        cats  = categories + [categories[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=cats,
            fill="toself",
            name=s["name"],
            line=dict(color=color, width=2),
            fillcolor=f"{color}20",
            hovertemplate="%{theta}: <b>%{r:.1f}%</b><extra></extra>",
        ))

    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                tickfont=dict(color="#525252", size=9),
                gridcolor="rgba(255,255,255,0.07)",
                linecolor="rgba(255,255,255,0.07)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#c6c6c6", size=11),
                gridcolor="rgba(255,255,255,0.07)",
                linecolor="rgba(255,255,255,0.10)",
            ),
        ),
        legend=dict(**get_plotly_theme()["legend"]),
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Pie / Donut chart
# ─────────────────────────────────────────────────────────────

def render_donut_chart(
    labels: List[str],
    values: List[float],
    *,
    title: str = "Distribution",
    hole: float = 0.55,
    key: str = "donut_chart",
    height: int = 320,
    show: bool = True,
) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker=dict(
            colors=_PALETTE[:len(labels)],
            line=dict(color="rgba(15,17,23,1)", width=2),
        ),
        textinfo="percent+label",
        textfont=dict(color="#f4f4f4", size=11, family="IBM Plex Sans"),
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
    ))
    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        showlegend=True,
        legend=dict(**get_plotly_theme()["legend"]),
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Scatter plot
# ─────────────────────────────────────────────────────────────

def render_scatter(
    x_values: List[float],
    y_values: List[float],
    labels: Optional[List[str]] = None,
    color_values: Optional[List[float]] = None,
    *,
    x_label: str = "X",
    y_label: str = "Y",
    title: str = "Scatter Analysis",
    key: str = "scatter_chart",
    height: int = 360,
    show: bool = True,
) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=x_values,
        y=y_values,
        mode="markers+text",
        text=labels or [],
        textposition="top center",
        textfont=dict(color="#8d8d8d", size=10),
        marker=dict(
            size=10,
            color=color_values or _PALETTE[0],
            colorscale=[[0,"#fa4d56"],[0.5,"#f1c21b"],[1,"#42be65"]]
            if color_values else None,
            showscale=bool(color_values),
            line=dict(width=1, color="rgba(255,255,255,0.2)"),
        ),
        hovertemplate="<b>%{text}</b><br>X=%{x:.2f}, Y=%{y:.2f}<extra></extra>",
    ))
    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        xaxis=dict(title=x_label, **get_plotly_theme()["xaxis"]),
        yaxis=dict(title=y_label, **get_plotly_theme()["yaxis"]),
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Horizontal bar (department benchmark)
# ─────────────────────────────────────────────────────────────

def render_benchmark_bars(
    departments: List[str],
    scores: List[float],
    highlight_dept: Optional[str] = None,
    threshold: float = 60.0,
    *,
    title: str = "Department Benchmark",
    key: str = "benchmark_bars",
    height: int = 300,
    show: bool = True,
) -> go.Figure:
    colors = [
        "#4589ff" if d == highlight_dept
        else "#42be65" if s >= threshold
        else "#fa4d56"
        for d, s in zip(departments, scores)
    ]
    fig = go.Figure(go.Bar(
        x=scores,
        y=departments,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{s:.1f}%" for s in scores],
        textposition="inside",
        textfont=dict(color="white", size=11, family="IBM Plex Mono"),
        hovertemplate="<b>%{y}</b>: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(
        x=threshold, line_dash="dot",
        line_color="rgba(241,194,27,0.6)", line_width=1.5,
    )
    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        xaxis=dict(range=[0, 105], ticksuffix="%", **get_plotly_theme()["xaxis"]),
        yaxis=dict(**get_plotly_theme()["yaxis"]),
        bargap=0.3,
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Waterfall / gap chart
# ─────────────────────────────────────────────────────────────

def render_gap_waterfall(
    stages: List[str],
    values: List[float],
    baseline: float = 0.0,
    *,
    title: str = "Gap Waterfall Analysis",
    key: str = "gap_waterfall",
    height: int = 360,
    show: bool = True,
) -> go.Figure:
    measure = ["relative"] * len(values)
    text    = [f"{v:+.1f}%" for v in values]
    colors  = ["#42be65" if v >= 0 else "#fa4d56" for v in values]

    fig = go.Figure(go.Waterfall(
        name="Gap",
        orientation="v",
        x=stages,
        y=values,
        measure=measure,
        text=text,
        textposition="outside",
        textfont=dict(color="#c6c6c6", size=11),
        decreasing=dict(marker_color="#fa4d56"),
        increasing=dict(marker_color="#42be65"),
        totals=dict(marker_color="#4589ff"),
        connector=dict(line=dict(color="rgba(255,255,255,0.15)", width=1, dash="dot")),
        base=baseline,
        hovertemplate="<b>%{x}</b>: %{y:+.1f}%<extra></extra>",
    ))
    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        yaxis=dict(ticksuffix="%", **get_plotly_theme()["yaxis"]),
    )
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Gauge chart
# ─────────────────────────────────────────────────────────────

def render_gauge(
    value: float,
    min_val: float = 0.0,
    max_val: float = 100.0,
    *,
    title: str = "Score",
    threshold: float = 60.0,
    key: str = "gauge_chart",
    height: int = 260,
    show: bool = True,
) -> go.Figure:
    pct   = (value - min_val) / (max_val - min_val)
    color = "#42be65" if pct >= 0.8 else "#f1c21b" if pct >= 0.6 else "#fa4d56"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title=dict(text=title, font=dict(color="#c6c6c6", size=13)),
        number=dict(font=dict(color=color, size=36, family="IBM Plex Mono"), suffix="%"),
        delta=dict(
            reference=threshold,
            increasing=dict(color="#42be65"),
            decreasing=dict(color="#fa4d56"),
        ),
        gauge=dict(
            axis=dict(
                range=[min_val, max_val],
                tickcolor="#525252",
                tickfont=dict(color="#525252", size=10),
                nticks=6,
            ),
            bar=dict(color=color, thickness=0.22),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[min_val, threshold * 0.6],     color="rgba(250,77,86,0.15)"),
                dict(range=[threshold * 0.6, threshold],   color="rgba(241,194,27,0.10)"),
                dict(range=[threshold, max_val],            color="rgba(66,190,101,0.10)"),
            ],
            threshold=dict(
                line=dict(color="rgba(241,194,27,0.6)", width=2),
                thickness=0.75,
                value=threshold,
            ),
        ),
    ))
    _apply_theme(fig, height=height)
    if show:
        _render(fig, key, height, True)
    return fig


# ─────────────────────────────────────────────────────────────
# Sankey diagram (CO → PO flow)
# ─────────────────────────────────────────────────────────────

def render_sankey_flow(
    source_labels: List[str],
    target_labels: List[str],
    sources: List[int],
    targets: List[int],
    values: List[float],
    *,
    title: str = "CO → PO Flow",
    key: str = "sankey_chart",
    height: int = 420,
    show: bool = True,
) -> go.Figure:
    all_labels = source_labels + target_labels
    palette = [
        "rgba(69,137,255,0.7)", "rgba(51,177,255,0.7)",
        "rgba(190,149,255,0.7)", "rgba(66,190,101,0.7)",
        "rgba(241,194,27,0.7)", "rgba(250,77,86,0.7)",
    ]
    node_colors = [palette[i % len(palette)] for i in range(len(all_labels))]
    link_colors = [palette[s % len(palette)].replace("0.7", "0.25") for s in sources]

    fig = go.Figure(go.Sankey(
        arrangement="freeform",
        node=dict(
            pad=18, thickness=18,
            line=dict(color="rgba(255,255,255,0.08)", width=0.5),
            label=all_labels,
            color=node_colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=sources,
            target=[t + len(source_labels) for t in targets],
            value=values,
            color=link_colors,
            hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>Strength: %{value}<extra></extra>",
        ),
    ))
    _apply_theme(
        fig,
        title=dict(text=title, font=dict(size=14, color="#f4f4f4"), x=0),
        height=height,
        font=dict(family="IBM Plex Sans", color="#c6c6c6", size=11),
    )
    if show:
        _render(fig, key, height, True)
    return fig
