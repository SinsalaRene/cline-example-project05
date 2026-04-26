"""Dashboard statistics API routes."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.database import get_db
from app.models import FirewallRule, RuleStatus, User
from app.schemas import StatisticsResponse, HealthCheckResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/dashboard", response_model=StatisticsResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get dashboard statistics for all users with view access."""
    total = db.execute(select(func.count(FirewallRule.id))).scalar() or 0
    
    by_status = {
        str(row[0]): row[1]
        for row in db.execute(
            select(FirewallRule.status, func.count(FirewallRule.id))
            .group_by(FirewallRule.status)
        ).all()
    }
    
    by_action = {
        str(row[0]): row[1]
        for row in db.execute(
            select(FirewallRule.action, func.count(FirewallRule.id))
            .group_by(FirewallRule.action)
        ).all()
    }
    
    by_landing_zone = {
        row[0]: row[1]
        for row in db.execute(
            select(FirewallRule.landing_zone, func.count(FirewallRule.id))
            .group_by(FirewallRule.landing_zone)
        ).all()
    }
    
    by_category = {
        str(row[0]): row[1]
        for row in db.execute(
            select(FirewallRule.category, func.count(FirewallRule.id))
            .group_by(FirewallRule.category)
        ).all()
    }
    
    return StatisticsResponse(
        total_rules=total,
        by_status=dict(by_status),
        by_action=dict(by_action),
        by_landing_zone=dict(by_landing_zone),
        by_category=dict(by_category),
    )


@router.get("/health", response_model=HealthCheckResponse)
async def detailed_health_check(
    db: Session = Depends(get_db),
):
    """Detailed health check with dependency status."""
    db_status = "healthy"
    try:
        db.execute(select(func.count(FirewallRule.id)))
    except Exception:
        db_status = "unhealthy"
    
    return HealthCheckResponse(
        status="ok" if db_status == "healthy" else "degraded",
        version="2.0.0",
        environment="development",
        database=db_status,
        cache="unknown",
        timestamp=__import__('datetime').datetime.utcnow().isoformat(),
    )