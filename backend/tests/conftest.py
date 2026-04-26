"""Pytest fixtures for backend testing."""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import get_pool_extension
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings, Environment
from app.database import Base
from app.main import app
from app.models import User, FirewallRule, Tag, ApprovalRecord
from app.schemas import RuleAction, RuleStatus, ResourceCategory, ApprovalStatus
from app.auth.auth import create_access_token


# Override settings for testing
@pytest.fixture(autouse=True)
def override_settings():
    """Override settings with test-specific values."""
    original_secret = settings.SECRET_KEY
    original_db = settings.DATABASE_URL
    original_env = settings.ENVIRONMENT
    original_debug = settings.DEBUG
    original_allowed_hosts = settings.ALLOWED_HOSTS
    settings.SECRET_KEY = "test-secret-key-for-testing-only-do-not-use-in-production"
    settings.DATABASE_URL = "sqlite+aiosqlite:///./test_firewall_portal.db"
    settings.ENVIRONMENT = Environment.DEVELOPMENT
    settings.DEBUG = True
    settings.ALLOWED_HOSTS = ["*"]
    yield
    settings.SECRET_KEY = original_secret
    settings.DATABASE_URL = original_db
    settings.ENVIRONMENT = original_env
    settings.DEBUG = original_debug
    settings.ALLOWED_HOSTS = original_allowed_hosts


# Async engine and session for tests
@pytest.fixture(scope="session")
def anyio_backend():
    """Backends for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    import aiosqlite
    from sqlalchemy.ext.asyncio import create_async_engine

    test_db_url = "sqlite+aiosqlite:///./test_firewall_portal.db"
    test_engine = create_async_engine(test_db_url, echo=False)
    return test_engine


@pytest_asyncio.fixture
async def db_session(engine):
    """Create a database session with rollback after each test."""
    async with AsyncSession(engine) as session:
        await session.begin_nested()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        await session.close()


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client."""
    async def get_test_db():
        yield db_session

    transport = ASGITransport(app=app)
    app.dependency_overrides[getattr(__import__("app.main", fromlist=["get_db"]), "get_db", lambda: get_test_db)] = get_test_db
    app.router.dependency_overrides = {
        getattr(__import__("app.routers.firewalls", fromlist=["get_db"]), "get_db", lambda: None): get_test_db,
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser for testing."""
    user = User(
        oidc_sub="test-sub-super-" + str(uuid4())[:8],
        email="super@example.com",
        display_name="Super User",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def normal_user(db_session: AsyncSession) -> User:
    """Create a normal user for testing."""
    user = User(
        oidc_sub="test-sub-user-" + str(uuid4())[:8],
        email="user@example.com",
        display_name="Normal User",
        role="workload_stakeholder",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def security_user(db_session: AsyncSession) -> User:
    """Create a security stakeholder user."""
    user = User(
        oidc_sub="test-sub-sec-" + str(uuid4())[:8],
        email="security@example.com",
        display_name="Security User",
        role="security_stakeholder",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_rule(superuser, db_session: AsyncSession) -> FirewallRule:
    """Create a sample firewall rule for testing."""
    rule = FirewallRule(
        name="Test Rule",
        description="A test firewall rule",
        landing_zone="corp",
        rule_collection_name="Test Collection",
        priority=100,
        action=RuleAction.ALLOW,
        status=RuleStatus.DRAFT,
        created_by_id=superuser.id,
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)
    return rule


@pytest_asyncio.fixture
async def active_rule(superuser, db_session: AsyncSession) -> FirewallRule:
    """Create an active firewall rule for testing."""
    rule = FirewallRule(
        name="Active Rule",
        description="An active firewall rule",
        landing_zone="corp",
        rule_collection_name="Active Collection",
        priority=200,
        action=RuleAction.ALLOW,
        status=RuleStatus.ACTIVE,
        source_address="0.0.0.0/0",
        destination_address="10.0.0.0/8",
        destination_ports=["443", "80"],
        destination_fqdns=["*.example.com"],
        protocols=["TCP"],
        category=ResourceCategory.NETWORK,
        workload="web-frontend",
        tags=[
            Tag(name="production", color="#ff0000"),
        ],
        created_by_id=superuser.id,
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)
    return rule


@pytest_asyncio.fixture
async def draft_rule(superuser, db_session: AsyncSession) -> FirewallRule:
    """Create a draft firewall rule for testing."""
    rule = FirewallRule(
        name="Draft Rule",
        description="A draft firewall rule",
        landing_zone="dev",
        rule_collection_name="Draft Collection",
        priority=300,
        action=RuleAction.DENY,
        status=RuleStatus.DRAFT,
        created_by_id=superuser.id,
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)
    return rule


@pytest_asyncio.fixture
async def multiple_rules(superuser, db_session: AsyncSession) -> list:
    """Create multiple firewall rules for testing."""
    rules = []
    for i in range(5):
        rule = FirewallRule(
            name=f"Test Rule {i}",
            description=f"Description for rule {i}",
            landing_zone="corp" if i % 2 == 0 else "dev",
            rule_collection_name="Test Collection",
            priority=100 + i * 10,
            action=RuleAction.ALLOW if i % 2 == 0 else RuleAction.DENY,
            status=RuleStatus.ACTIVE if i < 3 else RuleStatus.DRAFT,
            created_by_id=superuser.id,
        )
        db_session.add(rule)
        rules.append(rule)
    await db_session.commit()
    for rule in rules:
        await db_session.refresh(rule)
    return rules


@pytest_asyncio.fixture
async def sample_tags(db_session: AsyncSession) -> list:
    """Create sample tags."""
    tags = [
        Tag(name="production", color="#ff0000"),
        Tag(name="staging", color="#ffaa00"),
        Tag(name="development", color="#00ff00"),
    ]
    db_session.add_all(tags)
    await db_session.commit()
    return tags


@pytest_asyncio.fixture
async def sample_approval(superuser, sample_rule, db_session: AsyncSession) -> ApprovalRecord:
    """Create a sample approval record."""
    approval = ApprovalRecord(
        rule_id=sample_rule.id,
        user_id=superuser.id,
        action=ApprovalStatus.APPROVE,
        notes="Initial approval",
        created_at=datetime.utcnow(),
    )
    db_session.add(approval)
    await db_session.commit()
    await db_session.refresh(approval)
    return approval


@pytest_asyncio.fixture
def admin_access_token():
    """Generate an admin access token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "role": "admin"},
        expires_delta=timedelta(minutes=15),
    )


