"""Chapter 1 - Context: urbanization is blamed for emissions, but wealth is the real driver."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ._theme import ACCENT, WARM, MUTED, _apply_theme


def build_urban_by_income(df) -> go.Figure:
    """Changes in urbanization percentage and average CO₂ emissions by income group"""
    order = ["Low income", "Lower middle income", "Upper middle income", "High income"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
                    x=df["income_group"],
                    y=df["avg_co2_per_capita"],
                    marker_color=ACCENT,
                    customdata=df[["countries"]],
                    hovertemplate=("<b>%{x}</b><br>Countries: %{customdata[0]}<br>Average CO₂: %{y:.1f}t/cap"
                    "<extra></extra>"),
                    showlegend=False,
                ), secondary_y=False)
    fig.add_trace(go.Scatter(
                    x=df["income_group"],
                    y=df["avg_urban_pct"],
                    mode="lines+markers",
                    line=dict(color=WARM, width=3),
                    marker=dict(color=WARM, size=15),
                    customdata=df[["countries"]],
                    hovertemplate=( "<b>%{x}</b><br>Countries: %{customdata[0]}<br>"
                                    "Average urbanization: %{y:.0f}%"
                                    "<extra></extra>"
                    ),
                    showlegend=False,
                ), secondary_y=True)
    fig.update_xaxes(categoryorder="array", categoryarray=order, showgrid=False)
    fig = _apply_theme(
        fig,
        height=560,
        bargap=0.38,
        xaxis_title=None,
        yaxis_title="Average CO₂/capita (tonnes)",
    )
    fig.update_yaxes(rangemode="tozero", color='#26231D', secondary_y=False)
    fig.update_yaxes(title_text="Average urban population (%)", secondary_y=True)
    return fig


_INCOME_COLORS = {
    "High income":          "#14532d",
    "Upper middle income":  "#7fae5a",
    "Lower middle income":  "#d59a4a",
    "Low income":           "#c2603f",
}
def build_density_vs_emissions(df) -> go.Figure:
    """Population density and territorial CO₂ per capita"""
    df["color"] = df["income_group"].map(_INCOME_COLORS)
    fig = go.Figure(
        go.Scatter(
            x=df["population_density"],
            y=df["co2_per_capita"],
            mode="markers+text",
            showlegend=False,
            marker=dict(color=df["color"], size=15, line=dict(width=1, color="#ffffff")),
            customdata=df[["country"]],
            hovertemplate=(
                "<b> %{customdata[0]}</b><br>"
                " CO₂: %{y:.2f}t/cap<br>"
                " Population density: %{x:.2f} people/km²<extra></extra>"
            ),
        )
    )
    fig = _apply_theme(
        fig,
        height=620,
        xaxis_title="Population density (people/km², log scale)",
        yaxis_title="CO₂ per capita (tonnes)",
    )
    fig.update_xaxes(type="log")
    return fig


def build_urban_vs_air_pollution(df) -> go.Figure:
    """Urban % vs PM2.5: the correlation is noisy worldwide, but clearly negative within Europe (highlighted, r ≈ -0.51)."""
    HOVER = ("<b>%{customdata[0]}</b><br> Urban population: %{x:.0f}%<br>"
             " PM2.5 exposure: %{y:.1f}µg/m³<extra></extra>")
    eu = df[df["is_europe"]].dropna(subset=["urban_population_pct", "pm25_exposure"])
    row = df[~df["is_europe"]]

    slope, intercept = np.polyfit(eu["urban_population_pct"], eu["pm25_exposure"], 1)
    xs = np.array([eu["urban_population_pct"].min(), eu["urban_population_pct"].max()])
    r = eu["urban_population_pct"].corr(eu["pm25_exposure"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=row["urban_population_pct"],
        y=row["pm25_exposure"],
        mode="markers",
        name="Rest of world",
        marker=dict(size=9, color=MUTED, opacity=0.35),
        customdata=row[["country"]],
        hovertemplate=HOVER,
    ))
    fig.add_trace(go.Scatter(
        x=xs,
        y=slope * xs + intercept,
        mode="lines",
        line=dict(color=WARM, width=2, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=eu["urban_population_pct"],
        y=eu["pm25_exposure"],
        mode="markers",
        name="Europe",
        marker=dict(size=14, color="rgba(0, 0, 0, 0)", line=dict(width=2, color=WARM)),
        customdata=eu[["country"]],
        hovertemplate=HOVER,
    ))
    fig.add_annotation(
        x=0.98,
        y=0.95,
        xref="paper",
        yref="paper",
        xanchor="right",
        text=f"Europe: r = {r:.2f}",
        showarrow=False,
        font=dict(color=WARM, size=19, weight=700),
    )
    fig = _apply_theme(
        fig,
        height=620,
        margin=dict(l=8, r=28, t=12, b=8),
        showlegend=False,
        xaxis_title="Urban population (%)",
        yaxis_title="PM2.5 exposure (µg/m³)",
    )
    return fig


def build_gdp_vs_co2(df) -> go.Figure:
    """GDP per capita vs territorial CO₂ per capita, coloured by income group (wealth drives emissions)."""
    df["color"] = df["income_group"].map(_INCOME_COLORS)
    r = df["gdp_per_capita"].corr(df["co2_per_capita"])   # Pearson: strength of the wealth->CO₂ link
    fig = go.Figure(
        go.Scatter(
            x=df["gdp_per_capita"],
            y=df["co2_per_capita"],
            mode="markers+text",
            marker=dict(color=df["color"], size=15, line=dict(width=1, color="#ffffff")),
            customdata=df[["country"]],
            hovertemplate=(
                "<b> %{customdata[0]}</b><br>"
                " GDP: %{x:.0f}$/cap<br>"
                " CO₂: %{y:.1f}t/cap<extra></extra>"
            ),
        )
    )
    fig = _apply_theme(
        fig,
        height=620,
        xaxis_title="GDP per capita (international $, log scale)",
        yaxis_title="CO₂ per capita (tonnes)",
    )
    fig.update_xaxes(type="log")
    fig.add_annotation(x=0.03, y=0.96, xref="paper", yref="paper", xanchor="left",
                       text=f"r = {r:.2f}", showarrow=False, font=dict(color=ACCENT, size=19, weight=700))
    return fig
