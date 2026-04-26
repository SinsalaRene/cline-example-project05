import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI async dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_session():
    """Get a synchronous database session for non-async contexts."""
    import sqlalchemy
    sync_engine = create_async_engine(
        settings.DATABASE_URL.replace("asyncpg", "psycopg2"),
        pool_pre_ping=True,
    )
    Session = async_sessionmaker(sync_engine, expire_on_commit=False)
    return Session()


async def init_db():
    """Initialize database tables from models."""
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_test_db():
    """Get a test database session (for pytest)."""
    async with AsyncSessionLocal() as session:
        yield session