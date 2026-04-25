"""Firewall rule API routes."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user, require_role
from app.database import get_db
from app.models import User
from app.schemas import (
    FirewallRuleCreate,
    FirewallRuleUpdate,
    FirewallRuleResponse,
    FirewallRuleListResponse,
    RuleFilterRequest,
    AuditLogResponse,
)
from app.services.firewall_service import FirewallRuleService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rules", tags=["firewall-rules"])


@router.get("", response_model=FirewallRuleListResponse)
async def list_rules(
    landing_zone: Optional[str] = Query(None, description="Filter by landing zone"),
    status: Optional[str] = Query(None, description="Filter by status (comma-separated)"),
    action: Optional[str] = Query(None, description="Filter by action (comma-separated)"),
    category: Optional[str] = Query(None, description="Filter by category (comma-separated)"),
    workload: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    priority_min: Optional[int] = Query(None, ge=100, le=10000),
    priority_max: Optional[int] = Query(None, ge=100, le=10000),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort_by: str = Query("updated_at", regex="^(name|landing_zone|priority|updated_at|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List firewall rules with filtering and pagination."""
    status_list = [s.strip().lower() for s in status.split(",")] if status else None
    action_list = [a.strip().lower() for a in action.split(",")] if action else None
    category_list = [c.strip().lower() for c in category.split(",")] if category else None

    filter_req = RuleFilterRequest(
        landing_zone=landing_zone,
        status=status_list,
        action=action_list,
        category=category_list,
        workload=workload,
        environment=environment,
        search=search,
        priority_min=priority_min,
        priority_max=priority_max,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = FirewallRuleService(db)
    rules, total = service.list_rules(filter_req, page, per_page)

    items = [
        FirewallRuleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            landing_zone=r.landing_zone,
            subscription_id=r.subscription_id,
            resource_group=r.resource_group,
            firewall_policy=r.firewall_policy,
            rule_collection_name=r.rule_collection_name,
            priority=r.priority,
            action=r.action.value if hasattr(r.action, "value") else str(r.action),
            source_addresses=r.source_addresses,
            destination_addresses=r.destination_addresses,
            destination_ports=r.destination_ports,
            destination_fqdns=r.destination_fqdns,
            protocols=r.protocols,
            category=r.category.value if hasattr(r.category, "value") else str(r.category),
            workload=r.workload,
            workload_type=r.workload_type.value if hasattr(r.workload_type, "value") else str(r.workload_type),
            environment=r.environment,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            is_active=r.is_active,
            created_by=r.created_by,
            created_at=r.created_at,
            updated_at=r.updated_at,
            approved_at=r.approved_at,
            approved_by=r.approved_by,
            submitted_for_approval_at=r.submitted_for_approval_at,
            tags=[{"id": t.id, "name": t.name, "color": t.color} for t in r.tags] if r.tags else [],
            approvers=[{"id": a.id, "email": a.email, "display_name": a.display_name, "role": a.role} for a in r.approvers] if r.approvers else [],
            approvals=[{"id": a.id, "approver_role": a.approver_role, "approver_name": a.approver_name, "status": a.status.value, "notes": a.notes} for a in r.approvals] if r.approvals else [],
        )
        for r in rules
    ]

    return FirewallRuleListResponse(total=total, page=page, per_page=per_page, items=items)


