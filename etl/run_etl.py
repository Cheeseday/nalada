import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
from etl.owid_loader import run as run_owid
from etl.country_enrichment import run as run_enrichment
from etl.worldbank_loader import run as run_worldbank
from etl.eurostat_loader import run as run_eurostat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=== Starting full ETL pipeline ===")
    start = time.time()
    
    steps = [
        ("OWID CO2 data",        run_owid),
        ("Country enrichment",   run_enrichment),
        ("World Bank data",      run_worldbank),
        ("Eurostat cities",      run_eurostat),
    ]

    for step_name, step_fn in steps:
        logger.info(f"--- {step_name} ---")
        step_start = time.time()
        try:
            step_fn()
            elapsed = round(time.time() - step_start, 2)
            logger.info(f"--- {step_name} complete in {elapsed}s ---")
        except Exception as e:
            logger.error(f"--- {step_name} FAILED: {e} ---")
            raise

    total = round(time.time() - start, 2)
    logger.info(f"=== ETL pipeline complete in {total}s ===")


if __name__ == "__main__":
    run_pipeline()