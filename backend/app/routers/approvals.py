"""Approval workflow API routes."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user, require_role
from app.database import get_db
from app.models import ApprovalRecord, User
from app.schemas import ApprovalActionRequest
from app.services.approval_service import ApprovalWorkflowService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/pending", response_model=dict)
async def get_pending_approvals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all pending approvals for the current user."""
    service = ApprovalWorkflowService(db)
    approvals, total = service.get_pending_approvals(user, page, per_page)
    return {"total": total, "page": page, "per_page": per_page, "items": approvals}


@router.get("/rule/{rule_id}/status", response_model=list)
async def get_rule_approval_status(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get approval status for a specific rule."""
    service = ApprovalWorkflowService(db)
    status = service.get_rule_approval_status(rule_id)
    return status


@router.post("/rule/{rule_id}/submit", response_model=dict)
async def submit_for_approval(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit a rule for approval."""
    service = ApprovalWorkflowService(db)
    rule = service.submit_for_approval(rule_id, user)
    return {
        "message": f"Rule {rule_id} submitted for approval",
        "rule_id": rule_id,
        "status": rule.status.value if hasattr(rule.status, "value") else str(rule.status),
    }


@router.post("/rule/{rule_id}/approve/{approval_id}", response_model=dict)
async def approve_approval(
    rule_id: int,
    approval_id: int,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Approve a specific approval record."""
    service = ApprovalWorkflowService(db)
    try:
        rule = service.approve(rule_id, approval_id, user, notes)
        return {
            "message": f"Approval {approval_id} approved",
            "approval_id": approval_id,
            "rule_id": rule_id,
            "rule_status": rule.status.value if hasattr(rule.status, "value") else str(rule.status),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/rule/{rule_id}/reject/{approval_id}", response_model=dict)
async def reject_approval(
    rule_id: int,
    approval_id: int,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reject a specific approval record."""
    service = ApprovalWorkflowService(db)
    try:
        rule = service.reject(rule_id, approval_id, user, notes)
        return {
            "message": f"Approval {approval_id} rejected",
            "approval_id": approval_id,
            "rule_id": rule_id,
            "rule_status": rule.status.value if hasattr(rule.status, "value") else str(rule.status),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))