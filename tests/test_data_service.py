"""
Integration tests for the data_service read layer.

These hit the real database, so they're integration tests (conftest skips them
when the DB is down). Run from the project root:  pytest -v
"""
import pandas as pd
import pytest

from db import data_service


# Every get_* function paired with a readable id. Add new queries here.
GETTERS = [
    ("co2_urban_by_income",    data_service.get_co2_urban_by_income),
    ("density_vs_co2",         data_service.get_density_vs_co2),
    ("urban_vs_air_pollution", data_service.get_urban_vs_air_pollution),
    ("top_reducers",           data_service.get_top_reducers),
    ("decade_change",          data_service.get_decade_change),
    ("emissions_peak",         data_service.get_emissions_peak),
    ("fake_decoupler_board",   data_service.get_fake_decoupler_board),
    ("consumption_gap",        data_service.get_consumption_gap),
    ("subregion_rankings",     data_service.get_subregion_rankings),
    ("grid_cleanliness",       data_service.get_grid_cleanliness),
    ("decoupling_index_2000",  lambda: data_service.get_decoupling_index(2000)),
    ("decoupling_index_1990",  lambda: data_service.get_decoupling_index(1990)),
]


# Pattern 1 - smoke across all queries: each one executes and returns a frame
# with columns. This is the pytest version of the __main__ block: if any .sql
# breaks, exactly that parametrised case fails (and names itself).
@pytest.mark.parametrize("getter", [g for _, g in GETTERS], ids=[n for n, _ in GETTERS])
def test_query_executes_and_returns_frame(getter):
    df = getter()
    assert isinstance(df, pd.DataFrame)
    assert df.shape[1] > 0          # has columns, even if zero rows


# Pattern 2 - schema: a query exposes the columns the dashboard will rely on.
def test_top_reducers_has_expected_columns():
    df = data_service.get_top_reducers()
    assert {"country", "year", "co2_per_capita", "reduction"} <= set(df.columns)


# Pattern 3 - domain rule: top_reducers is capped at 10 by its LIMIT.
def test_top_reducers_capped_at_ten():
    assert len(data_service.get_top_reducers()) <= 10


# Pattern 4 - parameter behaviour: the 1990 base drops post-Soviet countries with
# no 1990 row, so it returns no more rows than the 2000 base.
def test_decoupling_1990_base_not_larger_than_2000():
    rows_2000 = len(data_service.get_decoupling_index(2000))
    rows_1990 = len(data_service.get_decoupling_index(1990))
    assert rows_1990 <= rows_2000
