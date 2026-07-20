"""
Integration tests for the data_service read layer.

These hit the real database, so they're integration tests (conftest skips them
when the DB is down). Run from the project root:  pytest -v
"""
import numpy as np
import pandas as pd
import pytest

from db import data_service

pytestmark = pytest.mark.integration

# Every get_* function paired with a readable id. Add new queries here.
GETTERS = [
    ("co2_urban_by_income",    data_service.get_co2_urban_by_income),
    ("density_vs_co2",         data_service.get_density_vs_co2),
    ("urban_vs_air_pollution", data_service.get_urban_vs_air_pollution),
    ("gdp_vs_co2",             data_service.get_gdp_vs_co2),
    ("decoupler_class",        data_service.get_decoupler_class),
    ("top_reducers",           data_service.get_top_reducers),
    ("decade_change",          data_service.get_decade_change),
    ("emissions_peak",         data_service.get_emissions_peak),
    ("fake_decoupler_board",   data_service.get_fake_decoupler_board),
    ("consumption_gap",        data_service.get_consumption_gap),
    ("subregion_rankings",     data_service.get_subregion_rankings),
    ("grid_cleanliness",       data_service.get_grid_cleanliness),
    ("city_cars_by_country",   data_service.get_city_cars_by_country),
    ("city_cars_snapshot",     data_service.get_city_cars_snapshot),
    ("tpi_leaderboard_2000",   lambda: data_service.get_tpi_leaderboard(2000)),
    ("tpi_leaderboard_1990",   lambda: data_service.get_tpi_leaderboard(1990)),
    ("tpi_sufficiency",        data_service.get_tpi_sufficiency),
    ("decoupling_index_2000",  lambda: data_service.get_decoupling_index(2000)),
    ("decoupling_index_1990",  lambda: data_service.get_decoupling_index(1990)),
]

VERDICTS = ['genuine', 'partial', 'fake', 'no_decoupling', 'net_exporter', 'degrowth']

# Pattern 1 - smoke across all queries: each one executes and returns a frame
# with columns. This is the pytest version of the __main__ block: if any .sql
# breaks, exactly that parametrised case fails (and names itself).
@pytest.mark.parametrize("getter", [g for _, g in GETTERS], ids=[n for n, _ in GETTERS])
def test_query_executes_and_returns_frame(getter):
    df = getter()
    assert isinstance(df, pd.DataFrame)
    assert df.shape[1] > 0          # has columns, even if zero rows


def test_city_cars_by_country():
    df = data_service.get_city_cars_by_country()
    unexp = set(df['verdict']) - set(VERDICTS)
    assert (df['n_cities'] > 0).all()
    assert not unexp, f"Unexpected verdict values: {unexp}"


# Pattern 2 - schema: a query exposes the columns the dashboard will rely on.
def test_top_reducers_has_expected_columns():
    df = data_service.get_top_reducers()
    assert {"country", "year", "co2_per_capita", "reduction"} <= set(df.columns)


def test_decade_change_has_expected_columns():
    df = data_service.get_decade_change()
    assert {'country', 'year', 'co2_per_capita', 'prev_co2_per_capita', 'reduction'} <= set(df.columns)


def test_tpi_leaderboard_has_expected_columns():
    df = data_service.get_tpi_leaderboard(2000)
    assert {'country', 'honesty_base_yr', 'verdict', 's_honesty', 's_abs',
            's_prosperity', 's_co2', 'momentum', 'final', 'base_year'} <= set(df.columns)


# The one bit of real pandas logic: get_tpi_leaderboard left-merges the canonical
# decoupler_class verdict on iso_code. A left merge silently yields NaN verdicts if
# any iso_code fails to match, so guard both the match and the vocabulary.
def test_tpi_leaderboard_verdicts_all_matched():
    df = data_service.get_tpi_leaderboard(2000)
    assert df['verdict'].notna().all(), "left-merge left some verdicts NaN"
    unexp = set(df['verdict'].dropna()) - set(VERDICTS)
    assert not unexp, f"Unexpected verdict values: {unexp}"


