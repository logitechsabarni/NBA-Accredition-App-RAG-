import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional

# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#4facfe",
    "secondary": "#00f2fe",
    "accent": "#a78bfa",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "surface": "rgba(255,255,255,0.05)",
    "border": "rgba(99,179,237,0.15)",
}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a0b4c8", family="Inter, sans-serif", size=12),
    margin=dict(t=40, b=40, l=40, r=20),
    xaxis=dict(gridcolor="rgba(99,179,237,0.08)", linecolor="rgba(99,179,237,0.15)"),
    yaxis=dict(gridcolor="rgba(99,179,237,0.08)", linecolor="rgba(99,179,237,0.15)"),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(99,179,237,0.15)",
        font=dict(color="#a0b4c8"),
    ),
)


def readiness_gauge(score: float, title: str = "Accreditation Readiness") -> go.Figure:
    """Create a gauge chart for readiness score."""
    color = "#ef4444"
    if score >= 80:
        color = "#22c55e"
    elif score >= 70:
        color = "#84cc16"
    elif score >= 60:
        color = "#f59e0b"
    elif score >= 50:
        color = "#f97316"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": title, "font": {"color": "#e8f0fe", "size": 14}},
        delta={"reference": 60, "increasing": {"color": "#22c55e"}, "decreasing": {"color": "#ef4444"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#7a9bb5", "tickfont": {"color": "#7a9bb5"}},
            "bar": {"color": color},
            "bgcolor": "rgba(255,255,255,0.04)",
            "borderwidth": 1,
            "bordercolor": "rgba(99,179,237,0.2)",
            "steps": [
                {"range": [0, 50], "color": "rgba(239,68,68,0.1)"},
                {"range": [50, 60], "color": "rgba(249,115,22,0.1)"},
                {"range": [60, 70], "color": "rgba(245,158,11,0.1)"},
                {"range": [70, 80], "color": "rgba(132,204,22,0.1)"},
                {"range": [80, 100], "color": "rgba(34,197,94,0.1)"},
            ],
            "threshold": {
                "line": {"color": "#4facfe", "width": 3},
                "thickness": 0.75,
                "value": 60,
            },
        },
        number={"suffix": "%", "font": {"color": color, "size": 36}},
    ))
    fig.update_layout(**CHART_LAYOUT, height=280)
    return fig


def co_attainment_bar(co_data: Dict[str, Dict], target: float = 60.0) -> go.Figure:
    """Bar chart for CO attainment."""
    cos = list(co_data.keys())
    attainments = [co_data[c]["attainment"] for c in cos]
    colors_list = [COLORS["success"] if v >= target else COLORS["danger"] for v in attainments]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cos,
        y=attainments,
        marker_color=colors_list,
        marker_line=dict(color="rgba(0,0,0,0.3)", width=1),
        name="CO Attainment",
        hovertemplate="<b>%{x}</b><br>Attainment: %{y:.1f}%<extra></extra>",
        text=[f"{v:.1f}%" for v in attainments],
        textposition="outside",
        textfont=dict(color="#e0e6f0", size=11),
    ))
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="#f59e0b",
        line_width=2,
        annotation_text=f"Target ({target}%)",
        annotation_font_color="#f59e0b",
    )
    fig.update_layout(
        **CHART_LAYOUT,
        title="CO Attainment Analysis",
        xaxis_title="Course Outcomes",
        yaxis_title="Attainment (%)",
        yaxis_range=[0, 110],
        height=360,
        showlegend=False,
    )
    return fig


def po_attainment_bar(po_data: Dict[str, Dict], target: float = 60.0) -> go.Figure:
    """Bar chart for PO attainment."""
    pos = list(po_data.keys())
    attainments = [po_data[p]["attainment"] for p in pos]
    colors_list = [COLORS["primary"] if v >= target else COLORS["warning"] for v in attainments]

    fig = go.Figure(go.Bar(
        x=pos,
        y=attainments,
        marker_color=colors_list,
        name="PO Attainment",
        hovertemplate="<b>%{x}</b><br>Attainment: %{y:.1f}%<extra></extra>",
        text=[f"{v:.1f}%" for v in attainments],
        textposition="outside",
        textfont=dict(color="#e0e6f0", size=11),
    ))
    fig.add_hline(y=target, line_dash="dash", line_color="#f59e0b", line_width=2,
                  annotation_text=f"Target ({target}%)", annotation_font_color="#f59e0b")
    fig.update_layout(
        **CHART_LAYOUT,
        title="PO Attainment Analysis",
        xaxis_title="Program Outcomes",
        yaxis_title="Attainment (%)",
        yaxis_range=[0, 110],
        height=360,
    )
    return fig


