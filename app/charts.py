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
# Warm, calm three-colour system. INK / ACCENT / WARM / GRID mirror --ink / --accent / --clay / --border.
INK = "#26231d"          # was #16202a
MUTED = "#857c6c"        # was #5c6b7a  (charts.js lightens this on the dark panel)
ACCENT = "#14532d"       # pine green   (was #0b7a43)
ACCENT_DARK = "#1c6b3e"  # was #01853a
WARM = "#c2603f"         # warm clay    (was #d1495b)
GRID = "#e7e0d0"         # warm grid    (was #e9ece7)
GRID_A = "#cfe8d6"       # was #c8ffa3
BLACK = "#1c1a17"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
BORDER_RADIUS = "14px"

# Light green for the Europe series on the dark finale panel — pine (#14532d) would
# vanish against the #123a24 panel, so the always-dark PM2.5 chart uses this instead.
EU_ON_DARK = "#7fbf8f"


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
        barcornerradius=5,
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
    "Strong decoupling":     "#14532d",  # pine
    "Weak decoupling":       "#7fae5a",  # soft leaf
    "Coupling":              "#d59a4a",  # amber
    "Emissions outpace GDP": "#c2603f",  # clay
    "Emissions rose":        "#8a6d9c",  # muted mauve
    "Recession":             "#a89e8a",  # warm stone
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
    "genuine": ACCENT, "net_exporter": "#d59a4a",
    "no_decoupling": "#a89e8a", "fake": WARM, "degrowth": "#8a6d9c",
}

def build_top_reducers(df) -> go.Figure:
    """Horizontal bar: top-15 European countries by % CO₂/capita cut over the last decade."""
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
                " CO₂/capita: %{customdata[0]:.1f} -> %{customdata[1]:.1f} t <br>"
                " Reduction: %{x:.2f}%<extra></extra>"
            ),
            text=d["reduction"].map(lambda v: f" -{v:.0f}%"),
            textfont=dict(size=15, color=ACCENT, weight=700),
            textposition="outside",
            cliponaxis=False,
        )
    )
    return _apply_theme(
        fig,
        height=620,
        bargap=0.36,
        xaxis_title="CO₂ per capita reduction over the last 10 years (%)",
        yaxis_title=None,
    )


def build_emissions_peak(df, top=15):
    """How much lower is the total CO₂ level in each country now than its historical maximum."""
    d = df.sort_values("abs_co2_drop", ascending=False).head(top).iloc[::-1]
    stem_x, stem_y = [], []
    for _, r in d.iterrows():
        stem_x += [0, r["abs_co2_drop"], None]
        stem_y += [r["country"], r["country"], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stem_x, 
                             y=stem_y, 
                             mode="lines",
                             line=dict(color=GRID, width=4), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=d["abs_co2_drop"], 
        y=d["country"], 
        mode="markers+text",
        marker=dict(color=ACCENT, size=13),
        text=d["abs_co2_drop"].map(lambda v: f"  -{v:.0f}%"),
        textposition='middle right',
        textfont=dict(size=14, color=ACCENT, weight=700),
        customdata=d[["year_of_peak", "max_co2_total", "current_co2_total"]],
        hovertemplate=("<b>%{y}</b><br>%{x:.0f}% below peak<br>"
                       "peak %{customdata[0]}: %{customdata[1]:.0f} Mt -> %{customdata[2]:.0f} Mt now"
                       "<extra></extra>"),
        showlegend=False,
    ))
    return _apply_theme(fig, 
                        height=520, 
                        xaxis_title="Below peak emissions (%)", 
                        yaxis_title=None)


def build_decade_change(df):
    """Heatmap: each country's % CO2 per capita change across the last three decades."""
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


