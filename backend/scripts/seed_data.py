"""Seed data script for development environment."""
import asyncio
import os
import sys

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import RuleAction, RuleStatus, ResourceCategory, ApprovalStatus
from app.database import engine
from app.models import ApprovalRecord, AuditLog, FirewallRule, Tag, TagRule, User
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker


async def seed_data():
    """Seed the database with initial data."""
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
            User(
                oidc_sub="dev-sub-001",
                email="admin@example.com",
                display_name="Admin User",
                role="admin",
            ),
            User(
                oidc_sub="dev-sub-002",
                email="security@example.com",
                display_name="Security Reviewer",
                role="security_stakeholder",
            ),
            User(
                oidc_sub="dev-sub-003",
                email="workload@example.com",
                display_name="Workload Owner",
                role="workload_stakeholder",
            ),
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