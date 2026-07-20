"""
Tests for the fairness-referee internals in app.charts.synthesis.

_mc_rank_samples and build_tpi_robustness are pure functions of their input frame,
so their mechanics and structure are unit-tested with a small synthetic leaderboard
(no DB). The published reproducibility numbers (NB08, seed 42) and the component-
redundancy bound are asserted against the real leaderboard and marked `integration`.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from app.charts.synthesis import (
    _mc_rank_samples,
    build_tpi_robustness,
    _MC_COMPONENT_COLUMNS,
)
from db import data_service


def _synthetic_leaderboard():
    """Four countries. AAA dominates every component, so it must rank 1 under any
    positive weighting; DDD carries a data-quality ('!') flag the referee must drop."""
    return pd.DataFrame({
        "iso_code":     ["AAA", "BBB", "CCC", "DDD"],
        "country":      ["Aaa", "Bbb", "Ccc", "Ddd"],
        "verdict":      ["genuine", "partial", "fake", "genuine"],
        "flag":         [None, None, "*", "!"],
        "s_honesty":    [90.0, 60.0, 30.0, 99.0],
        "s_energy":     [88.0, 55.0, 25.0, 99.0],
        "s_abs":        [86.0, 50.0, 20.0, 99.0],
        "s_prosperity": [84.0, 45.0, 15.0, 99.0],
        "s_co2":        [82.0, 40.0, 10.0, 99.0],
    })


# --- Unit: _mc_rank_samples mechanics ---
def test_mc_rank_samples_drops_quality_flag_and_shapes():
    samples = _mc_rank_samples(_synthetic_leaderboard(), n_draws=500)
    assert set(samples) == {"AAA", "BBB", "CCC"}          # DDD ('!') dropped
    assert all(arr.shape == (500,) for arr in samples.values())
    stacked = np.concatenate(list(samples.values()))
    assert stacked.min() >= 1 and stacked.max() <= 3       # ranks within [1, n_clean]


def test_mc_rank_samples_dominant_country_always_first():
    samples = _mc_rank_samples(_synthetic_leaderboard(), n_draws=500)
    assert (samples["AAA"] == 1).all()
    assert np.median(samples["AAA"]) == 1.0


def test_mc_rank_samples_deterministic_for_seed():
    a = _mc_rank_samples(_synthetic_leaderboard(), n_draws=500, seed=42)
    b = _mc_rank_samples(_synthetic_leaderboard(), n_draws=500, seed=42)
    assert all(np.array_equal(a[k], b[k]) for k in a)


# --- Unit: build_tpi_robustness structure ---
def test_robustness_figure_traces_and_order():
    fig = build_tpi_robustness(_synthetic_leaderboard(), top=12)
    assert isinstance(fig, go.Figure)
    assert all(isinstance(tr, go.Box) for tr in fig.data)
    # DDD dropped; the rest ordered by median rank (AAA best).
    assert [tr.name for tr in fig.data] == ["AAA", "BBB", "CCC"]


def test_robustness_respects_top_cap():
    fig = build_tpi_robustness(_synthetic_leaderboard(), top=2)
    assert [tr.name for tr in fig.data] == ["AAA", "BBB"]


# --- Integration: reproducibility against the real leaderboard ---
# These lock the numbers the methodology chapter publishes. If they fail, the
# referee's output has drifted - a real signal, not a flaky test.
@pytest.mark.integration
def test_mc_rank_samples_reproduces_published_numbers():
    samples = _mc_rank_samples(data_service.get_tpi_leaderboard(2000))  # seed 42, 2000 draws
    medians = {iso: float(np.median(r)) for iso, r in samples.items()}
    assert medians["SWE"] == 2.0                       # NB08's validated headline number
    top4 = sorted(medians, key=medians.get)[:4]
    assert {"SWE", "FIN", "NOR"} <= set(top4)          # the leading group is stable


@pytest.mark.integration
def test_tpi_components_not_redundant():
    df = data_service.get_tpi_leaderboard(2000)
    corr = df[_MC_COMPONENT_COLUMNS].astype(float).corr().abs()
    off_diag = corr.where(~np.eye(len(corr), dtype=bool)).stack()
    assert off_diag.max() < 0.6, f"components too correlated:\n{off_diag.sort_values()}"


@pytest.mark.integration
def test_robustness_contender_order_real_data():
    fig = build_tpi_robustness(data_service.get_tpi_leaderboard(2000), top=12)
    assert len(fig.data) == 12
    assert fig.data[0].name == "SWE"                   # lowest median rank leads the plot
