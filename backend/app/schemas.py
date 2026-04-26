"""Pydantic schemas for request/response validation."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator
from app.config import Role, ApprovalLevel
from app.models import RuleAction, RuleStatus, ApprovalStatus, WorkloadType, ResourceCategory


# ─── Authentication ───────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    expires_in: int = 1800


class TokenData(BaseModel):
    sub: str | None = None
    email: str | None = None
    roles: List[str] = Field(default_factory=list)
    workload: str | None = None
    workload_type: str | None = None


class LoginRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


# ─── Users ────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int | None = None
    oidc_sub: str | None = None
    email: str | None = None
    display_name: str | None = None
    role: str | None = None
    workload: str | None = None
    workload_type: str | None = None
    is_active: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: str
    display_name: str
    role: str = "viewer"
    workload: str | None = None
    workload_type: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = {r.value for r in Role}
        if v not in allowed:
            raise ValueError(f"Role must be one of: {allowed}")
        return v


# ─── Tags ─────────────────────────────────────────────────────────────────────

class TagResponse(BaseModel):
    id: int | None = None
    name: str | None = None
    color: str | None = None

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str
    color: str | None = None


# ─── Firewall Rules ──────────────────────────────────────────────────────────

class FirewallRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    landing_zone: str = Field(..., min_length=1, max_length=255)
    subscription_id: str | None = None
    resource_group: str | None = None
    firewall_policy: str | None = None
    rule_collection_name: str = Field(..., min_length=1, max_length=255)
    priority: int = Field(200, ge=100, le=10000)
    action: RuleAction = RuleAction.DENY
    source_addresses: List[str] | None = None
    destination_addresses: List[str] | None = None
    destination_ports: List[str] | None = None
    destination_fqdns: List[str] | None = None
    protocols: List[str] | None = None
    category: ResourceCategory = ResourceCategory.NETWORK
    workload: str | None = None
    workload_type: str | None = None
    environment: str = "development"
    tags: List[str] | None = None
    approvers: List[str] | None = None  # list of user emails or OIDC sub identifiers
    required_approval_level: str | None = None

    @field_validator("workload_type")
    @classmethod
    def validate_workload_type(cls, v):
        if v is not None and not any(v == wt.value for wt in WorkloadType):
            raise ValueError(f"Invalid workload_type. Must be one of: {[e.value for e in WorkloadType]}")
        return v


class FirewallRuleCreate(FirewallRuleBase):
    pass


class FirewallRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    landing_zone: str | None = None
    subscription_id: str | None = None
    resource_group: str | None = None
    firewall_policy: str | None = None
    rule_collection_name: str | None = None
    priority: int | None = Field(default=None, ge=100, le=10000)
    action: RuleAction | None = None
    source_addresses: List[str] | None = None
    destination_addresses: List[str] | None = None
    destination_ports: List[str] | None = None
    destination_fqdns: List[str] | None = None
    protocols: List[str] | None = None
    category: ResourceCategory | None = None
    workload: str | None = None
    workload_type: str | None = None
    environment: str | None = None
    is_active: bool | None = None


class FirewallRuleResponse(FirewallRuleBase):
    id: int
    status: RuleStatus | None = RuleStatus.DRAFT
    is_active: bool = True
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    submitted_for_approval_at: datetime | None = None
    tags: List[TagResponse] = Field(default_factory=list)
    approvers: List[UserResponse] = Field(default_factory=list)
    approvals: List["ApprovalResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class FirewallRuleListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List[FirewallRuleResponse]


# ─── Approval ─────────────────────────────────────────────────────────────────

class ApprovalRecordResponse(BaseModel):
    id: int | None = None
    rule_id: int | None = None
    approver_id: str | None = None
    approver_name: str | None = None
    approver_role: str | None = None
    status: ApprovalStatus | None = ApprovalStatus.PENDING
    notes: str | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApprovalActionRequest(BaseModel):
    action: str = Field(..., description="approve or reject")
    notes: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v.lower() not in ("approve", "reject"):
            raise ValueError("Action must be 'approve' or 'reject'")
        return v


class ApprovalWorkflowResponse(BaseModel):
    id: int | None = None
    rule_id: int | None = None
    approval_level: str | None = None
    approver_role: str | None = None
    approver_email: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    is_completed: bool = False
    completed_at: datetime | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    action: str | None = None
    old_values: dict | None = None
    new_values: dict | None = None
    user_id: str | None = None
    username: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime | None = None
    extra_data: dict | None = None

    model_config = {"from_attributes": True}


class AuditLogFilter(BaseModel):
    entity_type: str | None = None
    entity_id: int | None = None
    action: str | None = None
    user_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int = 1
    per_page: int = 50


# ─── Rule Collection ──────────────────────────────────────────────────────────

class RuleCollectionResponse(BaseModel):
    id: int | None = None
    name: str | None = None
    firewall_policy: str | None = None
    subscription_id: str | None = None
    resource_group: str | None = None
    rule_count: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ─── Search / Filter ─────────────────────────────────────────────────────────

# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    items: List[Any] = Field(..., description="List of items")


# ─── Statistics ───────────────────────────────────────────────────────────────

class StatisticsResponse(BaseModel):
    """Dashboard statistics."""
    total_rules: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_action: Dict[str, int] = Field(default_factory=dict)
    by_landing_zone: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    """Health check response with dependency status."""
    status: str
    version: str
    environment: str
    database: str = "unknown"
    cache: str = "unknown"
    timestamp: str
