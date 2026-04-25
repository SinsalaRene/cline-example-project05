"""Audit logging service for tracking all changes to firewall rules and user actions."""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models import AuditLog, FirewallRule


class AuditService:
    """Handles audit logging operations."""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filtering and pagination."""
        query = select(AuditLog)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if action:
            query = query.where(AuditLog.action == action)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        # Apply pagination
        query = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page)
        logs = self.db.execute(query).scalars().all()

        return logs, total or 0

    def get_rule_audit_history(self, rule_id: int, page: int = 1, per_page: int = 50) -> tuple[list[AuditLog], int]:
        """Get complete audit history for a specific firewall rule."""
        return self.get_logs(entity_type="firewall_rule", entity_id=rule_id, page=page, per_page=per_page)