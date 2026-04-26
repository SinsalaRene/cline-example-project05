# Session 3: Database Migrations & Data Integrity

## Context

You are working on the Azure Firewall Manager application. Sessions 1-2 (Security & API) have been completed. Now we set up Alembic migrations, enhance data models, and improve data integrity.

## Project Structure (After Sessions 1-2)

```
cline-example-project05/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py            # Environment-based config
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── models.py            # SQLAlchemy models (TO ENHANCE)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── logging_config.py
│   │   ├── middleware/
│   │   ├── tasks/
│   │   ├── auth/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── firewalls.py
│   │   │   ├── approvals.py
│   │   │   ├── stats.py
│   │   │   └── export.py
│   │   └── services/
│   └── tests/
│   ├── alembic/                 # NEW: Migration directory
│   ├── scripts/                 # NEW: Helper scripts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
├── docker-compose.yml
└── .env.example
```

## Tasks

### Task 3.1: Alembic Setup

```bash
cd backend
alembic init alembic
```

Create `backend/alembic/env.py`:

```python
"""Alembic environment configuration."""
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base
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
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="migration.",
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
```

Create `backend/alembic/script.py.mako`:

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on or "None")}

def upgrade() -> None:
    """Upgrade migration."""
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    """Downgrade migration."""
    ${downgrades if downgrades else "pass"}
```

Create `backend/alembic.ini`:

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/firewall_manager
```

### Task 3.2: Enhanced Data Models (`backend/app/models.py`)

Add soft delete, versioning, and tracking:

```python
"""Enhanced SQLAlchemy models with soft delete and versioning."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, JSON, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY, INET
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.functions import now
from sqlalchemy.sql.schema import ForeignKeyConstraint

from app.database import Base
from app.config import RuleAction, RuleStatus, ApprovalStatus, ResourceCategory, WorkloadType


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_factory(context=None):
    return datetime.now(timezone.utc)


class _BaseMixin:
    """Mixin adding soft delete, versioning, and tracking."""
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, nullable=True, index=True
    )
    _version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_factory
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_factory, onupdate=utc_now_factory
    )
    external_id: Mapped[str | None] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }


class User(Base, _BaseMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    oidc_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), default="viewer")
    workload: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workload_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    rules = relationship("FirewallRule", back_populates="created_by_user")
    approvals = relationship("ApprovalRecord", back_populates="approver")


class Tag(Base, _BaseMixin):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    rules = relationship("TagRule", back_populates="tag")


class TagRule(Base, _BaseMixin):
    """Junction table for tags and rules."""
    __tablename__ = "tag_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id"), nullable=False)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("firewall_rules.id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("tag_id", "rule_id", name="uq_tag_rule"),
    )
    
    tag = relationship("Tag", back_populates="rules")
    rule = relationship("FirewallRule", back_populates="tags")


class FirewallRule(Base, _BaseMixin):
    __tablename__ = "firewall_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    landing_zone: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    firewall_policy: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule_collection_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=200)
    action: Mapped[str] = mapped_column(SAEnum(RuleAction), default=RuleAction.DENY)
    source_addresses: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    destination_addresses: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    destination_ports: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    destination_fqdns: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    protocols: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    category: Mapped[str] = mapped_column(SAEnum(ResourceCategory), default=ResourceCategory.NETWORK)
    workload: Mapped[str | None] = mapped_column(String(100), nullable=True)
    workload_type: Mapped[str | None] = mapped_column(SAEnum(WorkloadType), nullable=True)
    environment: Mapped[str] = mapped_column(String(20), default="development")
    status: Mapped[str] = mapped_column(SAEnum(RuleStatus), default=RuleStatus.DRAFT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Approval fields
    created_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    approved_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_for_approval_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_landing_zone_status", "landing_zone", "status"),
        Index("idx_workload_environment", "workload", "environment"),
        Index("idx_name_status", "name", "status"),
    )
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by_id])
    tags = relationship("TagRule", back_populates="rule")
    approvers = relationship("ApprovalRecord", back_populates="rule")


class ApprovalRecord(Base, _BaseMixin):
    __tablename__ = "approval_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("firewall_rules.id", ondelete="CASCADE"), nullable=False)
    approver_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approver_role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_rule_status", "rule_id", "status"),
    )
    
    rule = relationship("FirewallRule", back_populates="approvers")
    approver = relationship("User", foreign_keys=[approver_id], uselist=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_entity", "entity_type", "entity_id"),
        Index("idx_timestamp", "timestamp"),
    )
```

### Task 3.3: Generate Initial Migration

```bash
cd backend
alembic revision --autogenerate -m "Initial migration with enhanced models"
```

### Task 3.4: Seed Data Script (`backend/scripts/seed_data.py`)

```python
"""Seed data script for development environment."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import engine, Base
from app.models import User, FirewallRule, Tag, ApprovalRecord, AuditLog
from app.config import RuleAction, RuleStatus, ResourceCategory, ApprovalStatus


async def seed_data():
    """Seed the database with initial data."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        # Check if data already exists
        existing = await session.execute(select(User))
        if existing.first():
            print("Database already seeded, skipping...")
            return
        
        print("Seeding database...")
        
        # Create users
        users = [
            User(oidc_sub="dev-sub-001", email="admin@example.com",
                 display_name="Admin User", role="admin"),
            User(oidc_sub="dev-sub-002", email="security@example.com",
                 display_name="Security Reviewer", role="security_stakeholder"),
            User(oidc_sub="dev-sub-003", email="workload@example.com",
                 display_name="Workload Owner", role="workload_stakeholder"),
        ]
        session.add_all(users)
        await session.commit()
        
        # Create tags
        tags = [
            Tag(name="production", color="#ff0000"),
            Tag(name="staging", color="#ffaa00"),
            Tag(name="development", color="#00ff00"),
        ]
        session.add_all(tags)
        await session.commit()
        
        # Create a sample firewall rule
        rule = FirewallRule(
            name="Allow-HTTPS-Inbound",
            description="Allow HTTPS traffic from internet",
            landing_zone="corp",
            rule_collection_name="Corporate-Rules",
            priority=100,
            action=RuleAction.ALLOW,
            destination_ports=["443"],
            category=ResourceCategory.NETWORK,
            environment="production",
            status=RuleStatus.ACTIVE,
        )
        session.add(rule)
        await session.commit()
        
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
```

### Task 3.5: Update `docker-compose.yml`

Add migration service:

```yaml
  migration_runner:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fw-portal-migration
    command: >
      sh -c "
        cd /app &&
        alembic upgrade head &&
        python scripts/seed_data.py
      "
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fw_portal
    depends_on:
      db:
        condition: service_healthy
    networks:
      - fw-portal-net
    restart: "no"
```

## Testing

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "Initial migration"

# Test migration
alembic upgrade head

# Run seed script
python scripts/seed_data.py

# Verify
docker compose up db migration_runner -d
```

## Acceptance Criteria

- [ ] Alembic configuration is working
- [ ] Initial migration generates correctly
- [ ] Models include soft delete (`deleted_at`)
- [ ] Models include version tracking (`_version`)
- [ ] Models include `external_id` (UUID)
- [ ] Indexes are added for common query patterns
- [ ] Seed data script runs successfully
- [ ] Migration service starts in Docker Compose