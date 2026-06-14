"""
Backfill country classifications (income group + region) into `countries`.

The OWID loader seeds `countries` with name + iso_code only - continent, region
and income_group are stubbed NULL (see owid_loader.transform). This step fills:
  - income_group, region : from the World Bank's official economy metadata
  - subregion            : from a hardcoded UN M49 European map (WB has no
                           within-Europe granularity)
all keyed by ISO-3 code.

Run *after* the OWID loader (which creates the country rows). One-shot backfill:
    python -m etl.country_enrichment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
import wbgapi as wb
from sqlalchemy.orm import Session

from db.database import engine
from db.models import Country

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INCOME_LABELS = {
    'HIC': 'High income',
    'UMC': 'Upper middle income',
    'LMC': 'Lower middle income',
    'LIC': 'Low income',
    'INX': 'Not classified',
}

# UN M49 European sub-regions. World Bank lumps all of Europe into one region
# ("Europe & Central Asia"), so this hardcoded map gives the balanced
# Northern/Western/Eastern/Southern split for within-Europe peer grouping.
# Note: UN M49 actually files Cyprus and Georgia under *Western Asia*; they are
# placed here pragmatically (this project treats them as European) - CYP with
# Southern Europe, GEO with Eastern Europe
EUROPE_SUBREGION = {
    # Northern Europe
    'DNK': 'Northern Europe', 'EST': 'Northern Europe', 'FIN': 'Northern Europe',
    'ISL': 'Northern Europe', 'IRL': 'Northern Europe', 'LVA': 'Northern Europe',
    'LTU': 'Northern Europe', 'NOR': 'Northern Europe', 'SWE': 'Northern Europe',
    'GBR': 'Northern Europe',
    # Western Europe
    'AUT': 'Western Europe', 'BEL': 'Western Europe', 'FRA': 'Western Europe',
    'DEU': 'Western Europe', 'LIE': 'Western Europe', 'LUX': 'Western Europe',
    'MCO': 'Western Europe', 'NLD': 'Western Europe', 'CHE': 'Western Europe',
    # Eastern Europe
    'BLR': 'Eastern Europe', 'BGR': 'Eastern Europe', 'CZE': 'Eastern Europe',
    'HUN': 'Eastern Europe', 'MDA': 'Eastern Europe', 'POL': 'Eastern Europe',
    'ROU': 'Eastern Europe', 'RUS': 'Eastern Europe', 'SVK': 'Eastern Europe',
    'UKR': 'Eastern Europe', 'GEO': 'Eastern Europe',  # GEO: UN M49 = Western Asia
    # Southern Europe
    'ALB': 'Southern Europe', 'AND': 'Southern Europe', 'BIH': 'Southern Europe',
    'HRV': 'Southern Europe', 'GRC': 'Southern Europe', 'ITA': 'Southern Europe',
    'MLT': 'Southern Europe', 'MNE': 'Southern Europe', 'MKD': 'Southern Europe',
    'PRT': 'Southern Europe', 'SMR': 'Southern Europe', 'SRB': 'Southern Europe',
    'SVN': 'Southern Europe', 'ESP': 'Southern Europe', 'XKX': 'Southern Europe',
    'CYP': 'Southern Europe',  # CYP: UN M49 = Western Asia
}


def fetch_classifications() -> pd.DataFrame:
    """
    Pull income level + region per economy from the World Bank.
    Returns a frame: iso_code, region, income_group (human-readable labels).
    """
    logger.info("Fetching World Bank economy metadata...")
    econ = wb.economy.DataFrame()                 # index = ISO-3 code

    for col in ('region', 'incomeLevel', 'aggregate'):
        if col not in econ.columns:
            logger.warning(
                f"Expected column '{col}' missing; got {list(econ.columns)}"
            )

    if 'aggregate' in econ.columns:
        econ = econ[~econ['aggregate']]

    try:
        region_labels = wb.region.Series().to_dict()
    except Exception as e:
        logger.warning(f"Region label lookup failed ({e}); storing region codes")
        region_labels = {}

    econ = econ.copy()
    econ['region'] = econ['region'].map(region_labels).fillna(econ['region'])
    econ['income_group'] = econ['incomeLevel'].map(INCOME_LABELS).fillna(econ['incomeLevel'])
    econ['iso_code'] = econ.index

    out = econ[['iso_code', 'region', 'income_group']].reset_index(drop=True)
    logger.info(f"  -> {len(out)} economies classified")
    return out


def update_countries(class_df: pd.DataFrame, session: Session) -> None:
    """
    Write region + income_group (World Bank) and subregion (UN M49) onto
    existing country rows, matched by iso_code.
    """
    countries = {c.iso_code: c for c in session.query(Country).all()}
    logger.info(f"Countries in DB to enrich: {len(countries)}")

    classified = {row['iso_code']: row for _, row in class_df.iterrows()}

    wb_updated = 0
    sub_updated = 0
    for iso_code, country in countries.items():
        row = classified.get(iso_code)
        if row is not None:
            country.region = row['region'] if pd.notna(row['region']) else None
            country.income_group = row['income_group'] if pd.notna(row['income_group']) else None
            wb_updated += 1

        subregion = EUROPE_SUBREGION.get(iso_code)
        if subregion is not None:
            country.subregion = subregion
            sub_updated += 1

    logger.info(f"World Bank region/income set: {wb_updated}")
    logger.info(f"UN M49 subregion set: {sub_updated}")

    missing = sorted(iso for iso, c in countries.items() if c.income_group is None)
    if missing:
        logger.warning(f"Still no income_group ({len(missing)}): {missing}")


def run():
    logger.info("Country enrichment started")
    class_df = fetch_classifications()

    with Session(engine) as session:
        try:
            update_countries(class_df, session)
            session.commit()
            logger.info("Country enrichment complete")
        except Exception as e:
            session.rollback()
            logger.error(f"Enrichment failed, rolled back: {e}")
            raise


if __name__ == "__main__":
    run()
