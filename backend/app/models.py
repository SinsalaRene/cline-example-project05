import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SaEnum,
    Table, Index, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM as PGENUM
from app.config import ApprovalLevel
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class RuleAction(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
    ALERT = "alert"


class RulePriority(str, enum.Enum):
    LOW = 100
    MEDIUM = 200
    HIGH = 300


class RuleStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    VIEW = "view"


class ResourceCategory(str, enum.Enum):
    NETWORK = "network"
    SECURITY = "security"
    APPLICATION = "application"
    DATA = "data"


class WorkloadType(str, enum.Enum):
    WEB = "web"
    API = "api"
    DATABASE = "database"
    STORAGE = "storage"
    COMPUTE = "compute"
    AI = "ai"
    DATA_PROCESSING = "data_processing"


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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    oidc_sub = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    workload = Column(String(100), nullable=True)
    workload_type = Column(SaEnum(WorkloadType), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    rules = relationship("FirewallRule", secondary=rule_approvers, back_populates="approvers")
    audit_logs = relationship("AuditLog", back_populates="user")
    approvals = relationship("ApprovalRecord", back_populates="approver")

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_workload", "workload"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    rules = relationship("FirewallRule", secondary=rule_tags, back_populates="tags")


class FirewallRule(Base):
    """SQLAlchemy ORM model for Azure firewall rules."""
    __tablename__ = "firewall_rules"
    __table_args__ = (
        CheckConstraint("priority >= 100 AND priority <= 10000", name="check_priority_range"),
        UniqueConstraint("name", "landing_zone", name="uq_rule_name_zone"),
        Index("ix_rules_status", "status"),
        Index("ix_rules_landing_zone", "landing_zone"),
        Index("ix_rules_category", "category"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    landing_zone = Column(String(255), nullable=False, index=True)
    subscription_id = Column(String(255), nullable=True, index=True)
    resource_group = Column(String(255), nullable=True)
    firewall_policy = Column(String(255), nullable=True)
    rule_collection_name = Column(String(255), nullable=False)
    priority = Column(Integer, nullable=False, default=200)
    action = Column(SaEnum(RuleAction), nullable=False, default="deny")

    source_addresses = Column(JSONB, nullable=True)
    destination_addresses = Column(JSONB, nullable=True)
    destination_ports = Column(JSONB, nullable=True)
    destination_fqdns = Column(JSONB, nullable=True)
    protocols = Column(JSONB, nullable=True)

    category = Column(SaEnum(ResourceCategory), nullable=True, default="network")
    workload = Column(String(100), nullable=True, index=True)
    workload_type = Column(SaEnum(WorkloadType), nullable=True)
    environment = Column(String(50), nullable=True, default="development")

    status = Column(SaEnum(RuleStatus), nullable=False, default="draft")
    is_active = Column(Boolean, default=True)

    required_approval_level = Column(PGENUM(ApprovalLevel), nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    submitted_for_approval_at = Column(DateTime, nullable=True)

    approvals = relationship("ApprovalRecord", back_populates="rule", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="rule", cascade="all, delete-orphan")
    approvers = relationship("User", secondary=rule_approvers, back_populates="rules")
    tags = relationship("Tag", secondary=rule_tags, back_populates="rules")


class ApprovalRecord(Base):
    """Represents a single approval step in the approval workflow."""
    __tablename__ = "approval_records"
    __table_args__ = (
        Index("ix_approval_rule_id", "rule_id"),
        Index("ix_approval_user", "approver_id"),
        Index("ix_approval_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("firewall_rules.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(String(255), ForeignKey("users.oidc_sub"), nullable=True)
    approver_role = Column(String(50), nullable=False)
    approver_name = Column(String(255), nullable=False)
    status = Column(SaEnum(ApprovalStatus), default="pending")
    notes = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    rule = relationship("FirewallRule", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(SaEnum(AuditAction), nullable=False)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    user_id = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    extra_data = Column(JSONB, nullable=True)

    rule = relationship("FirewallRule", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")


class ApprovalWorkflow(Base):
    """Defines the approval workflow configuration for a firewall rule."""
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_approval_levels = Column(JSONB, nullable=False)
    auto_approve_after_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    rules = relationship("FirewallRule", back_populates="workflow")