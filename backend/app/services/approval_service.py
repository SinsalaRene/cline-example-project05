"""Multi-level approval workflow service."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import (
    ApprovalRecord, ApprovalStatus, FirewallRule, RuleStatus,
    User, AuditAction,
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

# Approval level roles
SECURITY_ROLE = "security_stakeholder"
WORKLOAD_ROLE = "workload_stakeholder"


def get_required_approvers(rule: FirewallRule) -> list[dict]:
    """Determine which approvers are needed based on the rule's configuration."""
    approvers: list[dict] = []

    # Determine required levels based on rule configuration
    if hasattr(rule, 'required_approval_level') and rule.required_approval_level:
        if rule.required_approval_level in ("security_and_workload", WORKLOAD_ROLE):
            approvers.append({"role": SECURITY_ROLE, "level": 1})
            approvers.append({"role": WORKLOAD_ROLE, "level": 2})
        elif rule.required_approval_level == SECURITY_ROLE:
            approvers.append({"role": SECURITY_ROLE, "level": 1})
        elif rule.required_approval_level == WORKLOAD_ROLE:
            approvers.append({"role": WORKLOAD_ROLE, "level": 1})
    else:
        # Default: both security and workload stakeholders
        approvers.append({"role": SECURITY_ROLE, "level": 1})
        approvers.append({"role": WORKLOAD_ROLE, "level": 2})

    # If no approvers assigned, find users with those roles in the same workload
    if not approvers:
        if rule.workload:
            for i, lvl in enumerate(["security_stakeholder", "workload_stakeholder"]):
                approvers.append({"role": lvl, "level": i + 1})

    return approvers


