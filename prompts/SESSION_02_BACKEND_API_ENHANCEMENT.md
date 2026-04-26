# Session 2: Backend API Enhancement

## Context

You are working on the Azure Firewall Manager application. Session 1 (Security Hardening) has been completed. Now we enhance the API with versioning, structured logging, OpenAPI documentation, and background task infrastructure.

## Project Structure (After Session 1)

```
cline-example-project05/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry (async, secure)
│   │   ├── config.py            # Environment-based config
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── logging_config.py    # NEW: Structured logging
│   │   ├── middleware/          # NEW: Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── request_id.py
│   │   │   └── error_handler.py
│   │   ├── tasks/               # NEW: Background tasks
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── notifications.py
│   │   ├── auth/
│   │   │   └── auth.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── firewalls.py
│   │   │   └── approvals.py
│   │   └── services/
│   │       ├── firewall_service.py
│   │       ├── approval_service.py
│   │       └── audit_service.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
├── docker-compose.yml
└── .env.example
```

## Tasks

### Task 2.1: Structured Logging (`backend/app/logging_config.py`)

Create new file:

```python
"""Structured JSON logging configuration."""
import logging
import sys
import json
import uuid
from datetime import datetime, timezone
from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "unknown"),
        }
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ("name", "msg", "args", "levelname", "levelno",
                           "pathname", "filename", "folder", "module",
                           "exc_info", "exc_text", "stack_info", "lineno",
                           "funcName", "created", "relativeCreated",
                           "threadName", "processName", "thread", "process",
                           "request_id"):
                if not key.startswith("_"):
                    log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging():
    """Configure application-wide logging."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Request ID logger
    logging.getLogger("app.middleware.request_id").setLevel(logging.INFO)
```

### Task 2.2: Request ID Middleware (`backend/app/middleware/request_id.py`)

Create new file:

```python
"""Request ID middleware for tracking."""
import uuid
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from app.config import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to every request/response."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(settings.REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        response = await call_next(request)
        response.headers[settings.REQUEST_ID_HEADER] = request_id
        return response
```

### Task 2.3: Error Handler Middleware (`backend/app/middleware/error_handler.py`)

Create new file:

```python
"""Consistent error response handler."""
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Consistent error response format."""
    
    def __init__(self, error: str, detail: str = "", code: str = "", 
                 field: str = "", path: str = ""):
        self.error = error
        self.detail = detail
        self.code = code
        self.field = field
        self.path = path
    
    def to_dict(self):
        result = {
            "error": self.error,
            "detail": self.detail,
        }
        if self.code:
            result["code"] = self.code
        if self.field:
            result["field"] = self.field
        if self.path:
            result["path"] = self.path
        return result


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")},
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", ""),
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "Request validation failed",
            "validation_errors": errors,
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")},
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")},
    )
```

### Task 2.4: Enhanced Schemas (`backend/app/schemas.py`)

Add pagination metadata and enhanced documentation:

```python
"""Pydantic schemas for request/response validation."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.config import Role, RuleAction, RuleStatus, ApprovalStatus, ApprovalLevel, WorkloadType, ResourceCategory


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""
    total: int
    page: int
    per_page: int
    total_pages: int
    
    @field_validator('total_pages')
    @classmethod
    def calculate_total_pages(cls, v):
        return (v + 99) // 100 if hasattr(cls, '__field_names__') else (0)


class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    items: List[Any] = Field(..., description="List of items")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    expires_in: int = 1800
    
    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    sub: str | None = None
    email: str | None = None
    roles: List[str] = Field(default_factory=list)
    workload: str | None = None
    workload_type: str | None = None


class LoginRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


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

    model_config = ConfigDict(from_attributes=True)


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


class TagResponse(BaseModel):
    id: int | None = None
    name: str | None = None
    color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    name: str
    color: str | None = None


class FirewallRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique rule name")
    description: str | None = None
    landing_zone: str = Field(..., min_length=1, max_length=255, description="Azure landing zone")
    subscription_id: str | None = None
    resource_group: str | None = None
    firewall_policy: str | None = None
    rule_collection_name: str = Field(..., min_length=1, max_length=255, description="Rule collection name")
    priority: int = Field(200, ge=100, le=10000, description="Rule priority (lower = higher priority)")
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
    approvers: List[str] | None = None
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

    model_config = ConfigDict(from_attributes=True)


class FirewallRuleListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List[FirewallRuleResponse]


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

    model_config = ConfigDict(from_attributes=True)


class ApprovalActionRequest(BaseModel):
    action: str = Field(..., description="approve or reject")
    notes: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v.lower() not in ("approve", "reject"):
            raise ValueError("Action must be 'approve' or 'reject'")
        return v


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

    model_config = ConfigDict(from_attributes=True)


class RuleFilterRequest(BaseModel):
    landing_zone: str | None = None
    status: List[str] | None = None
    action: List[str] | None = None
    category: List[str] | None = None
    workload: str | None = None
    environment: str | None = None
    search: str | None = None
    priority_min: int | None = None
    priority_max: int | None = None
    page: int = 1
    per_page: int = 50
    sort_by: str = "updated_at"
    sort_order: str = "desc"


class StatisticsResponse(BaseModel):
    """Dashboard statistics."""
    total_rules: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_action: Dict[str, int] = Field(default_factory=dict)
    by_landing_zone: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str = "unknown"
    cache: str = "unknown"
    timestamp: str
```