# Pattern 3 - domain rule: top_reducers is capped at 15 by its LIMIT.
def test_top_reducers_capped_by_limit():
    assert len(data_service.get_top_reducers()) <= 15


def test_tpi_sufficiency_capped_by_limit():
    assert len(data_service.get_tpi_sufficiency()) <= 15


# Pattern 4 - parameter behaviour: the 1990 base drops post-Soviet countries with
# no 1990 row, so it returns no more rows than the 2000 base.
def test_decoupling_1990_base_not_larger_than_2000():
    rows_2000 = len(data_service.get_decoupling_index(2000))
    rows_1990 = len(data_service.get_decoupling_index(1990))
    assert rows_1990 <= rows_2000


def test_tpi_leaderboard_1990_base_not_larger_than_2000():
    rows_2000 = len(data_service.get_tpi_leaderboard(2000))
    rows_1990 = len(data_service.get_tpi_leaderboard(1990))
    assert rows_1990 <= rows_2000


def test_decade_change_valid_values():
    df = data_service.get_decade_change()
    assert (df['co2_per_capita'] <= 40).all()
    assert (df['co2_per_capita'] > 0).all()
    assert (df['prev_co2_per_capita'] <= 40).all()
    assert (df['prev_co2_per_capita'] > 0).all()


def test_tpi_sufficiency_adequate_values():
    df = data_service.get_tpi_sufficiency()
    unexp = set(df['verdict']) - set(VERDICTS)
    assert (df['cons_now_t'] < 30).all()
    assert (df['final'] <= 100).all()
    assert not unexp, f"Unexpected verdict values: {unexp}"


def test_fake_board_adequate_values():
    df = data_service.get_fake_decoupler_board()
    assert not df.empty
    assert len(df) == df['rank'].max()
    assert (df['co2_total'] > 0).all()


def test_urban_by_income_valid_values():
    df = data_service.get_co2_urban_by_income()
    income_groups_amount = 4
    assert len(df) == income_groups_amount
    assert (df['avg_urban_pct'] <= 100).all()
    assert sum(df['countries']) > 190


# Pattern 5 - getter contracts on the TPI leaderboard. The four criterion-referenced
# components are score_linear outputs, so they're clipped to [0, 100]; honesty is a
# penalised component and may go negative (but never above 100).
CLIPPED_SCORES = ["s_abs", "s_prosperity", "s_co2", "s_energy"]


def test_tpi_clipped_scores_in_range():
    df = data_service.get_tpi_leaderboard(2000)
    for col in CLIPPED_SCORES:
        vals = df[col].dropna()
        bad = vals[~vals.between(0, 100)]
        assert bad.empty, f"{col} outside [0,100]: {bad.tolist()}"
    assert (df["s_honesty"].dropna() <= 100).all()


# The five weights sum to 1 (0.40 honesty + 4 x 0.15), so for a country with every
# component present the weighted parts plus momentum must reconstruct `final`. This
# locks both the weight vector and the SQL scoring pipeline in one assertion.
TPI_WEIGHTS = {"s_honesty": 0.40, "s_co2": 0.15, "s_abs": 0.15,
               "s_energy": 0.15, "s_prosperity": 0.15}


def test_tpi_final_reconstructs_from_weighted_components():
    assert round(sum(TPI_WEIGHTS.values()), 9) == 1.0
    df = data_service.get_tpi_leaderboard(2000)
    full = df.dropna(subset=list(TPI_WEIGHTS) + ["momentum", "final"])
    assert not full.empty, "no country has all five components - can't check reconstruction"
    rebuilt = sum(full[c] * w for c, w in TPI_WEIGHTS.items()) + full["momentum"]
    assert np.allclose(rebuilt, full["final"], atol=0.5)