class ApprovalWorkflowService:
    """Manages multi-level approval workflows for firewall rules."""

    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def submit_for_approval(self, rule_id: int, user: User) -> FirewallRule:
        """Submit a firewall rule for approval, creating approval records."""
        rule = self.db.execute(
            select(FirewallRule).where(FirewallRule.id == rule_id)
        ).scalar_one_or_none()

        if not rule:
            raise ValueError(f"Firewall rule {rule_id} not found")

        if rule.status not in (RuleStatus.DRAFT, RuleStatus.REJECTED):
            raise ValueError(f"Rule is in '{rule.status.value}' state - cannot submit")

        old_status = RuleStatus(rule.status)
        rule.status = RuleStatus.PENDING_APPROVAL
        rule.submitted_for_approval_at = datetime.utcnow()

        # Get required approvers for this rule
        required = get_required_approvers(rule)

        # Find users for each approver role in the rule's workload context
        workload_filter = select(User).where(User.is_active == True)
        if rule.workload:
            workload_filter = workload_filter.where(User.workload == rule.workload)

        all_users = self.db.execute(workload_filter).scalars().all()

        for approver_info in required:
            role = approver_info["role"]
            level = approver_info["level"]

            # Find a user with this role in the workload context
            approver = None
            for u in all_users:
                if u.role == role:
                    approver = u
                    break

            # If no exact match, try any user with the role
            if not approver:
                for u in all_users:
                    if u.role == role:
                        approver = u
                        break

            record = ApprovalRecord(
                rule_id=rule.id,
                approver_id=approver.oidc_sub if approver else None,
                approver_name=approver.display_name if approver else f"{role} (unassigned)",
                approver_role=role,
                status=ApprovalStatus.PENDING,
            )
            self.db.add(record)

            logger.info(f"Created approval record #{record.id} for rule #{rule_id}, level {level}, role {role}")

        self.audit.log_action(
            entity_type="firewall_rule",
            entity_id=rule_id,
            action=AuditAction.SUBMIT.value,
            old_values={"status": old_status.value},
            new_values={"status": RuleStatus.PENDING_APPROVAL.value},
            user_id=user.oidc_sub,
            username=user.display_name,
            extra_data={"required_levels": [a["role"] for a in required]},
        )

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def approve(self, rule_id: int, approval_id: int, user: User, notes: Optional[str] = None) -> FirewallRule:
        """Approve a single approval record in the workflow."""
        record = self.db.execute(
            select(ApprovalRecord).where(
                ApprovalRecord.id == approval_id,
                ApprovalRecord.rule_id == rule_id,
            )
        ).scalar_one_or_none()

        if not record:
            raise ValueError(f"Approval record {approval_id} not found for rule {rule_id}")

        if record.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval record is already {record.status.value}")

        # Check if user is authorized to approve this level
        if record.approver_role != user.role:
            # Admin can approve any role
            if user.role != "admin":
                raise ValueError(f"User role '{user.role}' cannot approve role '{record.approver_role}'")

        record.status = ApprovalStatus.APPROVED
        record.approved_at = datetime.utcnow()
        record.notes = notes

        # Check if all approval levels are completed
        all_records = self.db.execute(
            select(ApprovalRecord).where(ApprovalRecord.rule_id == rule_id)
        ).scalars().all()

        rule = self.db.execute(
            select(FirewallRule).where(FirewallRule.id == rule_id)
        ).scalar_one_or_none()

        # Check if all approvers have approved
        if all(r.status == ApprovalStatus.APPROVED for r in all_records):
            old_status = RuleStatus(rule.status) if rule else RuleStatus.DRAFT
            rule.status = RuleStatus.ACTIVE
            rule.approved_at = datetime.utcnow()
            rule.approved_by = user.oidc_sub

            self.audit.log_action(
                entity_type="firewall_rule",
                entity_id=rule_id,
                action=AuditAction.APPROVE.value,
                old_values={"status": old_status.value},
                new_values={"status": RuleStatus.ACTIVE.value},
                user_id=user.oidc_sub,
                username=user.display_name,
                extra_data={"approver_role": user.role, "notes": notes},
            )

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def reject(self, rule_id: int, approval_id: int, user: User, notes: Optional[str] = None) -> FirewallRule:
        """Reject a single approval record in the workflow."""
        record = self.db.execute(
            select(ApprovalRecord).where(
                ApprovalRecord.id == approval_id,
                ApprovalRecord.rule_id == rule_id,
            )
        ).scalar_one_or_none()

        if not record:
            raise ValueError(f"Approval record {approval_id} not found for rule {rule_id}")

        if record.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval record is already {record.status.value}")

        # Check authorization
        if record.approver_role != user.role:
            if user.role != "admin":
                raise ValueError(f"User role '{user.role}' cannot reject role '{record.approver_role}'")

        record.status = ApprovalStatus.REJECTED
        record.approved_at = datetime.utcnow()
        record.notes = notes

        # Reject the entire rule
        rule = self.db.execute(
            select(FirewallRule).where(FirewallRule.id == rule_id)
        ).scalar_one_or_none()

        if rule:
            old_status = RuleStatus(rule.status) if rule else RuleStatus.DRAFT
            rule.status = RuleStatus.REJECTED
            rule.approved_at = datetime.utcnow()

            self.audit.log_action(
                entity_type="firewall_rule",
                entity_id=rule_id,
                action=AuditAction.REJECT.value,
                old_values={"status": old_status.value},
                new_values={"status": RuleStatus.REJECTED.value},
                user_id=user.oidc_sub,
                username=user.display_name,
                extra_data={"approver_role": user.role, "notes": notes},
            )

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_pending_approvals(self, user: User, page: int = 1, per_page: int = 20) -> tuple[list[dict], int]:
        """Get all pending approvals for the current user."""
        query = (
            select(ApprovalRecord)
            .join(FirewallRule)
            .options(joinedload(ApprovalRecord.rule))
            .where(
                ApprovalRecord.status == ApprovalStatus.PENDING,
                (ApprovalRecord.approver_id == user.oidc_sub) | (user.role == "admin")
            )
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(ApprovalRecord.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page)

        records = self.db.execute(query).scalars().all()

        result = []
        for r in records:
            rule = self.db.execute(
                select(FirewallRule).where(FirewallRule.id == r.rule_id)
            ).scalar_one_or_none()
            result.append({
                "approval_record_id": r.id,
                "rule_id": r.rule_id,
                "rule_name": rule.name if rule else "Unknown",
                "rule_status": rule.status.value if rule else None,
                "approver_role": r.approver_role,
                "status": r.status.value,
                "notes": r.notes,
                "created_at": r.created_at,
            })

        return result, total or 0

    def get_rule_approval_status(self, rule_id: int) -> list[dict]:
        """Get the approval status for a specific rule."""
        records = self.db.execute(
            select(ApprovalRecord).where(ApprovalRecord.rule_id == rule_id).order_by(ApprovalRecord.approver_role)
        ).scalars().all()

        return [
            {
                "id": r.id,
                "approver_role": r.approver_role,
                "approver_name": r.approver_name,
                "status": r.status.value,
                "notes": r.notes,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            }
            for r in records
        ]

    def check_auto_approve(self) -> list[FirewallRule]:
        """Auto-approve rules that have been pending for longer than configured days."""
        cutoff = datetime.utcnow() - timedelta(days=settings.AUTO_APPROVE_AFTER_DAYS)

        query = (
            select(FirewallRule)
            .where(
                FirewallRule.status == RuleStatus.PENDING_APPROVAL,
                FirewallRule.submitted_for_approval_at <= cutoff,
            )
        )

        rules = self.db.execute(query).scalars().all()

        for rule in rules:
            # Mark all pending approvals as approved
            pending_approvals = self.db.execute(
                select(ApprovalRecord).where(
                    ApprovalRecord.rule_id == rule.id,
                    ApprovalRecord.status == ApprovalStatus.PENDING
                )
            ).scalars().all()

            for approval in pending_approvals:
                approval.status = ApprovalStatus.APPROVED
                approval.approved_at = datetime.utcnow()
                approval.notes = "Auto-approved: pending longer than configured threshold"

            old_status = RuleStatus(rule.status) if rule else RuleStatus.DRAFT
            rule.status = RuleStatus.ACTIVE
            rule.approved_at = datetime.utcnow()
            rule.approved_by = "system"

            self.audit.log_action(
                entity_type="firewall_rule",
                entity_id=rule.id,
                action=AuditAction.APPROVE.value,
                old_values={"status": old_status.value},
                new_values={"status": RuleStatus.ACTIVE.value},
                user_id="system",
                username="system",
                extra_data={"reason": "auto_approve_threshold"},
            )

        if rules:
            self.db.commit()

        return rules