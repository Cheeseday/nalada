"""Chapter 4 - Synthesis: the honesty-weighted Transition Performance Index and its caveats."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ._theme import (INK, ACCENT, WARM, MUTED, _apply_theme, _hex_to_rgba,
                     _VERDICT_ORDER, _VERDICT_LABEL, _VERDICT_COLORS)


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
    d["color"] = d["verdict"].map(_VERDICT_COLORS)
    d["vlabel"] = d["verdict"].map(_VERDICT_LABEL)
    d["scoretext"] = d["final"].map(lambda v: f"{v:.1f}")

    fig = go.Figure(go.Bar(
        x=d["final"],
        y=d["label"],
        orientation="h",
        marker_color=d["color"],
        cliponaxis=False,
        showlegend=False,
        text=d["scoretext"],
        textposition="outside",
        textfont=dict(size=13, color=INK),
        customdata=d[["vlabel"]],
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
    """Slope chart: each country's TPI rank under a 1990 vs 2000 base year (the post-Soviet deindustrialization).

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
        color = _VERDICT_COLORS.get(row["verdict"], MUTED)
        vlabel = _VERDICT_LABEL.get(row["verdict"], row["verdict"])
        fig.add_trace(go.Scatter(
            x=["1990 base", "2000 base"],
            y=[row["rank_1990"], row["rank_2000"]],
            mode="lines+markers+text",
            text=["", row["country"]],
            textposition="middle right",
            textfont=dict(size=13, color=INK),
            line=dict(color=color, width=2),
            marker=dict(size=10, color=color),
            cliponaxis=False,
            hovertemplate=(f"<b>{row['country']}</b> · {vlabel}"
                           "<br>%{x}: rank %{y}<extra></extra>"),
            showlegend=False,
        ))
    return _apply_theme(
        fig, 
        height=730,
        margin=dict(l=8, r=150, t=8, b=8),
        xaxis_title=None,
        yaxis=dict(title="TPI rank (1 = best)", autorange="reversed")
    )


def build_tpi_weighted_contribution(df, top=15) -> go.Figure:
    """Stacked bars: how each weighted component (plus momentum) builds the top-15 TPI scores.

    The five weighted components sum to the composite; momentum (±3, added after all weights) is stacked
    on top so the full bar height equals the `final` score shown on the leaderboard.
    """
    WEIGHTS = {
        "honesty": 0.40,
        "co2_reduction": 0.15,
        "abs_consumption": 0.15,
        "energy_clean": 0.15,
        "prosperity": 0.15
    }
    d = _tpi_headline(df).sort_values("final", ascending=False).head(top).copy()

    component_pairs = [
        ("honesty", "s_honesty"),
        ("co2_reduction", "s_co2"),
        ("abs_consumption", "s_abs"),
        ("energy_clean", "s_energy"),
        ("prosperity", "s_prosperity")
    ]
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
             "Territorial CO₂/cap cut: %{customdata[1]:.1f} pts<br>"
             "Consumption CO₂/capita: %{customdata[2]:.1f} pts<br>"
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
        "LTU": "bottom center", 
        "DEU": "bottom center", 
        "GRC": "middle right",
        "FIN": "middle right", 
        "IRL": "middle right", 
        "NOR": "middle right",
        "SWE": "middle right", 
        "PRT": "middle right",
    }
    for v in _VERDICT_ORDER:
        sub = df[df["verdict"] == v]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["final"],
            y=sub["cons_latest"],
            mode="markers+text",
            name=_VERDICT_LABEL[v],
            text=sub["iso_code"],
            textposition=sub["iso_code"].map(lambda c: _TEXTPOS_OVERRIDES.get(c, "top center")),
            textfont=dict(size=12, color=INK),
            marker=dict(size=15, color=_VERDICT_COLORS[v], line=dict(width=1, color="#ffffff")),
            customdata=sub[["country"]],
            hovertemplate=("<b>%{customdata[0]}</b><br>TPI score: %{x:.1f}<br>"
                           "Consumption CO₂: %{y:.1f} t/capita<extra></extra>"),
            showlegend=False,
        ))
    fig.add_hline(
        y=2,
        line=dict(color=ACCENT, width=2, dash="dash"),
        annotation_text="2 t/capita fair-share target",
        annotation_position="top right",
        annotation_font_color=ACCENT
    )
    fig.update_annotations(font=dict(size=15, weight=700))
    return _apply_theme(
        fig,
        height=620,
        margin=dict(l=8, r=28, t=8, b=8),
        xaxis_title="TPI score (2000 base)",
        yaxis=dict(title="Consumption CO₂ per capita (t, latest)", autorange="reversed")
    )


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


