import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
import wbgapi as wb
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db.database import engine
from db.models import Country, Urbanization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDICATORS = {
    'SP.URB.TOTL.IN.ZS': 'urban_population_pct',
    'SP.URB.GROW':        'urban_growth_rate',
    'EN.POP.DNST':        'population_density',
    'SP.URB.TOTL':        'urban_population_total',
    'EN.ATM.PM25.MC.M3':  'pm25_exposure',
    'EN.POP.SLUM.UR.ZS':  'slum_population_pct',
    'EG.ELC.ACCS.UR.ZS':  'electricity_access_pct',
}


def extract() -> dict[str, pd.DataFrame]:
    raw = {}
    for code, col_name in INDICATORS.items():
        logger.info(f"Fetching {col_name} ({code})...")
        try:
            df = wb.data.DataFrame(code)
            raw[col_name] = df
            logger.info(f"  → {df.shape[0]} economies, {df.shape[1]} years")
        except Exception as e:
            logger.warning(f" - Failed to fetch {code}: {e}")
    return raw


def reshape_indicator(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    df = df.reset_index()
    df = df.rename(columns={'economy': 'iso_code'})

    # Melt: years as columns - one row per country/year
    df = df.melt(
        id_vars='iso_code',
        var_name='year',
        value_name=col_name
    )

    # Clean year
    df['year'] = df['year'].str.replace('YR', '').astype(int)

    df = df.dropna(subset=[col_name])

    return df[['iso_code', 'year', col_name]]


def transform(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    combined = None

    for col_name, df in raw.items():
        logger.info(f"Reshaping {col_name}...")
        long_df = reshape_indicator(df, col_name)
        logger.info(f"  - {len(long_df)} non-null rows")

        if combined is None:
            combined = long_df
        else:
            combined = combined.merge(
                long_df,
                on=['iso_code', 'year'],
                how='outer'
            )

    logger.info(f"Combined shape: {combined.shape}")
    logger.info(f"Years range: {combined['year'].min()} - {combined['year'].max()}")
    logger.info(f"Unique countries: {combined['iso_code'].nunique()}")

    return combined


def safe_float(value) -> float | None:
    "Convert to float, return None if NaN or invalid."
    try:
        return None if pd.isna(value) else float(value)
    except (TypeError, ValueError):
        return None


def load_urbanization(
    combined_df: pd.DataFrame,
    session: Session
) -> None:
    "Insert urbanization rows - skip duplicates, skip unknown countries."
    # Build iso - id map from existing countries
    iso_to_id = {c.iso_code: c.id for c in session.query(Country).all()}
    logger.info(f"Countries available for matching: {len(iso_to_id)}")

    records = []
    skipped_unknown = 0
    skipped_no_data = 0

    for _, row in combined_df.iterrows():
        country_id = iso_to_id.get(row['iso_code'])
        if not country_id:
            skipped_unknown += 1
            continue

        values = [
            safe_float(row.get('urban_population_pct')),
            safe_float(row.get('urban_growth_rate')),
            safe_float(row.get('population_density')),
            safe_float(row.get('urban_population_total')),
            safe_float(row.get('pm25_exposure')),
            safe_float(row.get('slum_population_pct')),
            safe_float(row.get('electricity_access_pct')),
        ]
        if all(v is None for v in values):
            skipped_no_data += 1
            continue

        records.append({
            'country_id':               country_id,
            'year':                     int(row['year']),
            'urban_population_pct':     values[0],
            'urban_growth_rate':        values[1],
            'population_density':       values[2],
            'urban_population_total':   values[3],
            'pm25_exposure':            values[4],
            'slum_population_pct':      values[5],
            'electricity_access_pct':   values[6],
            'source':                   'WorldBank',
        })

    if records:
        stmt = insert(Urbanization).values(records).on_conflict_do_nothing(
            index_elements=['country_id', 'year']
        )
        session.execute(stmt)

    logger.info(f"Urbanization loaded: {len(records)}")
    logger.info(f"Skipped - unknown country: {skipped_unknown}")
    logger.info(f"Skipped - all values null: {skipped_no_data}")

def run():
    logger.info("World Bank Loader started")

    raw = extract()
    combined_df = transform(raw)

    with Session(engine) as session:
        try:
            load_urbanization(combined_df, session)
            session.commit()
            logger.info("World Bank Loader complete")
        except Exception as e:
            session.rollback()
            logger.error(f"ETL failed, rolled back: {e}")
            raise


if __name__ == "__main__":
    run()