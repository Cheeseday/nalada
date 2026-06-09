import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db.database import engine
from db.models import Country, City, CityStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ISO2 (Eurostat) -> ISO3 (our DB)
ISO2_TO_ISO3 = {
    'AT': 'AUT', 'BE': 'BEL', 'BG': 'BGR', 'HR': 'HRV', 'CY': 'CYP',
    'CZ': 'CZE', 'DK': 'DNK', 'EE': 'EST', 'FI': 'FIN', 'FR': 'FRA',
    'DE': 'DEU', 'EL': 'GRC', 'HU': 'HUN', 'IE': 'IRL', 'IT': 'ITA',
    'LV': 'LVA', 'LT': 'LTU', 'LU': 'LUX', 'MT': 'MLT', 'NL': 'NLD',
    'PL': 'POL', 'PT': 'PRT', 'RO': 'ROU', 'SK': 'SVK', 'SI': 'SVN',
    'ES': 'ESP', 'SE': 'SWE', 'UK': 'GBR', 'NO': 'NOR', 'CH': 'CHE',
    'AL': 'ALB', 'BY': 'BLR', 'GE': 'GEO', 'UA': 'UKR',
}

# Eurostat indicator codes -> our column names
TRAN_INDICATORS = {
    'TT1057I': 'cars_per_1000',
    'TT1079V': 'bicycle_network_km',
    'TT1019V': 'avg_journey_to_work_min',
    'TT1080V': 'public_transport_cost_eur',
}

ENV_INDICATORS = {
    'EN5205V': 'green_urban_area_pct',
    'EN4008V': 'municipal_waste_1000t',
    'EN3011V': 'wastewater_treatment_pct',
    'EN5202V': 'industrial_land_pct',
}


def _get_year_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).startswith(('19', '20')) and str(c).isdigit()]


def _find_col(df: pd.DataFrame, prefix: str) -> str | None:
    """Find the first string column whose values start with prefix."""
    for col in df.select_dtypes('object').columns:
        vals = df[col].dropna().head(20).astype(str)
        if vals.str.startswith(prefix).any():
            return col
    return None


def _find_city_col(df: pd.DataFrame) -> str | None:
    for col in df.select_dtypes('object').columns:
        vals = df[col].dropna().head(20).astype(str)
        # city code: 2 letters + 3 digits + 1 letter
        if vals.str.match(r'^[A-Z]{2}\d{3}[A-Z]$').any():
            return col
    return None


def extract_population(eurostat) -> pd.DataFrame:
    # DATAFRAME: city_code | name | iso2 | population
    # One row per core city (type='C'), population = latest non-null year.
    logger.info("Fetching urb_cpop1 (city populations)...")
    raw = eurostat.get_data_df('urb_cpop1')
    df  = raw.reset_index()

    city_col  = _find_city_col(df)
    indic_col = _find_col(df, 'POP')  # population indicator codes start with POP
    year_cols = _get_year_cols(df)

    if not city_col:
        raise ValueError("Cannot find city code column in urb_cpop1")

    logger.info(f"  city_col={city_col}, indic_col={indic_col}, years={len(year_cols)}")

    # Core cities only
    df['_city_code'] = df[city_col].astype(str)
    df = df[df['_city_code'].str.endswith('C')].copy()

    # Total resident population indicator: POP1001I (usually)
    if indic_col:
        pop_total = df[df[indic_col] == 'POP1001I'].copy()
        if pop_total.empty:
            pop_total = df[df[indic_col].str.startswith('POP', na=False)].copy()
    else:
        pop_total = df.copy()

    # Latest population = last non-null year value per city
    if year_cols and not pop_total.empty:
        pop_total['population'] = pop_total[year_cols].apply(
            lambda row: row.dropna().iloc[-1] if row.dropna().size else None, axis=1
        )
    else:
        pop_total['population'] = None

    # Get city names via eurostat dictionary
    try:
        city_dict = eurostat.get_dic('urb_cpop1', 'cities', full=False)
        pop_total['name'] = pop_total['_city_code'].map(city_dict)
    except Exception:
        logger.warning("  Could not fetch city name dictionary - names will be None")
        pop_total['name'] = None

    pop_total['iso2'] = pop_total['_city_code'].str[:2]

    result = (
        pop_total[['_city_code', 'name', 'iso2', 'population']]
        .rename(columns={'_city_code': 'city_code'})
        .drop_duplicates(subset='city_code')
        .reset_index(drop=True)
    )

    # Filter to known European countries only
    result = result[result['iso2'].isin(ISO2_TO_ISO3.keys())].copy()
    result['iso3'] = result['iso2'].map(ISO2_TO_ISO3)

    logger.info(f"  Core cities extracted: {len(result)}")
    return result


