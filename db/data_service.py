"""
Read layer between the database and the app: load each db/queries/*.sql and
expose one get_*() per query returning a DataFrame. Smoke test: python -m db.data_service
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from db.database import engine

logger = logging.getLogger(__name__)
QUERIES_DIR = Path(__file__).parent / "queries"


def _load_sql(name: str) -> str:
    """Read a query file from db/queries/ by stem name (without the .sql)."""
    path = QUERIES_DIR / f"{name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"Query not found: {path}")
    # utf-8 is required - the query comments use ₂, ≈, → etc.
    return path.read_text(encoding="utf-8")


def _run(name: str, **params) -> pd.DataFrame:
    """Load <name>.sql, execute it with optional bind params, return a DataFrame."""
    sql = _load_sql(name)
    df = pd.read_sql_query(text(sql), engine, params=params or None)
    logger.debug("Query '%s' returned %d rows", name, len(df))
    return df


def get_co2_urban_by_income() -> pd.DataFrame:
    """Avg CO₂/capita + avg urban % by World Bank income group (global)."""
    return _run("co2_urban_by_income")


def get_density_vs_co2() -> pd.DataFrame:
    """Per-country latest density vs latest CO₂/capita, with income group (global)."""
    return _run("density_vs_co2_by_income")


def get_urban_vs_air_pollution() -> pd.DataFrame:
    """Per-country latest urban % vs PM2.5 exposure (European correlation ≈ -0.534)."""
    return _run("urban_vs_air_pollution")


def get_gdp_vs_co2() -> pd.DataFrame:
    """Per-country GDP/capita vs territorial CO₂/capita, latest shared year, by income group (global; NB05 r≈0.74)."""
    return _run("gdp_vs_co2")


def get_top_reducers() -> pd.DataFrame:
    """Top 10 European countries by % CO₂/capita reduction over the last 10 years."""
    return _run("top_reducers")


def get_decade_change() -> pd.DataFrame:
    """Decade-over-decade CO₂/capita change per country (2000 / 2010 / 2020)."""
    return _run("decade_change")


def get_emissions_peak() -> pd.DataFrame:
    """Each country's peak-emissions year and how far below it sits today."""
    return _run("emissions_peak")


def get_fake_decoupler_board() -> pd.DataFrame:
    """European countries ranked by trade_co2_share (share of imported emissions)."""
    return _run("fake_decoupler_board")


def get_decoupler_class() -> pd.DataFrame:
    """Canonical genuine/fake/net_exporter verdicts per country (NB04)."""
    return _run("decoupler_class")


def get_consumption_gap() -> pd.DataFrame:
    """Gap between consumption and territorial CO₂/capita, ranked (honest vs flattering)."""
    return _run("gap_co2_per_capita")


def get_decoupling_index(base_year: int = 2000) -> pd.DataFrame:
    """GDP vs CO₂ index relative to base_year (2000 headline, 1990 Soviet contrast), per country."""
    return _run("decoupling_index", base_year=base_year)


def get_subregion_rankings() -> pd.DataFrame:
    """Rank each country's CO₂/capita within its UN M49 European subregion."""
    return _run("subregions_co2_pc")


def get_grid_cleanliness() -> pd.DataFrame:
    """European countries ranked by energy carbon intensity (cleanest first)."""
    return _run("grid_cleanliness")


def get_city_cars_snapshot(snap_year: int = 2018) -> pd.DataFrame:
    """Per-city cars/1000 + population + decoupling verdict (best-coverage year)."""
    return _run("city_cars_snapshot", snap_year=snap_year)


def get_city_cars_by_country(snap_year: int = 2018) -> pd.DataFrame:
    """Median cars/1000 per European country, tagged with decoupling verdict."""
    return _run("city_cars_by_country", snap_year=snap_year)


def get_tpi_leaderboard(base_year: int = 2000) -> pd.DataFrame:
    """TPI leaderboard (NB08), ranked by final score. base_year 2000 = headline, 1990 = contrast."""
    return _run("tpi_scores", base_year=base_year)


def get_tpi_sufficiency() -> pd.DataFrame:
    """Actual vs required annual pace of consumption-CO₂/capita cuts for the TPI top-12 (2000 base)."""
    return _run("tpi_sufficiency")


if __name__ == "__main__":
    # Smoke test: run every query, report row/col counts, catch per-query errors.
    logging.basicConfig(level=logging.INFO)

    checks = [
        ("co2_urban_by_income",       get_co2_urban_by_income),
        ("density_vs_co2",            get_density_vs_co2),
        ("urban_vs_air_pollution",    get_urban_vs_air_pollution),
        ("gdp_vs_co2",                get_gdp_vs_co2),
        ("top_reducers",              get_top_reducers),
        ("decade_change",             get_decade_change),
        ("emissions_peak",            get_emissions_peak),
        ("fake_decoupler_board",      get_fake_decoupler_board),
        ("decoupler_class",           get_decoupler_class),
        ("consumption_gap",           get_consumption_gap),
        ("decoupling_index (2000)",   lambda: get_decoupling_index(2000)),
        ("decoupling_index (1990)",   lambda: get_decoupling_index(1990)),
        ("subregion_rankings",        get_subregion_rankings),
        ("grid_cleanliness",          get_grid_cleanliness),
        ("city_cars_by_country",      get_city_cars_by_country),
        ("city_cars_snapshot",        get_city_cars_snapshot),
        ("tpi_leaderboard (2000)",    lambda: get_tpi_leaderboard(2000)),
        ("tpi_leaderboard (1990)",    lambda: get_tpi_leaderboard(1990)),
        ("tpi_sufficiency",           get_tpi_sufficiency),
    ]

    failures = 0
    for label, func in checks:
        try:
            df = func()
            print(f"OK   {label:28s} {df.shape[0]:>4} rows x {df.shape[1]} cols")
        except Exception as e:
            failures += 1
            print(f"FAIL {label:28s} {type(e).__name__}: {e}")

    print(f"\n{len(checks) - failures}/{len(checks)} queries OK")