def copo_heatmap(matrix_df: "pd.DataFrame") -> go.Figure:
    """Heatmap for CO-PO mapping matrix."""
    fig = go.Figure(go.Heatmap(
        z=matrix_df.values,
        x=list(matrix_df.columns),
        y=list(matrix_df.index),
        colorscale=[
            [0.0, "rgba(255,255,255,0.04)"],
            [0.33, "rgba(79,172,254,0.25)"],
            [0.67, "rgba(79,172,254,0.55)"],
            [1.0, "rgba(79,172,254,0.9)"],
        ],
        zmin=0, zmax=3,
        text=matrix_df.values,
        texttemplate="%{text}",
        textfont=dict(color="#e0e6f0", size=13, family="Inter"),
        hovertemplate="<b>%{y} → %{x}</b><br>Strength: %{z}<extra></extra>",
        showscale=True,
        colorbar=dict(
            tickvals=[0, 1, 2, 3],
            ticktext=["None", "Low", "Medium", "High"],
            tickfont=dict(color="#a0b4c8"),
            outlinecolor="rgba(99,179,237,0.2)",
            outlinewidth=1,
        ),
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title="CO-PO Mapping Matrix",
        height=max(350, len(matrix_df.index) * 50 + 100),
        xaxis=dict(side="top"),
    )
    return fig


def readiness_trend(months: int = 12) -> go.Figure:
    """Synthetic readiness trend line chart."""
    import random
    random.seed(42)
    base = 55
    vals = []
    for i in range(months):
        base = min(base + random.uniform(-1, 3.5), 95)
        vals.append(round(base, 1))

    month_labels = pd.date_range(end=pd.Timestamp.now(), periods=months, freq="ME")
    month_labels = [m.strftime("%b %y") for m in month_labels]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=vals,
        mode="lines+markers",
        line=dict(color=COLORS["primary"], width=3),
        marker=dict(color=COLORS["primary"], size=8, line=dict(color="#0a0e1a", width=2)),
        fill="tozeroy",
        fillcolor="rgba(79,172,254,0.07)",
        name="Readiness Score",
        hovertemplate="<b>%{x}</b><br>Score: %{y}%<extra></extra>",
    ))
    fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b", line_width=1.5,
                  annotation_text="NBA Target", annotation_font_color="#f59e0b")
    fig.update_layout(
        **CHART_LAYOUT,
        title="Accreditation Readiness Trend",
        yaxis_range=[40, 100],
        height=300,
    )
    return fig


def department_comparison(benchmarks: Dict[str, float]) -> go.Figure:
    """Horizontal bar chart comparing departments."""
    depts = list(benchmarks.keys())
    scores = list(benchmarks.values())
    colors_list = [COLORS["success"] if s >= 60 else COLORS["warning"] for s in scores]

    fig = go.Figure(go.Bar(
        x=scores,
        y=depts,
        orientation="h",
        marker_color=colors_list,
        text=[f"{s}%" for s in scores],
        textposition="outside",
        textfont=dict(color="#e0e6f0"),
        hovertemplate="<b>%{y}</b><br>Readiness: %{x}%<extra></extra>",
    ))
    fig.add_vline(x=60, line_dash="dash", line_color="#f59e0b",
                  annotation_text="NBA Threshold", annotation_font_color="#f59e0b")
    fig.update_layout(
        **CHART_LAYOUT,
        title="Department Readiness Comparison",
        xaxis_range=[0, 105],
        height=350,
    )
    return fig


def sar_progress_donut(sections: List[Dict], completion: Dict[str, float]) -> go.Figure:
    """Donut chart for SAR section completion."""
    labels = [s["title"] for s in sections]
    vals = [completion.get(s["id"], 0) for s in sections]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=[max(v, 2) for v in vals],  # Ensure visibility
        hole=0.6,
        marker=dict(
            colors=px.colors.sequential.Blues_r[:len(labels)],
            line=dict(color="#0a0e1a", width=2),
        ),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Completion: %{value:.0f}%<extra></extra>",
    ))

    overall = sum(vals) / len(vals) if vals else 0
    fig.add_annotation(
        text=f"{overall:.0f}%",
        x=0.5, y=0.5,
        font=dict(size=28, color="#4facfe", family="Inter"),
        showarrow=False,
    )
    fig.add_annotation(
        text="Complete",
        x=0.5, y=0.38,
        font=dict(size=11, color="#7a9bb5"),
        showarrow=False,
    )
    fig.update_layout(**CHART_LAYOUT, title="SAR Completion Status", height=360, showlegend=False)
    return fig
