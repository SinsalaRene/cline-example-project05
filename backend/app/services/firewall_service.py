"""Firewall rule CRUD service."""
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import (
    FirewallRule, RuleStatus, RuleAction,
    AuditAction, AuditLog, Tag, User,
    ResourceCategory, WorkloadType,
)
from app.schemas import RuleFilterRequest, FirewallRuleUpdate

logger = logging.getLogger(__name__)


class FirewallRuleService:
    """Handles CRUD operations for firewall rules."""

    def __init__(self, db: Session):
        self.db = db

    def create_rule(self, rule_data: dict, user: User) -> FirewallRule:
        """Create a new firewall rule."""
        rule = FirewallRule(
            name=rule_data["name"],
            description=rule_data.get("description"),
            landing_zone=rule_data["landing_zone"],
            subscription_id=rule_data.get("subscription_id"),
            resource_group=rule_data.get("resource_group"),
            firewall_policy=rule_data.get("firewall_policy"),
            rule_collection_name=rule_data["rule_collection_name"],
            priority=rule_data.get("priority", 200),
            action=rule_data.get("action", RuleAction.DENY),
            source_addresses=rule_data.get("source_addresses"),
            destination_addresses=rule_data.get("destination_addresses"),
            destination_ports=rule_data.get("destination_ports"),
            destination_fqdns=rule_data.get("destination_fqdns"),
            protocols=rule_data.get("protocols"),
            category=rule_data.get("category", ResourceCategory.NETWORK),
            workload=rule_data.get("workload"),
            workload_type=rule_data.get("workload_type"),
            environment=rule_data.get("environment", "development"),
            status=RuleStatus.DRAFT,
            is_active=True,
            required_approval_level=rule_data.get("required_approval_level"),
            created_by=user.oidc_sub,
        )

        # Add tags
        tag_names = rule_data.get("tags", [])
        for tag_name in tag_names:
            tag = self.db.execute(
                select(Tag).where(Tag.name == tag_name)
            ).scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                self.db.add(tag)
            rule.tags.append(tag)

        # Add approvers
        approver_ids = rule_data.get("approvers", [])
        for approver_id in approver_ids:
            approver = self.db.execute(
                select(User).where(
                    or_(User.oidc_sub == approver_id, User.email == approver_id)
                )
            ).scalar_one_or_none()
            if approver:
                rule.approvers.append(approver)

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        # Audit log
        AuditLog(
            entity_type="firewall_rule",
            entity_id=rule.id,
            action=AuditAction.CREATE.value,
            new_values={k: str(v) for k, v in rule_data.items()},
            user_id=user.oidc_sub,
            username=user.display_name,
        )

        logger.info(f"Firewall rule {rule.id} created by {user.display_name}")
        return rule

    def get_rule(self, rule_id: int) -> Optional[FirewallRule]:
        """Get a single firewall rule by ID."""
        return self.db.execute(
            select(FirewallRule)
            .options(
                joinedload(FirewallRule.tags),
                joinedload(FirewallRule.approvers),
                joinedload(FirewallRule.approvals),
            )
            .where(FirewallRule.id == rule_id)
        ).scalar_one_or_none()

    def list_rules(
        self,
        filter_req: Optional[RuleFilterRequest] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[FirewallRule], int]:
        """List firewall rules with filtering and pagination."""
        query = select(FirewallRule).options(
            joinedload(FirewallRule.tags),
            joinedload(FirewallRule.approvers),
            joinedload(FirewallRule.approvals),
        )

        if filter_req:
            if filter_req.landing_zone:
                query = query.where(FirewallRule.landing_zone == filter_req.landing_zone)
            if filter_req.status:
                statuses = [s.strip().lower() for s in filter_req.status]
                query = query.where(FirewallRule.status.in_([s.strip().lower() for s in statuses]))
            if filter_req.action:
                actions = [a.strip().lower() for a in filter_req.action]
                query = query.where(FirewallRule.action.in_([a.strip().lower() for a in actions]))
            if filter_req.category:
                cats = [c.strip().lower() for c in filter_req.category]
                query = query.where(FirewallRule.category.in_([c.strip().lower() for c in cats]))
            if filter_req.workload:
                query = query.where(FirewallRule.workload == filter_req.workload)
            if filter_req.environment:
                query = query.where(FirewallRule.environment == filter_req.environment)
            if filter_req.search:
                search_term = f"%{filter_req.search}%"
                query = query.where(
                    or_(
                        FirewallRule.name.ilike(search_term),
                        FirewallRule.description.ilike(search_term),
                        FirewallRule.rule_collection_name.ilike(search_term),
                    )
                )
            if filter_req.priority_min is not None:
                query = query.where(FirewallRule.priority >= filter_req.priority_min)
            if filter_req.priority_max is not None:
                query = query.where(FirewallRule.priority <= filter_req.priority_max)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        # Determine sort
        sort_by = filter_req.sort_by if filter_req else "updated_at"
        sort_order = filter_req.sort_order if filter_req else "desc"

        sort_map = {
            "name": FirewallRule.name,
            "landing_zone": FirewallRule.landing_zone,
            "priority": FirewallRule.priority,
            "updated_at": FirewallRule.updated_at,
            "created_at": FirewallRule.created_at,
        }
        sort_column = sort_map.get(sort_by, FirewallRule.updated_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        query = query.offset((page - 1) * per_page).limit(per_page)

        rules = self.db.execute(query).scalars().all()
        return rules, total or 0

    def update_rule(
        self,
        rule_id: int,
        update_data: dict,
        user: User,
    ) -> FirewallRule:
        """Update an existing firewall rule."""
        rule = self.db.execute(
            select(FirewallRule).where(FirewallRule.id == rule_id)
        ).scalar_one_or_none()

        if not rule:
            raise ValueError(f"Firewall rule {rule_id} not found")

        # Determine old values for audit
        old_values = {
            "name": rule.name,
            "description": rule.description,
            "priority": rule.priority,
            "action": rule.action.value if hasattr(rule.action, "value") else str(rule.action),
            "status": rule.status.value if hasattr(rule.status, "value") else str(rule.status),
        }

        for key, value in update_data.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)

        rule.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(rule)

        # Audit log
        new_values = {k: str(v) for k, v in update_data.items()}
        AuditLog(
            entity_type="firewall_rule",
            entity_id=rule.id,
            action=AuditAction.UPDATE.value,
            old_values=old_values,
            new_values=new_values,
            user_id=user.oidc_sub,
            username=user.display_name,
        )

        logger.info(f"Firewall rule {rule_id} updated by {user.display_name}")
        return rule

    def archive_rule(self, rule_id: int, user: User) -> FirewallRule:
        """Archive a firewall rule."""
        rule = self.db.execute(
            select(FirewallRule).where(FirewallRule.id == rule_id)
        ).scalar_one_or_none()

        if not rule:
            raise ValueError(f"Firewall rule {rule_id} not found")

        old_status = RuleStatus(rule.status) if rule else RuleStatus.DRAFT
        rule.status = RuleStatus.ARCHIVED
        rule.is_active = False

        self.db.commit()
        self.db.refresh(rule)

        AuditLog(
            entity_type="firewall_rule",
            entity_id=rule.id,
            action=AuditAction.DELETE.value,
            old_values={"status": old_status.value, "is_active": True},
            new_values={"status": RuleStatus.ARCHIVED.value, "is_active": False},
            user_id=user.oidc_sub,
            username=user.display_name,
        )

        return rule

    def get_rule_audit_logs(
        self,
        rule_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs for a specific rule."""
        from app.services.audit_service import AuditService
        audit = AuditService(self.db)
        return audit.get_rule_audit_history(rule_id, page, per_page)

    def get_collections(self, landing_zone: Optional[str] = None) -> list[dict]:
        """Get rule collections for a landing zone."""
        query = (
            select(
                FirewallRule.rule_collection_name,
                FirewallRule.firewall_policy,
                FirewallRule.subscription_id,
                FirewallRule.resource_group,
                func.count(FirewallRule.id).label("rule_count"),
            )
            .group_by(
                FirewallRule.rule_collection_name,
                FirewallRule.firewall_policy,
                FirewallRule.subscription_id,
                FirewallRule.resource_group,
            )
        )

        if landing_zone:
            query = query.where(FirewallRule.landing_zone == landing_zone)

        results = self.db.execute(query).all()
        return [
            {
                "name": r[0],
                "firewall_policy": r[1],
                "subscription_id": r[2],
                "resource_group": r[3],
                "rule_count": r[4],
            }
            for r in results
        ]

    def get_statistics(self) -> dict:
        """Get firewall rule statistics."""
        return {
            "total": self.db.execute(select(func.count(FirewallRule.id))).scalar() or 0,
            "by_status": {
                row[0]: row[1]
                for row in self.db.execute(
                    select(FirewallRule.status, func.count(FirewallRule.id))
                    .group_by(FirewallRule.status)
                ).all()
            },
            "by_action": {
                row[0]: row[1]
                for row in self.db.execute(
                    select(FirewallRule.action, func.count(FirewallRule.id))
                    .group_by(FirewallRule.action)
                ).all()
            },
            "by_landing_zone": {
                row[0]: row[1]
                for row in self.db.execute(
                    select(FirewallRule.landing_zone, func.count(FirewallRule.id))
                    .group_by(FirewallRule.landing_zone)
                ).all()
            },
        }