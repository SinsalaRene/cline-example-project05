"""Alembic environment configuration."""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base, engine
from app.models import *  # noqa: F401 - Import all models

# Alembic config
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"cls": None},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using sync connection (sync context for alembic autogenerate)."""
    # Use asyncpg dialect directly since psycopg2 is not needed
    from sqlalchemy import create_engine
    sync_url = str(settings.DATABASE_URL).replace("asyncpg", "psycopg2") if "asyncpg" in str(settings.DATABASE_URL) else settings.DATABASE_URL
    
    # Fallback to using asyncpg directly
    connectable = create_engine(
        settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()