@pytest_asyncio.fixture
def user_access_token():
    """Generate a user access token for testing."""
    return create_access_token(
        data={"sub": "normal-user", "role": "workload_stakeholder"},
        expires_delta=timedelta(minutes=15),
    )


@pytest_asyncio.fixture
def auth_headers(admin_access_token):
    """Generate auth headers for testing."""
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture
def rule_data():
    """Return valid firewall rule data."""
    return {
        "name": "Allow HTTPS Inbound",
        "description": "Allow HTTPS from internet",
        "landing_zone": "corp",
        "rule_collection_name": "Corporate Rules",
        "priority": 100,
        "action": "allow",
        "destination_ports": ["443"],
        "category": "network",
        "environment": "production",
        "source_address": "0.0.0.0/0",
        "destination_address": "10.0.0.0/8",
        "destination_fqdns": ["*.example.com"],
        "protocols": ["TCP"],
        "workload": "web-frontend",
        "tags": ["production"],
    }


@pytest.fixture
def invalid_rule_data():
    """Return invalid firewall rule data."""
    return {
        "name": "",
        "landing_zone": "invalid",
        "rule_collection_name": "",
        "priority": 99999,
        "action": "invalid",
    }


@pytest.fixture
def approval_data():
    """Return valid approval data."""
    return {
        "action": "approve",
        "notes": "Approved for production",
    }


@pytest.fixture
def filter_params():
    """Return valid filter parameters."""
    return {
        "landing_zone": "corp",
        "status": "ACTIVE",
        "action": "allow",
        "category": "network",
    }