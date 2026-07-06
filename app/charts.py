import numpy as np
import pandas as pd
"""
Figure builders for the dashboard - one builder per data_service getter.

Layering: route = orchestration, charts = figures (this file), data_service = data.
Each builder takes a DataFrame and returns a Plotly go.Figure; the route serializes
it with fig.to_json() and the browser renders it via Plotly.newPlot (see static/js/charts.js).
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Palette shared with app/static/css/style.css so the figures and the page read as one piece.
INK = "#16202a"
MUTED = "#5c6b7a"
ACCENT = "#0b7a43"       # deep decoupling green
ACCENT_DARK = "#01853a"
WARM = "#d1495b"
GRID = "#e9ece7"
GRID_A = "#c8ffa3"
BLACK = "#121312"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def _apply_theme(fig: go.Figure, **layout) -> go.Figure:
    """Apply the shared Nalada look: transparent background, house font and grid."""
    margin = layout.pop("margin", dict(l=8, r=28, t=8, b=8))
    fig.update_layout(
        font=dict(family=FONT, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=margin,
        colorway=[ACCENT, WARM, MUTED],
        hoverlabel=dict(font_family=FONT, bgcolor="rgba(255,255,255,0.75)", bordercolor=INK),
        **layout,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    return fig


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert #rrggbb to an rgba() string with the given alpha - for translucent fills."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"



#Decoupling part

# Tapio decoupling categories (shared vocabulary with NB09)
_TAPIO_COLORS = {
    "Strong decoupling":     "#01853A",
    "Weak decoupling":       "#A6D96A",
    "Coupling":              "#F2C14E",
    "Emissions outpace GDP": "#DF2E25",
    "Emissions rose":        "#7F14A2",
    "Recession":             "#878787",
}


def _tapio_category(gdp_index, co2_index):
    """Classify a (GDP index, CO₂ index) point into a Tapio decoupling zone."""
    delta_gdp = gdp_index - 100
    delta_co2 = co2_index - 100
    if delta_gdp > 0:
        if delta_co2 <= 0:
            return "Strong decoupling"
        e = delta_co2 / delta_gdp
        if e < 0.8:
            return "Weak decoupling"
        if e <= 1.2:
            return "Coupling"
        return "Emissions outpace GDP"
    if delta_co2 > 0:
        return "Emissions rose"
    return "Recession"


# decoupler_class verdicts (NB04)
_VERDICT_ORDER = ["genuine", "net_exporter", "no_decoupling", "fake", "degrowth"]
_VERDICT_LABEL = {
    "genuine": "Genuine", "net_exporter": "Net exporter",
    "no_decoupling": "No decoupling", "fake": "Fake", "degrowth": "Degrowth",
}
_VERDICT_COLORS = {
    "genuine": ACCENT, "net_exporter": "#e0a24a",
    "no_decoupling": "#9aa7b1", "fake": WARM, "degrowth": "#7F14A2",
}


def build_emissions_peak(df, top=15):
    """Lollipop: how far below its all-time peak each country's total CO₂ now sits."""
    d = df.sort_values("abs_co2_drop", ascending=False).head(top).iloc[::-1]
    stem_x, stem_y = [], []
    for _, r in d.iterrows():
        stem_x += [0, r["abs_co2_drop"], None]
        stem_y += [r["country"], r["country"], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stem_x, 
                             y=stem_y, 
                             mode="lines",
                             line=dict(color=GRID, width=3), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=d["abs_co2_drop"], 
        y=d["country"], 
        mode="markers",
        marker=dict(color=ACCENT, size=11),
        customdata=d[["year_of_peak", "max_co2_total", "current_co2_total"]],
        hovertemplate=("<b>%{y}</b><br>%{x:.0f}% below peak<br>"
                       "peak %{customdata[0]}: %{customdata[1]:.0f} Mt -> now: %{customdata[2]:.0f} Mt"
                       "<extra></extra>"),
        showlegend=False,
    ))
    return _apply_theme(fig, height=520, xaxis_title="Below peak emissions (%)", yaxis_title=None)