@router.get("/{rule_id}", response_model=FirewallRuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single firewall rule by ID."""
    service = FirewallRuleService(db)
    rule = service.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail=f"Firewall rule {rule_id} not found")

    return FirewallRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        landing_zone=rule.landing_zone,
        subscription_id=rule.subscription_id,
        resource_group=rule.resource_group,
        firewall_policy=rule.firewall_policy,
        rule_collection_name=rule.rule_collection_name,
        priority=rule.priority,
        action=rule.action.value if hasattr(rule.action, "value") else str(rule.action),
        source_addresses=rule.source_addresses,
        destination_addresses=rule.destination_addresses,
        destination_ports=rule.destination_ports,
        destination_fqdns=rule.destination_fqdns,
        protocols=rule.protocols,
        category=rule.category.value if hasattr(rule.category, "value") else str(rule.category),
        workload=rule.workload,
        workload_type=rule.workload_type.value if hasattr(rule.workload_type, "value") else str(rule.workload_type),
        environment=rule.environment,
        status=rule.status.value if hasattr(rule.status, "value") else str(rule.status),
        is_active=rule.is_active,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        approved_at=rule.approved_at,
        approved_by=rule.approved_by,
        submitted_for_approval_at=rule.submitted_for_approval_at,
        tags=[{"id": t.id, "name": t.name, "color": t.color} for t in rule.tags] if rule.tags else [],
        approvers=[{"id": a.id, "email": a.email, "display_name": a.display_name, "role": a.role} for a in rule.approvers] if rule.approvers else [],
        approvals=[{"id": a.id, "approver_role": a.approver_role, "approver_name": a.approver_name, "status": a.status.value, "notes": a.notes} for a in rule.approvals] if rule.approvals else [],
    )


@router.post("", response_model=FirewallRuleResponse, status_code=201)
async def create_rule(
    rule_data: FirewallRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new firewall rule."""
    service = FirewallRuleService(db)
    rule = service.create_rule(rule_data.model_dump(), user)

    return FirewallRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        landing_zone=rule.landing_zone,
        subscription_id=rule.subscription_id,
        resource_group=rule.resource_group,
        firewall_policy=rule.firewall_policy,
        rule_collection_name=rule.rule_collection_name,
        priority=rule.priority,
        action=rule.action.value if hasattr(rule.action, "value") else str(rule.action),
        source_addresses=rule.source_addresses,
        destination_addresses=rule.destination_addresses,
        destination_ports=rule.destination_ports,
        destination_fqdns=rule.destination_fqdns,
        protocols=rule.protocols,
        category=rule.category.value if hasattr(rule.category, "value") else str(rule.category),
        workload=rule.workload,
        workload_type=rule.workload_type.value if hasattr(rule.workload_type, "value") else str(rule.workload_type),
        environment=rule.environment,
        status=rule.status.value if hasattr(rule.status, "value") else str(rule.status),
        is_active=rule.is_active,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        approved_at=rule.approved_at,
        approved_by=rule.approved_by,
        submitted_for_approval_at=rule.submitted_for_approval_at,
        tags=[{"id": t.id, "name": t.name, "color": t.color} for t in rule.tags] if rule.tags else [],
        approvers=[{"id": a.id, "email": a.email, "display_name": a.display_name, "role": a.role} for a in rule.approvers] if rule.approvers else [],
        approvals=[{"id": a.id, "approver_role": a.approver_role, "approver_name": a.approver_name, "status": a.status.value, "notes": a.notes} for a in rule.approvals] if rule.approvals else [],
    )


@router.put("/{rule_id}", response_model=FirewallRuleResponse)
async def update_rule(
    rule_id: int,
    update_data: FirewallRuleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a firewall rule."""
    service = FirewallRuleService(db)
    rule = service.update_rule(rule_id, update_data.model_dump(exclude_none=True), user)

    return FirewallRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        landing_zone=rule.landing_zone,
        subscription_id=rule.subscription_id,
        resource_group=rule.resource_group,
        firewall_policy=rule.firewall_policy,
        rule_collection_name=rule.rule_collection_name,
        priority=rule.priority,
        action=rule.action.value if hasattr(rule.action, "value") else str(rule.action),
        source_addresses=rule.source_addresses,
        destination_addresses=rule.destination_addresses,
        destination_ports=rule.destination_ports,
        destination_fqdns=rule.destination_fqdns,
        protocols=rule.protocols,
        category=rule.category.value if hasattr(rule.category, "value") else str(rule.category),
        workload=rule.workload,
        workload_type=rule.workload_type.value if hasattr(rule.workload_type, "value") else str(rule.workload_type),
        environment=rule.environment,
        status=rule.status.value if hasattr(rule.status, "value") else str(rule.status),
        is_active=rule.is_active,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        approved_at=rule.approved_at,
        approved_by=rule.approved_by,
        submitted_for_approval_at=rule.submitted_for_approval_at,
        tags=[{"id": t.id, "name": t.name, "color": t.color} for t in rule.tags] if rule.tags else [],
        approvers=[{"id": a.id, "email": a.email, "display_name": a.display_name, "role": a.role} for a in rule.approvers] if rule.approvers else [],
        approvals=[{"id": a.id, "approver_role": a.approver_role, "approver_name": a.approver_name, "status": a.status.value, "notes": a.notes} for a in rule.approvals] if rule.approvals else [],
    )


@router.delete("/{rule_id}", response_model=dict)
async def archive_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "reviewer")),
):
    """Archive a firewall rule."""
    service = FirewallRuleService(db)
    rule = service.archive_rule(rule_id, user)
    return {"message": f"Firewall rule {rule_id} archived successfully", "rule_id": rule_id}


@router.get("/{rule_id}/audit", response_model=dict)
async def get_rule_audit_logs(
    rule_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get audit logs for a firewall rule."""
    service = FirewallRuleService(db)
    logs, total = service.get_rule_audit_logs(rule_id, page, per_page)

    items = [
        {
            "id": log.id,
            "action": log.action.value if hasattr(log.action, "value") else str(log.action),
            "old_values": log.old_values,
            "new_values": log.new_values,
            "user_id": log.user_id,
            "username": log.username,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "extra_data": log.extra_data,
        }
        for log in logs
    ]

    return {"total": total, "page": page, "per_page": per_page, "items": items}