### Task 2.5: Stats Router (`backend/app/routers/stats.py`)

Create new file:

```python
"""Dashboard statistics API routes."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.auth.auth import get_current_user
from app.database import get_db
from app.models import FirewallRule, RuleStatus, User
from app.schemas import StatisticsResponse, HealthCheckResponse
from sqlalchemy.orm import Session

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
        row[0]: row[1]
        for row in db.execute(
            select(FirewallRule.status, func.count(FirewallRule.id))
            .group_by(FirewallRule.status)
        ).all()
    }
    
    by_action = {
        row[0]: row[1]
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
    
    return StatisticsResponse(
        total_rules=total,
        by_status=dict(by_status),
        by_action=dict(by_action),
        by_landing_zone=dict(by_landing_zone),
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
```

### Task 2.6: Export Router (`backend/app/routers/export.py`)

Create new file:

```python
"""Data export API routes."""
import logging
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
        output.write(f"{rule.id},")
        output.write(f'"{(rule.name or "").replace('"', '""')}",')
        output.write(f'"{(rule.description or "").replace('"', '""')}",')
        output.write(f"{rule.landing_zone},")
        output.write(f"{rule.rule_collection_name},")
        output.write(f"{rule.priority},")
        output.write(f"{rule.action.value if hasattr(rule.action, 'value') else rule.action},")
        output.write(f"{rule.category.value if hasattr(rule.category, 'value') else rule.category},")
        output.write(f"{rule.status.value if hasattr(rule.status, 'value') else rule.status},")
        output.write(f"{rule.created_by},")
        output.write(f"{rule.created_at}\n")
    
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
            "Content-Disposition": f'attachment; filename="firewall_rules_{__import__("datetime").date.today()}.csv"'
        },
    )
```

### Task 2.7: Celery Tasks (`backend/app/tasks/base.py`)

Create new file:

```python
"""Celery task configuration."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "firewall_manager",
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
```

```python
"""Notification tasks."""
from app.tasks.base import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="send.notification")
def send_notification(self, user_id: str, notification_type: str, message: str):
    """Send a notification to a user."""
    logger.info(f"Sending {notification_type} notification to user {user_id}: {message}")
    # TODO: Implement actual notification sending
    return {"status": "sent", "user_id": user_id, "type": notification_type}


@celery_app.task(bind=True, name="process.approval")
def process_approval(self, rule_id: int, approver_id: str):
    """Process approval notification."""
    logger.info(f"Processing approval for rule {rule_id} by user {approver_id}")
    return {"status": "processed", "rule_id": rule_id}
```

### Task 2.8: Update `backend/app/main.py`

Add versioned routers and new middleware:

```python
# Add these router registrations:
app.include_router(auth.router, prefix="/api/v1")
app.include_router(firewalls.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
```

### Task 2.9: Update `backend/requirements.txt`

```
# Add for Session 2
celery[redis]==5.3.6
pandas==2.1.4
```

### Task 2.10: Update `docker-compose.yml`

Add Celery worker service:

```yaml
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fw-portal-celery
    command: celery -A app.tasks.base.celery_app worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - backend
    networks:
      - fw-portal-net
    restart: unless-stopped
```

## Testing

After completing all changes:

```bash
cd backend
pip install -r requirements.txt

# Test stats endpoint
curl http://localhost:8000/api/v1/stats/dashboard -H "Authorization: Bearer <token>"

# Test export endpoint
curl http://localhost:8000/api/v1/export/rules.csv -H "Authorization: Bearer <token>"

# Test health endpoint
curl http://localhost:8000/api/v1/stats/health
```

## Acceptance Criteria

- [ ] All API routes use `/api/v1/` prefix
- [ ] Structured JSON logging is active
- [ ] Request ID propagates through all requests
- [ ] Stats endpoint returns dashboard statistics
- [ ] Export endpoint generates valid CSV
- [ ] Celery worker runs and processes tasks
- [ ] OpenAPI docs are enhanced with descriptions
- [ ] Docker Compose starts all services