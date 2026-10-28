"""Plotly charts. Rendered with Streamlit's theme so they follow light/dark mode."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .baseline import Summary, end_use_costs
from .checks import STATUS_GOOD, STATUS_ICON, STATUS_IMPROVE, CheckResult
from .profile import HouseholdProfile
from .scenarios import Scenario

# Categorical slots in fixed order (validated for colour-vision deficiency).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
NEUTRAL = "#8a8983"
STATUS_COLOURS = {STATUS_GOOD: "#0ca30c", STATUS_IMPROVE: "#fab219", "Priority": "#d03b3b"}

SCENARIO_COLOURS = {
    "Current home": NEUTRAL,
    "Quick wins": SERIES[0],
    "Renter-friendly": SERIES[2],
    "Moderate upgrades": SERIES[1],
    "Deep retrofit": SERIES[6],
    "Custom": SERIES[3],
}


def _layout(fig: go.Figure, height: int, **kw) -> go.Figure:
    layout = dict(
        height=height,
        margin=dict(l=10, r=20, t=40, b=10),
        barcornerradius=4,
        hoverlabel=dict(namelength=-1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_layout(**{**layout, **kw})
    return fig


def end_use_chart(p: HouseholdProfile, s: Summary) -> go.Figure:
    costs = end_use_costs(p, s)
    rows = sorted(((k, e, g) for k, (e, g) in costs.items() if e + g > 0.5), key=lambda r: r[1] + r[2])
    names = [r[0] for r in rows]
    fig = go.Figure()
    fig.add_bar(y=names, x=[r[1] for r in rows], name="Electricity", orientation="h", marker_color=SERIES[0],
                hovertemplate="%{y}<br>Electricity: $%{x:,.0f}/yr<extra></extra>")
    if any(r[2] > 0 for r in rows):
        fig.add_bar(y=names, x=[r[2] for r in rows], name="Gas", orientation="h", marker_color=SERIES[1],
                    hovertemplate="%{y}<br>Gas: $%{x:,.0f}/yr<extra></extra>")
    fig.update_xaxes(title="Indicative usage cost ($/yr, excludes supply charges)", tickprefix="$", separatethousands=True)
    return _layout(fig, 380, barmode="stack", bargap=0.25, title="Where your money goes")


def checks_chart(checks: list[CheckResult]) -> go.Figure:
    rows = list(reversed(checks))
    fig = go.Figure(
        go.Bar(
            y=[c.name for c in rows],
            x=[c.score for c in rows],
            orientation="h",
            marker_color=[STATUS_COLOURS[c.status] for c in rows],
            text=[f"{STATUS_ICON[c.status]} {c.status} · {c.score}" for c in rows],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x}/100<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 125], title="Score (out of 100)", tickvals=[0, 25, 50, 75, 100])
    return _layout(fig, 340, bargap=0.3, showlegend=False, title="Your seven checks")


def scenario_chart(scenarios: list[Scenario]) -> go.Figure:
    metrics = [
        ("Annual energy bill ($)", lambda s: s.summary.total_cost, "${:,.0f}"),
        ("Energy use (kWh equiv.)", lambda s: s.summary.energy_kwh_equiv, "{:,.0f}"),
        ("Emissions (t CO₂-e)", lambda s: s.summary.co2_kg / 1000, "{:.1f}"),
    ]
    fig = make_subplots(rows=1, cols=3, subplot_titles=[m[0] for m in metrics], horizontal_spacing=0.08)
    for col, (title, fn, fmt) in enumerate(metrics, start=1):
        for sc in scenarios:
            val = fn(sc)
            fig.add_bar(
                x=[sc.name], y=[val], name=sc.name, legendgroup=sc.name, showlegend=col == 1,
                marker_color=SCENARIO_COLOURS.get(sc.name, NEUTRAL),
                text=[fmt.format(val)], textposition="outside", cliponaxis=False,
                hovertemplate=f"{sc.name}<br>{title}: {fmt.replace('{:', '%{y:')}<extra></extra>",
            )
        fig.update_xaxes(showticklabels=False, row=1, col=col)
        fig.update_yaxes(rangemode="tozero", row=1, col=col)
    return _layout(fig, 420, bargap=0.15, title=None, margin=dict(l=10, r=10, t=90, b=10))
