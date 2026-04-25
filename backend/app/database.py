from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Non-FastAPI helper to get a db session."""
    return SessionLocal()


def init_db():
    """Initialize database tables from models."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine, checkfirst=True)