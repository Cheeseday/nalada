import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db.database import engine
from db.models import Country, Emission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OWID_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
LOCAL_PATH = os.path.join(os.path.dirname(__file__), "../data/owid-co2-data.csv")

# Columns to extract from OWID - mapped to our schema
EMISSION_COLUMNS = [
    'iso_code', 'year',
    'co2', 'co2_per_capita', 'co2_per_gdp',
    'consumption_co2', 'consumption_co2_per_capita', 'consumption_co2_per_gdp',
    'energy_per_capita', 'energy_per_gdp', 'co2_per_unit_energy',
    'coal_co2', 'gas_co2', 'oil_co2', 'methane', 'ghg_per_capita',
    'trade_co2', 'trade_co2_share',
    'temperature_change_from_co2', 'share_of_temperature_change_from_ghg',
    'gdp', 'population',
]

def extract() -> pd.DataFrame:
    """Load OWID CSV - local file first, fallback to URL."""
    if os.path.exists(LOCAL_PATH):
        logger.info("Loading from local file...")
        df = pd.read_csv(LOCAL_PATH)
    else:
        logger.info("Local file not found, downloading from OWID GitHub...")
        df = pd.read_csv(OWID_URL)
        # Save locally for future runs
        os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
        df.to_csv(LOCAL_PATH, index=False)
        logger.info(f"Saved to {LOCAL_PATH}")

    logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean and reshape raw OWID data.
    Returns: (countries_df, emissions_df)
    """

    # 1. Filter out non-countries
    # - rows without iso_code are regional aggregates (World, Asia, etc.)
    # - rows with OWID_ prefix are custom OWID aggregates
    df = df[df['iso_code'].notna()].copy()
    df = df[~df['iso_code'].str.startswith('OWID')]
    logger.info(f"After filtering non-countries: {len(df)} rows")

    # 2. Validate required columns exist
    missing = [c for c in EMISSION_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in OWID data: {missing}")

    # 3. Extract unique countries
    countries_df = (
        df[['country', 'iso_code']]
        .drop_duplicates(subset='iso_code')
        .rename(columns={'country': 'name'})
        .assign(continent=None, region=None, income_group=None)
        .reset_index(drop=True)
    )
    logger.info(f"Unique countries found: {len(countries_df)}")

    # 4. Build emissions DataFrame
    emissions_df = df[EMISSION_COLUMNS].copy()
    emissions_df = emissions_df.rename(columns={'co2': 'co2_total'})
    emissions_df = emissions_df.reset_index(drop=True)
    logger.info(f"Emission rows to load: {len(emissions_df)}")

    return countries_df, emissions_df


def safe_float(value) -> float | None:
    """Convert value to float, return None if NaN or invalid."""
    try:
        return None if pd.isna(value) else float(value)
    except (TypeError, ValueError):
        return None


def load_countries(countries_df: pd.DataFrame, session: Session) -> dict[str, int]:
    """
    Upsert countries - insert new, skip existing.
    Returns: {iso_code: country_id}
    """
    for _, row in countries_df.iterrows():
        stmt = insert(Country).values(
            name=row['name'],
            iso_code=row['iso_code'],
            continent=row['continent'],
            region=row['region'],
            income_group=row['income_group'],
        ).on_conflict_do_nothing(index_elements=['iso_code'])
        session.execute(stmt)

    session.flush()

    iso_to_id = {c.iso_code: c.id for c in session.query(Country).all()}
    logger.info(f"Countries in DB: {len(iso_to_id)}")
    return iso_to_id


def load_emissions(
    emissions_df: pd.DataFrame,
    iso_to_id: dict[str, int],
    session: Session
) -> None:
    """
    Batch insert emissions - skip duplicates via UniqueConstraint.
    """
    records = []
    skipped = 0

    for _, row in emissions_df.iterrows():
        country_id = iso_to_id.get(row['iso_code'])
        if not country_id:
            skipped += 1
            continue

        records.append({
            'country_id': country_id,
            'year': int(row['year']),
            'co2_total':                          safe_float(row['co2_total']),
            'co2_per_capita':                     safe_float(row['co2_per_capita']),
            'co2_per_gdp':                        safe_float(row['co2_per_gdp']),
            'consumption_co2':                    safe_float(row['consumption_co2']),
            'consumption_co2_per_capita':         safe_float(row['consumption_co2_per_capita']),
            'consumption_co2_per_gdp':            safe_float(row['consumption_co2_per_gdp']),
            'energy_per_capita':                  safe_float(row['energy_per_capita']),
            'energy_per_gdp':                     safe_float(row['energy_per_gdp']),
            'co2_per_unit_energy':                safe_float(row['co2_per_unit_energy']),
            'coal_co2':                           safe_float(row['coal_co2']),
            'gas_co2':                            safe_float(row['gas_co2']),
            'oil_co2':                            safe_float(row['oil_co2']),
            'methane':                            safe_float(row['methane']),
            'ghg_per_capita':                     safe_float(row['ghg_per_capita']),
            'trade_co2':                          safe_float(row['trade_co2']),
            'trade_co2_share':                    safe_float(row['trade_co2_share']),
            'temperature_change_from_co2':        safe_float(row['temperature_change_from_co2']),
            'share_of_temperature_change_from_ghg': safe_float(row['share_of_temperature_change_from_ghg']),
            'gdp':                                safe_float(row['gdp']),
            'population':                         safe_float(row['population']),
            'source': 'OWID',
        })

    if records:
        stmt = insert(Emission).values(records).on_conflict_do_nothing(
            index_elements=['country_id', 'year']
        )
        session.execute(stmt)

    logger.info(f"Emissions loaded: {len(records)}, skipped (unknown iso): {skipped}")


def run():
    logger.info("OWID Loader started")

    df = extract()
    countries_df, emissions_df = transform(df)

    with Session(engine) as session:
        try:
            iso_to_id = load_countries(countries_df, session)
            load_emissions(emissions_df, iso_to_id, session)
            session.commit()
            logger.info("OWID Loader complete")
        except Exception as e:
            session.rollback()
            logger.error(f"ETL failed, rolled back: {e}")
            raise


if __name__ == "__main__":
    run()