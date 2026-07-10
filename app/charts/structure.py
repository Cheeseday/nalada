"""Chapter 3 - Structure: honesty doesn't shape cities; city size does (a null result)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ._theme import (EU_ON_DARK, _apply_theme, _hex_to_rgba,
                     _VERDICT_LABEL, _VERDICT_COLORS)


def build_city_cars_by_country(df) -> go.Figure:
    """Horizontal bar: median cars/1000 per country, coloured by decoupling verdict"""
    df = df.copy()
    df["color"] = df["verdict"].map(_VERDICT_COLORS)
    fig = go.Figure(go.Bar(
        x=df["median_cars_per_1000"],
        y=df["country"],
        orientation="h",
        marker_color=df["color"],
        customdata=df[["n_cities"]],
        hovertemplate=("<b>%{y}</b><br>Median: %{x:.0f} cars/1000 people<br>"
        "Cities in stat: %{customdata[0]}<extra></extra>"),
        text=df["median_cars_per_1000"].map(lambda v: f"{v:.0f}"),
        textposition="outside",
        cliponaxis=False,
        showlegend=False,
    ))
    return _apply_theme(
        fig,
        height=590,
        margin=dict(l=8, r=28, t=8, b=8),
        bargap=0.4,
        xaxis_title="Median cars per 1000 people",
        yaxis_title=None,
    )


def build_cars_dist_by_verdict(df) -> go.Figure:
    """Box plot of cars/1000 by verdict: genuine sits slightly above fake - the honesty signal isn't there."""
    order = [v for v in ("genuine", "fake", "net_exporter") if (df["verdict"] == v).any()]
    fig = go.Figure()
    for v in order:
        sub = df[df["verdict"] == v]
        color = _VERDICT_COLORS[v]
        fig.add_trace(go.Box(
            y=sub["cars_per_1000"],
            name=_VERDICT_LABEL[v],
            boxmean="sd",
            boxpoints="all", jitter=0.5, pointpos=0, whiskerwidth=0.3,
            line_color=color,
            fillcolor=_hex_to_rgba(color, 0.18),
            marker=dict(color=color, size=4, opacity=0.5),
            customdata=sub[["city_code", "population"]],
            hovertemplate=("<b>%{customdata[0]}</b><br>%{y:.0f} cars/1000 people<br>"
                           "Population: %{customdata[1]:,.0f}<extra></extra>"),
            showlegend=False,
        ))
    return _apply_theme(
        fig,
        height=600,
        xaxis_title=None,
        yaxis_title="Cars per 1000 people",
    )


def build_cars_by_size_band(df) -> go.Figure:
    """Bars: median cars/1000 by city-size band. Size drives the reduction"""
    BINS = [0, 100_000, 250_000, 500_000, 1_000_000, np.inf]
    LABELS = ["<100k", "100-250k", "250-500k", "500k-1M", ">1M"]
    d = df.copy()
    d["size_band"] = pd.cut(d["population"], bins=BINS, labels=LABELS)
    g = (d.groupby("size_band", observed=True)
          .agg(median_cars=("cars_per_1000", "median"), n_cities=("city_code", "count"))
          .reindex(LABELS))
    fig = go.Figure(go.Bar(
        x=list(g.index),
        y=g["median_cars"],
        marker_color=EU_ON_DARK,
        customdata=g[["n_cities"]],
        hovertemplate=("<b>%{x}</b><br>Median: %{y:.0f} cars/1000 people<br>"
                       "Cities: %{customdata[0]}<extra></extra>"),
        text=g["median_cars"].map(lambda v: f"{v:.0f}"),
        textfont=dict(size=15),
        textposition="outside",
        cliponaxis=False,
    ))
    fig = _apply_theme(
        fig,
        height=520,
        bargap=0.35,
        xaxis_title="City population",
        yaxis_title="Median cars per 1000 people",
    )
    fig.update_xaxes(categoryorder="array", categoryarray=LABELS)
    return fig