def build_decade_change(df):
    """Heatmap: each country's % CO2/capita change across the last three decades."""
    labels = {2000: "1990s", 2010: "2000s", 2020: "2010s"}
    d = df.copy()
    d["decade"] = d["year"].map(labels)
    piv = d.pivot_table(index="country", columns="decade", values="reduction")
    piv = piv.reindex(columns=["1990s", "2000s", "2010s"])
    piv = piv.loc[piv.mean(axis=1).sort_values().index]
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=list(piv.columns), y=list(piv.index),
        colorscale=[[0.0, WARM], [0.5, "#f4f1e4"], [1.0, ACCENT]], zmid=0,
        colorbar=dict(title="% cut", thickness=12),
        hovertemplate="%{y} · %{x}<br>%{z:.0f}% change<extra></extra>",
    ))
    return _apply_theme(fig, height=760, margin=dict(l=8, r=28, t=8, b=8),
                        xaxis_title=None, yaxis_title=None)


def build_decoupling_index(df_2000, df_1990):
    """Tapio scatter (GDP index vs CO₂ index) with a 1990/2000 base-year toggle."""
    def prep(df):
        d = df.copy()
        d["category"] = [_tapio_category(g, c) for g, c in zip(d["gdp_index"], d["co2_index"])]
        d["color"] = d["category"].map(_TAPIO_COLORS)
        return d

    _HIDDEN_LABELS = {
        "Estonia", "Czechia", "Croatia", "Norway",
        "Netherlands", "Luxembourg", "Slovakia", "Belgium", 
        "Finland", "Bulgaria", "Germany", "United Kingdom",
    } 
    _TEXTPOS_OVERRIDES = {
        "Ukraine": "bottom center", "Latvia": "bottom center",
        "Denmark": "bottom center", "Switzerland": "bottom center", 
        "Sweden": "bottom center", "Hungary": "bottom center", "Greece": "middle left",
    }

    def scatter(d, visible):
        return go.Scatter(
            x=d["gdp_index"],
            y=d["co2_index"],
            mode="markers+text",
            visible=visible,
            showlegend=False,
            marker=dict(color=d["color"], size=13, line=dict(width=1, color="#ffffff")),
            text=d["country"].map(lambda c: "" if c in _HIDDEN_LABELS else c),
            textposition=d["country"].map(lambda c: _TEXTPOS_OVERRIDES.get(c, "top center")),
            textfont=dict(size=12, color=INK),
            customdata=d[["country", "category", "elasticity"]],
            hovertemplate=("<b>%{customdata[0]}</b><br>GDP %{x:.0f} · CO₂ %{y:.0f}<br>"
                           "%{customdata[1]} (e = %{customdata[2]:.2f})<extra></extra>"),
        )

    a, b = prep(df_2000), prep(df_1990)
    fig = go.Figure(
            [scatter(a, True), 
             scatter(b, False)
            ])
    fig.add_hline(y=100, line=dict(color=INK, width=1, dash='dash'), annotation_text='CO₂ baseline')
    fig.add_vline(x=100, line=dict(color=INK, width=1, dash='dash'), annotation_text=' GDP baseline')
    fig.add_annotation(x=0.98, y=0.07, xref="paper", yref="paper",
                       text="GDP ↑ · CO₂ ↓ = decoupling", showarrow=False,
                       font=dict(color=ACCENT, size=15), xanchor="right")
    fig.update_layout(updatemenus=[dict(
        type="buttons", direction="right", x=0, y=1.14, xanchor="left", yanchor="top",
        pad=dict(b=4), showactive=True,
        buttons=[
            dict(label="Since 2000", method="restyle", args=[{"visible": [True, False]}]),
            dict(label="Since 1990", method="restyle", args=[{"visible": [False, True]}]),
        ],
    )])
    return _apply_theme(fig, 
                        height=590, 
                        margin=dict(l=8, r=28, t=52, b=8),
                        xaxis_title="GDP index (base year = 100)",
                        yaxis_title="Territorial CO₂ index (base year = 100)")


