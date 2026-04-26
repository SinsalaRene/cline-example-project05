"""Data export API routes."""
import logging
from datetime import date
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func

from app.auth.auth import get_current_user, require_role
from app.database import get_db
from app.models import FirewallRule, User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])


def rules_to_csv(rules: list) -> str:
    """Convert firewall rules to CSV format."""
    output = StringIO()
    output.write("id,name,description,landing_zone,rule_collection_name,priority,action,category,status,created_by,created_at\n")
    
    for rule in rules:
        name = (rule.name or "").replace('"', '""')
        desc = (rule.description or "").replace('"', '""')
        action = rule.action.value if hasattr(rule.action, 'value') else rule.action
        category = rule.category.value if hasattr(rule.category, 'value') else rule.category
        status = rule.status.value if hasattr(rule.status, 'value') else rule.status
        created_at = rule.created_at.isoformat() if rule.created_at else ""
        
        output.write(f'{rule.id},"{name}","{desc}",{rule.landing_zone},{rule.rule_collection_name},{rule.priority},{action},{category},{status},{rule.created_by},{created_at}\n')
    
    output.seek(0)
    return output.getvalue()


@router.get("/rules.csv")
async def export_rules_csv(
    landing_zone: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "reviewer")),
):
    """Export firewall rules as CSV."""
    query = select(FirewallRule)
    if landing_zone:
        query = query.where(FirewallRule.landing_zone == landing_zone)
    
    rules = db.execute(query).scalars().all()
    csv_content = rules_to_csv(rules)
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="firewall_rules_{date.today()}.csv"'
        },
    )