# ---------------------------------------------------------------------------
# Fairness Referee 2, rendered live for the methodology chapter.
# Reproduces NB08's weight Monte Carlo straight from the component scores stored
# in tpi_scores - validated to match the notebook exactly at seed 42 (SWE median
# rank 2, FIN/NOR 3, PRT 4, GBR 5). Momentum is intentionally excluded and the
# data-quality ('!') flags are dropped, exactly as the notebook's referee does.
# ---------------------------------------------------------------------------
_MC_COMPONENT_COLUMNS = ["s_honesty", "s_energy", "s_abs", "s_prosperity", "s_co2"]


def _mc_rank_samples(df, n_draws=2000, seed=42):
    """{iso_code: array of ranks} across n_draws Dirichlet weightings of the five
    component scores, over the headline set. Each draw scores every country as a
    weighted average of whichever components it has (weights renormalised over the
    present ones) and ranks them. Vectorised over all draws at once."""
    clean = df[~df["flag"].fillna("").str.contains("!")].reset_index(drop=True)
    scores = clean[_MC_COMPONENT_COLUMNS].to_numpy(dtype=float)
    present = ~np.isnan(scores)
    filled = np.where(present, scores, 0.0)
    codes = clean["iso_code"].tolist()
    n, k = scores.shape

    rng = np.random.default_rng(seed)
    weights = rng.dirichlet(np.ones(k), size=n_draws)

    numerator = filled @ weights.T    # (n, n_draws)
    denominator = present @ weights.T
    composite = np.divide(numerator, denominator,
                          out=np.full_like(numerator, np.nan), where=denominator > 0)

    order = np.argsort(-composite, axis=0, kind="stable")      # rank 1 = highest composite
    ranks = np.empty_like(order)
    np.put_along_axis(ranks, order, np.arange(1, n + 1)[:, None], axis=0)

    return {iso: ranks[i] for i, iso in enumerate(codes)}


def build_tpi_robustness(df, top=12) -> go.Figure:
    """Box plot: how far each contender's TPI rank travels across 2,000 random
    weightings of the five components. A narrow box means the position barely depends
    on the weights - the point the fairness referees are making. Boxes are coloured by
    decoupling verdict; the rank axis is reversed so #1 sits at the top."""
    samples = _mc_rank_samples(df)
    medians = {iso: float(np.median(r)) for iso, r in samples.items()}
    contenders = sorted(samples, key=lambda iso: (medians[iso], np.mean(samples[iso])))[:top]

    verdict_of = dict(zip(df["iso_code"], df["verdict"]))
    country_of = dict(zip(df["iso_code"], df["country"]))

    fig = go.Figure()
    for iso in contenders:
        verdict = verdict_of.get(iso)
        color = _VERDICT_COLORS.get(verdict, MUTED)
        fig.add_trace(go.Box(
            y=samples[iso],
            name=iso,
            marker_color=color,
            line=dict(color=color, width=1.6),
            fillcolor=_hex_to_rgba(color, 0.25),
            boxpoints=False,
            whiskerwidth=0.4,
            showlegend=False,
            hovertext=f"{country_of.get(iso, iso)} - {_VERDICT_LABEL.get(verdict, '')}",
        ))
    fig.update_xaxes(categoryorder="array", categoryarray=contenders)
    return _apply_theme(
        fig,
        height=520,
        margin=dict(l=8, r=20, t=8, b=28),
        boxgap=0.45,
        xaxis_title=None,
        yaxis=dict(title="Rank under a random weighting (1 = best)",
                   autorange="reversed", dtick=2, zeroline=False),
    )