def build_consumption_gap(df):
    """Diverging bar: consumption minus territorial CO₂ per capita (importers vs exporters)."""
    d = df.sort_values("gap_per_capita")
    colors = [WARM if v > 0 else ACCENT for v in d["gap_per_capita"]]
    fig = go.Figure(
            go.Bar(
                x=d["gap_per_capita"], 
                y=d["country"], 
                orientation="h", 
                marker_color=colors,
                text=d["gap_per_capita"].map(lambda v: f"{v:.1f}"),
                textposition="outside",
                customdata=d[["co2_per_capita", "consumption_co2_per_capita"]],
                hovertemplate=("<b>%{y}</b><br>territorial CO₂: %{customdata[0]:.1f} t/cap <br>consumption CO₂: %{customdata[1]:.1f} t/cap"
                                "<br>gap: %{x:.1f} t/cap<extra></extra>"),
    ))
    fig.add_vline(x=0, line=dict(color=INK, width=1))
    return _apply_theme(fig, 
                        height=700,
                        xaxis_title="Difference between consumption CO₂ and territorial CO₂ per capita (tonnes/capita)",
                        yaxis_title=None)


def build_fake_decoupler_board(df, top=15):
    """Horizontal bar: net imported emissions as a share of territorial CO₂ (offshoring)."""
    d = df.sort_values("trade_co2_share", ascending=False).head(top).iloc[::-1]
    fig = go.Figure(
            go.Bar(
                x=d["trade_co2_share"], 
                y=d["country"], 
                orientation="h", 
                marker_color=WARM,
                text=d["trade_co2_share"].map(lambda v: f"{v:.0f}%"),
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>net imported emissions: %{x:.0f}% of territorial<extra></extra>",
    ))
    return _apply_theme(fig,
                        height=520,
                        xaxis_title="Net imported emissions (% of territorial CO₂)",
                        yaxis_title=None)


def build_decoupler_board(df):
    """The verdict: countries grouped by genuine/fake/… along their territorial-CO₂ cut."""
    MIN_GAP = 6.0
    BASE_AY = 20
    TIER_STEP = 16
    LEADER = "#aab4b2"
    fig = go.Figure()
    for v in _VERDICT_ORDER:
        sub = df[df["verdict"] == v]
        if sub.empty:
            continue
        sub = sub.assign(caveat=sub["caveat"].fillna(""))
        sub = sub.sort_values("co2_index").reset_index(drop=True)
        label = _VERDICT_LABEL[v]
        fig.add_trace(go.Scatter(
            x=sub["co2_index"], y=[label] * len(sub), mode="markers",
            name=label,
            marker=dict(color=_VERDICT_COLORS[v], size=14, line=dict(width=1.5, color="#ffffff")),
            customdata=sub[["country", "gap", "trade_co2_share", "caveat"]],
            hovertemplate=("<b>%{customdata[0]}</b><br>territorial CO₂ index %{x:.0f}"
                           "<br>gap %{customdata[1]:.0f} · trade %{customdata[2]:.0f}%"
                           "<br>%{customdata[3]}<extra></extra>"),
            showlegend=False,
        ))
        tier_last_x = []
        for _, r in sub.iterrows():
            x = r["co2_index"]
            tier = 0
            while tier < len(tier_last_x) and x - tier_last_x[tier] < MIN_GAP:
                tier += 1
            if tier == len(tier_last_x):
                tier_last_x.append(x)
            else:
                tier_last_x[tier] = x
            mag = BASE_AY + (tier // 2) * TIER_STEP
            ay = -mag if tier % 2 == 0 else mag
            fig.add_annotation(
                x=x, y=label, text=r["country"], xref="x", yref="y",
                showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=LEADER,
                ax=0, ay=ay, axref="pixel", ayref="pixel",
                font=dict(size=12, color=INK),
            )
    order = [_VERDICT_LABEL[v] for v in _VERDICT_ORDER if (df["verdict"] == v).any()]
    fig.update_yaxes(categoryorder="array", categoryarray=order[::-1])
    return _apply_theme(fig, height=620, margin=dict(l=8, r=28, t=64, b=8),
                        xaxis_title="Territorial CO₂ index (1990 = 100) - the lower, the greater the decrease",
                        yaxis_title=None)


def build_top_reducers(df) -> go.Figure:
    """Horizontal bar: top-10 European countries by % CO₂/capita cut over the last decade."""
    d = df.sort_values("reduction")
    fig = go.Figure(
        go.Bar(
            x=d["reduction"],
            y=d["country"],
            orientation="h",
            marker_color=ACCENT,
            customdata=d[["prev_co2_per_capita", "co2_per_capita"]],
            hovertemplate=(
                "<b> %{y}</b><br>"
                " CO₂ / capita: %{customdata[0]:.2f} -> %{customdata[1]:.2f} t <br>"
                " Reduction: %{x:.2f}%<extra></extra>"
            ),
            text=d["reduction"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
            cliponaxis=False,
        )
    )
    return _apply_theme(
        fig,
        height=430,
        bargap=0.33,
        xaxis_title="CO₂ per capita reduction over 10 years (%)",
        yaxis_title=None,
    )


# Context - Chapter 1
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
                    line=dict(color=WARM),
                    marker=dict(size=16),
                    customdata=df[["countries"]],
                    hovertemplate=( "<b>%{x}</b><br>Countries: %{customdata[0]}<br>"
                                    "Average urbanization: %{y:.0f}%"
                                    "<extra></extra>"
                    ),
                    showlegend=False,
                ), secondary_y=True)
    fig.update_xaxes(categoryorder="array", categoryarray=order)
    fig = _apply_theme(
        fig,
        height=560,
        bargap=0.38,
        xaxis_title=None,
        yaxis_title="Average CO₂/capita (tonnes)",
    )
    fig.update_yaxes(rangemode="tozero", secondary_y=False)
    fig.update_yaxes(title_text="Average urban population (%)", rangemode="tozero", secondary_y=True)
    return fig


