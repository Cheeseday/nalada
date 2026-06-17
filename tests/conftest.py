"""
Shared pytest setup.

The data_service tests are *integration* tests - they run real SQL against the
Postgres DB. This conftest:
  1. puts the project root on sys.path (so `from db... import` works under pytest), and
  2. skips every test if the database isn't reachable, so the suite degrades
     gracefully on a machine without the DB instead of erroring out.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import text

from db.database import engine

_db_ok = None


def _db_available() -> bool:
    """True if the DB answers a trivial query. Cached after the first check."""
    global _db_ok
    if _db_ok is None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _db_ok = True
        except Exception:
            _db_ok = False
    return _db_ok


@pytest.fixture(autouse=True)
def require_db():
    """Skip any test that needs the database when it isn't reachable."""
    if not _db_available():
        pytest.skip("Database not reachable - skipping integration tests")
