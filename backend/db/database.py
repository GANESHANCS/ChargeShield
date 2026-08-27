"""
Database Engine and Session Configuration for ChargeShield Risk Operations Backend.
Supports persistent SQLite storage for human review states and decision audit records,
and production PostgreSQL connection pooling and session lifecycle management.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from backend.core.config import settings
from backend.core.logging import logger

# Configure database engine connection options for SQLite vs PostgreSQL
engine_kwargs = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production PostgreSQL pool configuration
    engine_kwargs["pool_size"] = 15
    engine_kwargs["max_overflow"] = 25
    engine_kwargs["pool_recycle"] = 1800  # Recycle connections after 30 mins
    engine_kwargs["pool_timeout"] = 30    # Timeout waiting for pool connection

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes all database tables created via SQLAlchemy metadata."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database schema initialized successfully for '{settings.DATABASE_URL.split('@')[-1]}'.")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager providing a transactional SQLAlchemy DB session with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional DB session with rollback guarantee."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