_INCOME_COLORS = {
    "High income":          "#01853A",
    "Upper middle income":  "#BDD96A",
    "Lower middle income":  "#F1B72F",
    "Low income":           "#DF2E25",
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
    """Urban % vs PM2.5: noisy worldwide, but clearly negative within Europe (highlighted, r ≈ -0.51)."""
    HOVER = ("<b>%{customdata[0]}</b><br> Urban population: %{x:.0f}%<br>"
             " PM2.5 exposure: %{y:.1f}µg/m³<extra></extra>")
    eu = df[df["is_europe"]].dropna(subset=["urban_population_pct", "pm25_exposure"])
    row = df[~df["is_europe"]]

    slope, intercept = np.polyfit(eu["urban_population_pct"], eu["pm25_exposure"], 1)
    xs = np.array([eu["urban_population_pct"].min(), eu["urban_population_pct"].max()])
    r = eu["urban_population_pct"].corr(eu["pm25_exposure"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(          # rest of the world
        x=row["urban_population_pct"], y=row["pm25_exposure"], mode="markers", name="Rest of world",
        marker=dict(size=9, color=MUTED, opacity=0.35),
        customdata=row[["country"]], hovertemplate=HOVER,
    ))
    fig.add_trace(go.Scatter(          # Europe
        x=eu["urban_population_pct"], y=eu["pm25_exposure"], mode="markers", name="Europe",
        marker=dict(size=15, color=ACCENT, line=dict(width=1, color="#ffffff")),
        customdata=eu[["country"]], hovertemplate=HOVER,
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=slope * xs + intercept, mode="lines",
        line=dict(color=ACCENT, width=2, dash="dash"), hoverinfo="skip", showlegend=False,
    ))
    fig.add_annotation(x=0.98, y=0.95, xref="paper", yref="paper", xanchor="right",
                       text=f"Europe: r = {r:.2f}", showarrow=False, font=dict(color=ACCENT, size=14))
    fig = _apply_theme(
        fig,
        height=620,
        margin=dict(l=8, r=28, t=40, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
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
                       text=f"r = {r:.2f}", showarrow=False, font=dict(color=ACCENT, size=16))
    return fig


#Structure - Chapter 3
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
    
    for v in _VERDICT_ORDER:
        if (df["verdict"] == v).any():
            fig.add_trace(go.Bar(
                x=[None], 
                y=[None], 
                name=_VERDICT_LABEL[v],
                marker_color=_VERDICT_COLORS[v], 
                hoverinfo="skip"
            ))
    return _apply_theme(
        fig,
        height=590,
        margin=dict(l=8, r=28, t=40, b=8),
        bargap=0.4,
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
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
        marker_color=ACCENT,
        customdata=g[["n_cities"]],
        hovertemplate=("<b>%{x}</b><br>Median: %{y:.0f} cars/1000 people<br>"
                       "Cities: %{customdata[0]}<extra></extra>"),
        text=g["median_cars"].map(lambda v: f"{v:.0f}"),
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