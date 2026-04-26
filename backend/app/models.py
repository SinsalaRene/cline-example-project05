"""Enhanced SQLAlchemy models with soft delete and versioning."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, JSON, UniqueConstraint, Index, CheckConstraint, Table,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY, INET
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from app.config import (
    RuleAction, RuleStatus, ApprovalStatus, ResourceCategory,
    WorkloadType, AuditAction, ApprovalLevel,
)


# Re-export enums from config for backward compatibility
__all__ = [
    "RuleAction",
    "RuleStatus",
    "ApprovalStatus",
    "ResourceCategory",
    "WorkloadType",
    "AuditAction",
    "ApprovalLevel",
    # Models
    "_BaseMixin",
    "User",
    "Tag",
    "TagRule",
    "FirewallRule",
    "ApprovalRecord",
    "AuditLog",
    "ApprovalWorkflow",
]


def utc_now():
    """Return current UTC datetime (naive, for TIMESTAMP WITHOUT TIME ZONE)."""
    return datetime.utcnow()


def utc_now_factory(context=None):
    """Factory function for default datetime values (naive)."""
    return datetime.utcnow()


class _BaseMixin:
    """Mixin adding soft delete, versioning, and tracking to models."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, nullable=True, index=True
    )
    _version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_factory, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_factory, onupdate=utc_now_factory, nullable=False
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


# ─── Association Tables ────────────────────────────────────────────────────────

rule_tags = Table(
    "rule_tags",
    Base.metadata,
    Column("rule_id", Integer, ForeignKey("firewall_rules.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

rule_approvers = Table(
    "rule_approvers",
    Base.metadata,
    Column("rule_id", Integer, ForeignKey("firewall_rules.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(255), ForeignKey("users.oidc_sub", ondelete="CASCADE"), primary_key=True),
)


# ─── Models ───────────────────────────────────────────────────────────────────


class User(Base, _BaseMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    oidc_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), default="viewer")
    workload: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workload_type: Mapped[str | None] = mapped_column(SAEnum(WorkloadType), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    created_rules = relationship(
        "FirewallRule",
        foreign_keys="FirewallRule.created_by_id",
        back_populates="created_by_user",
        lazy="selectin",
    )
    approved_rules = relationship(
        "FirewallRule",
        foreign_keys="FirewallRule.approved_by_id",
        back_populates="approved_by_user",
        lazy="selectin",
    )
    approval_records = relationship(
        "ApprovalRecord",
        primaryjoin="User.oidc_sub == foreign(ApprovalRecord.approver_id)",
        back_populates="approver",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_workload", "workload"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Tag(Base, _BaseMixin):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    rule_tags = relationship("TagRule", back_populates="tag", lazy="selectin")

    __table_args__ = (
        Index("ix_tag_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name}>"


class TagRule(Base, _BaseMixin):
    """Junction table for tags and rules."""
    __tablename__ = "tag_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id"), nullable=False)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("firewall_rules.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("tag_id", "rule_id", name="uq_tag_rule"),
    )

    # Relationships
    tag = relationship("Tag", back_populates="rule_tags")
    rule = relationship("FirewallRule", back_populates="rule_tags_list")

    def __repr__(self) -> str:
        return f"<TagRule tag_id={self.tag_id} rule_id={self.rule_id}>"


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
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_for_approval_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_landing_zone_status", "landing_zone", "status"),
        Index("idx_workload_environment", "workload", "environment"),
        Index("idx_name_status", "name", "status"),
        CheckConstraint("priority >= 100 AND priority <= 10000", name="check_priority_range"),
        UniqueConstraint("name", "landing_zone", name="uq_rule_name_zone"),
    )

    # Relationships
    created_by_user = relationship(
        "User",
        back_populates="created_rules",
        foreign_keys=[created_by_id],
        lazy="selectin",
    )
    approved_by_user = relationship(
        "User",
        back_populates="approved_rules",
        foreign_keys=[approved_by_id],
        lazy="selectin",
    )
    rule_tags_list = relationship("TagRule", back_populates="rule", lazy="selectin")
    approvers = relationship(
        "ApprovalRecord",
        back_populates="rule",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FirewallRule id={self.id} name={self.name} status={self.status}>"


class ApprovalRecord(Base, _BaseMixin):
    __tablename__ = "approval_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("firewall_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approver_id = Column(String(255), ForeignKey("users.oidc_sub"), nullable=True)
    approver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approver_role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="security_stakeholder"
    )
    status: Mapped[str] = mapped_column(
        SAEnum(ApprovalStatus), default=ApprovalStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    rule = relationship("FirewallRule", back_populates="approvers")
    approver = relationship(
        "User",
        primaryjoin="User.oidc_sub == foreign(ApprovalRecord.approver_id)",
        uselist=False,
    )

    __table_args__ = (
        Index("idx_rule_status", "rule_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ApprovalRecord id={self.id} rule_id={self.rule_id} status={self.status}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(SAEnum(AuditAction), nullable=False)
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

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} entity={self.entity_type}:{self.entity_id} action={self.action}>"


# Backward compatibility
class ApprovalWorkflow(Base):
    """Defines the approval workflow configuration for a firewall rule."""
    __tablename__ = "approval_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_approval_levels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    auto_approve_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_factory)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_factory, onupdate=utc_now_factory
    )

    def __repr__(self) -> str:
        return f"<ApprovalWorkflow id={self.id} name={self.name}>"