def extract_indicators(eurostat, dataset: str, indicators: dict[str, str]) -> pd.DataFrame:
    # Fetch a Eurostat urban dataset and pivot it to wide format:
    # city_code | year | col1 | col2 | ...
    logger.info(f"Fetching {dataset} ({len(indicators)} indicators)...")
    raw = eurostat.get_data_df(dataset)
    df  = raw.reset_index()

    city_col  = _find_city_col(df)
    indic_col = _find_col(df, list(indicators.keys())[0][:2])
    year_cols = _get_year_cols(df)

    if not city_col or not indic_col:
        logger.warning(f"  Could not find required columns in {dataset} - skipping")
        return pd.DataFrame()

    logger.info(f"  city_col={city_col}, indic_col={indic_col}, years={len(year_cols)}")

    # Core cities in known countries only
    df['_city_code'] = df[city_col].astype(str)
    df = df[
        df['_city_code'].str.endswith('C') &
        df['_city_code'].str[:2].isin(ISO2_TO_ISO3.keys())
    ].copy()

    # Melt years to long format
    id_cols = ['_city_code', indic_col]
    long = df[id_cols + year_cols].melt(
        id_vars=id_cols, var_name='year', value_name='value'
    )
    long['year'] = long['year'].astype(int)
    long = long.dropna(subset=['value'])

    # Filter to our indicators only
    long = long[long[indic_col].isin(indicators.keys())].copy()
    long['column'] = long[indic_col].map(indicators)

    # Pivot to wide: one row per city per year
    wide = long.pivot_table(
        index=['_city_code', 'year'],
        columns='column',
        values='value',
        aggfunc='first'
    ).reset_index().rename(columns={'_city_code': 'city_code'})

    wide.columns.name = None
    logger.info(f"  Rows extracted: {len(wide)}, cities: {wide['city_code'].nunique()}")
    return wide


def load(cities_df: pd.DataFrame, tran_df: pd.DataFrame,
         env_df: pd.DataFrame, session: Session) -> None:

    # Build lookup: iso3 -> country.id
    iso3_to_id = {c.iso_code: c.id for c in session.query(Country).all()}

    # --- Load cities ---
    city_records = []
    for _, row in cities_df.iterrows():
        country_id = iso3_to_id.get(row['iso3'])
        if not country_id:
            continue
        city_records.append({
            'city_code':  row['city_code'],
            'name':       row['name'] if pd.notna(row.get('name')) else None,
            'country_id': country_id,
            'population': float(row['population']) if pd.notna(row.get('population')) else None,
        })

    if city_records:
        stmt = insert(City).values(city_records).on_conflict_do_nothing(
            index_elements=['city_code']
        )
        session.execute(stmt)
        session.flush()
        logger.info(f"Cities inserted/skipped: {len(city_records)}")

    # Build lookup: city_code -> city.id
    code_to_id = {c.city_code: c.id for c in session.query(City).all()}

    # --- Merge transport + environment by city_code + year ---
    if not tran_df.empty and not env_df.empty:
        stats_df = pd.merge(tran_df, env_df, on=['city_code', 'year'], how='outer')
    elif not tran_df.empty:
        stats_df = tran_df.copy()
    elif not env_df.empty:
        stats_df = env_df.copy()
    else:
        logger.warning("No indicator data to load")
        return

    # --- Load city_stats ---
    all_cols = (
        list(TRAN_INDICATORS.values()) +
        list(ENV_INDICATORS.values())
    )

    def safe_float(val):
        try:
            return None if pd.isna(val) else float(val)
        except (TypeError, ValueError):
            return None

    stat_records = []
    for _, row in stats_df.iterrows():
        city_id = code_to_id.get(row['city_code'])
        if not city_id:
            continue

        values = {col: safe_float(row.get(col)) for col in all_cols}
        # Skip rows where every indicator is null
        if all(v is None for v in values.values()):
            continue

        stat_records.append({
            'city_id': city_id,
            'year':    int(row['year']),
            **values,
            'source':  'Eurostat',
        })

    if stat_records:
        stmt = insert(CityStats).values(stat_records).on_conflict_do_nothing(
            index_elements=['city_id', 'year']
        )
        session.execute(stmt)
        logger.info(f"CityStats rows inserted/skipped: {len(stat_records)}")


def run():
    try:
        import eurostat
    except ImportError:
        logger.error("eurostat package not installed. Run: pip install eurostat")
        raise

    logger.info("Eurostat Loader started")

    cities_df = extract_population(eurostat)
    tran_df   = extract_indicators(eurostat, 'urb_ctran', TRAN_INDICATORS)
    env_df    = extract_indicators(eurostat, 'urb_cenv',  ENV_INDICATORS)

    with Session(engine) as session:
        try:
            load(cities_df, tran_df, env_df, session)
            session.commit()
            logger.info("Eurostat Loader complete")
        except Exception as e:
            session.rollback()
            logger.error(f"ETL failed, rolled back: {e}")
            raise


if __name__ == "__main__":
    run()
