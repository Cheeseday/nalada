import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import Config

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

engine = create_engine(
    Config.DATABASE_URL,
    echo=Config.DEBUG,        # SQL logs only in development
    pool_size=5,              # connection pool
    pool_pre_ping=True        # auto-reconnect if connection dropped
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    """Context manager for DB session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def check_connection():
    """Verify DB is reachable on startup"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise 