def build_decoupling_index(df) -> go.Figure:
    """Tapio scatter (GDP index vs CO₂ index) for a single base year."""
    d = df.copy()
    d["category"] = [_tapio_category(g, c) for g, c in zip(d["gdp_index"], d["co2_index"])]
    d["color"] = d["category"].map(_TAPIO_COLORS)

    _HIDDEN_LABELS = {
        "Estonia", "Czechia", "Croatia", "Norway", "Netherlands", "Luxembourg",
        "Slovakia", "Belgium", "Finland", "Bulgaria", "Germany", "United Kingdom",
    }
    _TEXTPOS_OVERRIDES = {
        "Ukraine": "bottom center", "Latvia": "bottom center", "Denmark": "bottom center",
        "Switzerland": "bottom center", "Sweden": "bottom center", "Hungary": "bottom center",
        "Greece": "middle left",
    }

    fig = go.Figure(go.Scatter(
        x=d["gdp_index"], y=d["co2_index"], mode="markers+text", showlegend=False,
        marker=dict(color=d["color"], size=13, line=dict(width=1, color="#ffffff")),
        text=d["country"].map(lambda c: "" if c in _HIDDEN_LABELS else c),
        textposition=d["country"].map(lambda c: _TEXTPOS_OVERRIDES.get(c, "top center")),
        textfont=dict(size=12, color=INK),
        customdata=d[["country", "category", "elasticity"]],
        hovertemplate=("<b>%{customdata[0]}</b><br>GDP %{x:.0f} · CO₂ %{y:.0f}<br>"
                       "%{customdata[1]} (e = %{customdata[2]:.2f})<extra></extra>"),
    ))
    fig.add_hline(y=100, line=dict(color=ACCENT, width=2, dash="dash"), annotation_text="<b>CO₂ baseline</b>")
    fig.add_vline(x=100, line=dict(color=ACCENT, width=2, dash="dash"), annotation_text="<b> GDP baseline</b>")
    fig.add_annotation(x=0.98, y=0.07, xref="paper", yref="paper",
                       text="<b>GDP ↑ · CO₂ ↓ = decoupling</b>", showarrow=False, xanchor="right")
    fig.update_annotations(font=dict(color=ACCENT, size=15))
    return _apply_theme(fig, height=590, margin=dict(l=8, r=28, t=12, b=8),
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
                text=d["gap_per_capita"].map(lambda v: f" {v:.1f}"),
                textposition="outside",
                textfont=dict(size=16, color=colors, weight=700),
                customdata=d[["co2_per_capita", "consumption_co2_per_capita"]],
                hovertemplate=("<b>%{y}</b><br>territorial CO₂: %{customdata[0]:.1f} t/cap <br>consumption CO₂: %{customdata[1]:.1f} t/cap"
                                "<br>gap: %{x:.1f} t/cap<extra></extra>"),
    ))
    fig.add_vline(x=0, line=dict(color=INK, width=2))
    return _apply_theme(fig,
                        height=710,
                        bargap=0.3,
                        xaxis_title="Difference between consumption CO₂ and territorial CO₂ per capita (tonnes/capita)",
                        yaxis_title=None)


def build_hero_teaser(df) -> go.Figure:
    """Compact landing-hero dumbbell: territorial (reported) vs consumption (actual)
    CO₂/capita for the countries with the widest gap - a one-glance hook for the
    flattering-vs-honest twist. Malta (an extreme outlier) is dropped so the axis
    isn't skewed."""
    d = (df[df["country"] != "Malta"]
         .nlargest(5, "gap_per_capita")
         .sort_values("gap_per_capita"))
    fig = go.Figure()
    for _, r in d.iterrows():
        fig.add_trace(go.Scatter(
            x=[r["co2_per_capita"], r["consumption_co2_per_capita"]],
            y=[r["country"], r["country"]],
            mode="lines", line=dict(color=GRID, width=3),
            hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=d["co2_per_capita"], y=d["country"], mode="markers",
        marker=dict(color=ACCENT, size=13),
        hovertemplate="<b>%{y}</b><br>Territorial (reported): %{x:.1f} t/cap<extra></extra>",
        showlegend=False))
    fig.add_trace(go.Scatter(
        x=d["consumption_co2_per_capita"], y=d["country"], mode="markers",
        marker=dict(color=WARM, size=13),
        hovertemplate="<b>%{y}</b><br>Consumption (actual): %{x:.1f} t/cap<extra></extra>",
        showlegend=False))
    fig = _apply_theme(fig, height=330, margin=dict(l=8, r=20, t=8, b=40),
                       xaxis_title="CO₂ per capita (tonnes)", yaxis_title=None)
    fig.update_xaxes(rangemode="tozero")
    return fig


def build_fake_decoupler_board(df, top=15):
    """Horizontal bar: net imported emissions as a share of territorial CO₂ (offshoring)."""
    d = df.sort_values("trade_co2_share", ascending=False).head(top).iloc[::-1]
    fig = go.Figure(
            go.Bar(
                x=d["trade_co2_share"], 
                y=d["country"], 
                orientation="h", 
                marker_color=WARM,
                text=d["trade_co2_share"].map(lambda v: f" +{v:.0f}%"),
                textfont=dict(size=14, color=WARM, weight=700),
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>net imported emissions: %{x:.0f}% of territorial<extra></extra>",
    ))
    return _apply_theme(fig,
                        height=630,
                        bargap=0.36,
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
    # Left (primary) axis carries the CO₂ bars; right (secondary) axis carries the urban line.
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
    fig.add_trace(go.Scatter(          # rest of the world (charts.js lightens MUTED on the dark panel)
        x=row["urban_population_pct"], 
        y=row["pm25_exposure"], 
        mode="markers", 
        name="Rest of world",
        marker=dict(size=9, color=MUTED, opacity=0.35),
        customdata=row[["country"]], 
        hovertemplate=HOVER,
    ))
    fig.add_trace(go.Scatter(          # Europe regression, drawn under the rings
        x=xs, 
        y=slope * xs + intercept, 
        mode="lines",
        line=dict(color=WARM, width=2, dash="dash"), 
        hoverinfo="skip", 
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(          # Europe — hollow rings so they read on the dark panel
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
                       text=f"r = {r:.2f}", showarrow=False, font=dict(color=ACCENT, size=19, weight=700)) # weight=700 
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
    # Verdict colour key is rendered as a custom HTML legend under the chart (see routes).
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


# Chapter 4 - Transition Performance Index (TPI)
_TPI_VERDICT_COLORS = {
    "Genuine": ACCENT,
    "Fake":    WARM,
    "Special": "#d59a4a",   # amber
    "Other":   "#a89e8a",   # warm stone
}

_TPI_COMPONENT_COLORS = {
    "honesty":         ACCENT,      # pine - the 0.40 anchor
    "co2_reduction":   "#3f7f88",   # teal
    "abs_consumption": "#9c6f84",   # mauve
    "energy_clean":    "#d59a4a",   # amber
    "prosperity":      "#7f8a72",   # sage
    "momentum":        "#cbbfa6",   # sand
}


def _tpi_headline(df):
    """NB08 headline ranking: drop data-quality ('!') flags, keep boundary ('*') ones."""
    return df[~df["flag"].fillna("").str.contains("!")]


def build_tpi_score(df, top=15) -> go.Figure:
    """One TPI leaderboard figure for a single base year (top-15 by final score,
    coloured by decoupling verdict). Data-quality-flagged countries are dropped;
    boundary cases keep a trailing asterisk."""
    d = _tpi_headline(df).sort_values("final", ascending=False).head(top).iloc[::-1].copy()
    d["label"] = d["country"] + d["flag"].fillna("").map(lambda f: " *" if "*" in f else "")
    d["color"] = d["verdict"].map(_TPI_VERDICT_COLORS)
    d["scoretext"] = d["final"].map(lambda v: f"{v:.1f}")

    fig = go.Figure(go.Bar(
        x=d["final"], y=d["label"], orientation="h",
        marker_color=d["color"], cliponaxis=False, showlegend=False,
        text=d["scoretext"], textposition="outside",
        textfont=dict(size=13, color=INK),
        customdata=d[["verdict"]],
        hovertemplate="<b>%{y}</b><br>TPI score: %{x:.1f}<br>Verdict: %{customdata[0]}<extra></extra>",
    ))
    fig.update_layout(barcornerradius=4)
    fig = _apply_theme(
        fig, 
        height=630, 
        bargap=0.4, 
        margin=dict(l=8, r=44, t=8, b=36),
        xaxis_title="Transition Performance Index"
    )
    fig.update_xaxes(range=[0, float(d["final"].max()) * 1.14])
    return fig


def build_rank_shift(df_2000, df_1990) -> go.Figure:
    """Slope chart: each country's TPI rank under a 1990 vs 2000 base year (the Soviet-windfall test).

    All countries are shown (not just the headline top-15); a line sloping down to the right
    lost rank when the clock starts in 2000, i.e. its lead leaned on the post-Soviet collapse.
    """
    r2000 = df_2000.reset_index(drop=True).copy()
    r1990 = df_1990.reset_index(drop=True).copy()
    r2000["rank_2000"] = range(1, len(r2000) + 1)
    r1990["rank_1990"] = range(1, len(r1990) + 1)
    shift = r2000[["iso_code", "country", "verdict", "rank_2000"]].merge(
        r1990[["iso_code", "rank_1990"]], on="iso_code", how="inner")

    fig = go.Figure()
    for _, row in shift.iterrows():
        color = _TPI_VERDICT_COLORS.get(row["verdict"], MUTED)
        fig.add_trace(go.Scatter(
            x=["1990 base", "2000 base"],
            y=[row["rank_1990"], row["rank_2000"]],
            mode="lines+markers+text",
            text=["", row["country"]],
            textposition="middle right",
            textfont=dict(size=11, color=INK),
            line=dict(color=color, width=2),
            marker=dict(size=8, color=color),
            cliponaxis=False,
            hovertemplate=(f"<b>{row['country']}</b> · {row['verdict']}"
                           "<br>%{x}: rank %{y}<extra></extra>"),
            showlegend=False,
        ))
    return _apply_theme(
        fig, height=730, margin=dict(l=8, r=150, t=8, b=8),
        xaxis_title=None,
        yaxis=dict(title="TPI rank (1 = best)", autorange="reversed"))


def build_tpi_weighted_contribution(df, top=15) -> go.Figure:
    """Stacked bars: how each weighted component (plus momentum) builds the top-15 TPI scores.

    The five weighted components sum to the composite; momentum (±3, added after all weights) is stacked
    on top so the full bar height equals the `final` score shown on the leaderboard.
    """
    WEIGHTS = {"honesty": 0.40, "co2_reduction": 0.15, "abs_consumption": 0.15,
               "energy_clean": 0.15, "prosperity": 0.15}
    d = _tpi_headline(df).sort_values("final", ascending=False).head(top).copy()

    component_pairs = [("honesty", "s_honesty"), ("co2_reduction", "s_co2"),
                       ("abs_consumption", "s_abs"), ("energy_clean", "s_energy"),
                       ("prosperity", "s_prosperity")]
    contrib = pd.DataFrame({"country": d["country"].values})
    for name, score_col in component_pairs:
        contrib[name] = d[score_col].fillna(0).values * WEIGHTS[name]
    contrib["momentum"] = d["momentum"].fillna(0).values
    contrib["final"] = d["final"].values

    segments = [
        ("honesty",         "Honesty (consumption cut - fake-decoupling penalty)"),
        ("co2_reduction",   "Territorial CO₂/capita cut"),
        ("abs_consumption", "Consumption CO₂/capita"),
        ("energy_clean",    "Grid cleanliness"),
        ("prosperity",      "GDP per capita"),
        ("momentum",        "Momentum (recent trend, ±3)"),
    ]
    custom = contrib[["honesty", "co2_reduction", "abs_consumption",
                      "energy_clean", "prosperity", "momentum", "final"]]
    hover = ("<b>%{x}</b><br>"
             "Honesty: %{customdata[0]:.1f} pts<br>"
             "Territorial CO₂ cut: %{customdata[1]:.1f} pts<br>"
             "Absolute consumption: %{customdata[2]:.1f} pts<br>"
             "Grid cleanliness: %{customdata[3]:.1f} pts<br>"
             "GDP/capita: %{customdata[4]:.1f} pts<br>"
             "Momentum: %{customdata[5]:.1f} pts<br>"
             "<b>Final score: %{customdata[6]:.1f}</b><extra></extra>")

    fig = go.Figure()
    last = segments[-1][0]
    for name, label in segments:
        fig.add_trace(go.Bar(
            name=label,
            x=contrib["country"],
            y=contrib[name],
            marker_color=_TPI_COMPONENT_COLORS[name],
            customdata=custom,
            hovertemplate=hover,
            text=contrib["final"].map(lambda v: f"{v:.0f}") if name == last else None,
            textposition="outside",
            textfont=dict(size=13, color=INK, weight=700),
            showlegend=False,
        ))
    fig.update_layout(barmode="stack")
    return _apply_theme(
        fig,
        height=660,
        xaxis_title=None,
        yaxis_title="TPI points (weighted)",
    )


def build_tpi_journey(df) -> go.Figure:
    """Scatter of TPI score vs current consumption CO₂/capita - the journey vs the destination.

    Y is reversed so cleaner (lower footprint) sits at the top: top-right = high-scoring AND clean.
    The 2 t/capita fair-share line makes the point that a good score isn't a clean footprint yet.
    """
    fig = go.Figure()
    _TEXTPOS_OVERRIDES = {
        "LTU": "bottom center", "DEU": "bottom center", "GRC": "middle right",
        "FIN": "middle right", "IRL": "middle right", "NOR": "middle right", 
        "SWE": "middle right", "PRT": "middle right",
    }
    for v in ("Genuine", "Fake", "Special", "Other"):
        sub = df[df["verdict"] == v]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["composite"], 
            y=sub["cons_latest"],
            mode="markers+text", 
            name=v,
            text=sub["iso_code"], 
            textposition=sub["iso_code"].map(lambda c: _TEXTPOS_OVERRIDES.get(c, "top center")),
            textfont=dict(size=10, color=INK),
            marker=dict(size=13, color=_TPI_VERDICT_COLORS[v], line=dict(width=1, color="#ffffff")),
            customdata=sub[["country"]],
            hovertemplate=("<b>%{customdata[0]}</b><br>TPI score: %{x:.1f}<br>"
                           "Consumption CO₂: %{y:.1f} t/capita<extra></extra>"),
            showlegend=False,
        ))
    fig.add_hline(y=2, line=dict(color=ACCENT, width=2, dash="dash"),
                  annotation_text="2 t/capita fair-share target",
                  annotation_position="top right", annotation_font_color=ACCENT)
    fig.update_annotations(font=dict(size=15, weight=700))
    return _apply_theme(
        fig,
        height=620,
        margin=dict(l=8, r=28, t=8, b=8),
        xaxis_title="TPI score (2000 base)",
        yaxis=dict(title="Consumption CO₂ per capita (t, latest)", autorange="reversed"))


def build_tpi_sufficiency(df) -> go.Figure:
    """Grouped bars: actual vs required annual pace of consumption-CO₂ cuts for the TPI top-15.

    Actual pace (slate) below required pace (red) = a high-ranking country still off a Paris-
    compatible path. Relative virtue is not sufficiency.
    """
    d = df.copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Actual pace (from 2010 to the latest)",
        x=d["country"], 
        y=d["actual_cut_pct"], 
        marker_color=MUTED,
        customdata=d[["country", "required_cut_pct"]],
        hovertemplate=("<b>%{customdata[0]}</b><br>Actual: %{y:.1f}%/year cut<br>"
                       "Required: %{customdata[1]:.1f}%/year<extra></extra>"),
        showlegend=False,
    ))
    fig.add_trace(go.Bar(
        name="Required for 2t by 2050",
        x=d["country"], 
        y=d["required_cut_pct"], 
        marker_color=WARM,
        customdata=d[["country", "actual_cut_pct"]],
        hovertemplate=("<b>%{customdata[0]}</b><br>Required: %{y:.1f}%/year<br>"
                       "Actual: %{customdata[1]:.1f}%/year cut<extra></extra>"),
        showlegend=False,
    ))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_xaxes(categoryorder="array", categoryarray=d["country"].tolist())
    return _apply_theme(
        fig,
        height=560,
        margin=dict(l=8, r=28, t=8, b=8),
        xaxis_title=None,
        yaxis_title="Annual reduction rate (%/year, positive = cutting)"
    )
