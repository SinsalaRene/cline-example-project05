# Session 1: Security Hardening & Configuration Management

## Context

You are working on the Azure Firewall Manager application - a Python FastAPI backend with Angular frontend for managing Azure firewall rules. This session focuses on security hardening.

## Project Structure

```
cline-example-project05/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Configuration settings
│   │   ├── database.py      # DB connection
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── auth/
│   │   │   └── auth.py      # Auth middleware
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
│   ├── src/app/
│   └── Dockerfile
├── infrastructure/
├── docker-compose.yml
└── .env.example
```

## Current Issues to Fix

1. **Hardcoded secrets** in `docker-compose.yml` and `backend/app/config.py`
2. **Synchronous database engine** in `backend/app/database.py`
3. **No security headers** or request ID tracking
4. **No rate limiting** on auth endpoints
5. **No environment validation** at startup
6. **Weak token refresh** mechanism

## Tasks

### Task 1.1: Environment-Based Configuration (`backend/app/config.py`)

Replace the current config with proper environment-based settings:

```python
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional, List
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class ApprovalLevel(str, Enum):
    SECURITY = "security"
    WORKLOAD = "workload"
    SECURITY_AND_WORKLOAD = "security_and_workload"


class Role(str, Enum):
    ADMIN = "admin"
    SECURITY_STAKEHOLDER = "security_stakeholder"
    WORKLOAD_STAKEHOLDER = "workload_stakeholder"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Azure Firewall Manager"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Database - use environment variables with defaults for local dev
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/firewall_manager",
        description="Database connection URL"
    )
    DATABASE_SSL_MODE: str = "prefer"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Azure Entra ID Configuration
    AZURE_TENANT_ID: str = Field(default="", description="Azure AD Tenant ID")
    AZURE_CLIENT_ID: str = Field(default="", description="Azure AD Client ID")
    AZURE_CLIENT_SECRET: str = Field(default="", description="Azure AD Client Secret")
    AZURE_INSTANCE_METADATA: str = "https://login.microsoftonline.com/common/.well-known/openid-configuration"

    # JWT Settings
    SECRET_KEY: str = Field(default="", description="JWT secret key - MUST be set in production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Origins
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost:3000"

    # Security
    RATE_LIMIT_AUTH: str = "5/minute"  # Auth endpoint rate limit
    RATE_LIMIT_DEFAULT: str = "100/minute"
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Approval Workflow Settings
    DEFAULT_APPROVAL_LEVEL: ApprovalLevel = ApprovalLevel.SECURITY_AND_WORKLOAD
    AUTO_APPROVE_AFTER_DAYS: int = 30

    @property
    def allowed_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode='after')
    def validate_production_settings(self):
        """Validate required settings for production."""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if not self.AZURE_TENANT_ID:
                raise ValueError("AZURE_TENANT_ID must be set in production")
            if not self.AZURE_CLIENT_ID:
                raise ValueError("AZURE_CLIENT_ID must be set in production")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### Task 1.2: Async Database (`backend/app/database.py`)

Replace with async SQLAlchemy:

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI async dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_sync():
    """Sync helper for non-async contexts (e.g., migrations)."""
    import sqlalchemy
    sync_engine = create_async_engine(
        settings.DATABASE_URL.replace("asyncpg", "psycopg2"),
        pool_pre_ping=True,
    )
    session = async_sessionmaker(sync_engine, expire_on_commit=False)
    return session()


async def init_db():
    """Initialize database tables from models."""
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_test_db():
    """Get a test database session (for pytest)."""
    async with AsyncSessionLocal() as session:
        yield session
```

### Task 1.3: Security Middleware (`backend/app/main.py`)

Add security middleware and request ID tracking:

```python
"""Main FastAPI application entry point."""
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import engine, init_db, get_db
from app.routers import auth, firewalls, approvals

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)


async def request_id_generator():
    """Generate unique request IDs."""
    return str(uuid.uuid4())


async def log_request(request: Request, response: Response, process_time: float = 0):
    """Log all requests with request ID."""
    request_id = request.headers.get(settings.REQUEST_ID_HEADER, "unknown")
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s "
        f"RequestID: {request_id}"
    )


# ─── Application lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables and seed on startup."""
    logger.info("Starting application...")
    await init_db()
    logger.info("Database tables created")

    # Seed default users if not present
    from sqlalchemy import select
    from app.models import User
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        admin = await db.execute(
            select(User).where(User.oidc_sub == "dev-sub-001")
        )
        if not admin.scalar_one_or_none():
            admin_user = User(
                oidc_sub="dev-sub-001",
                email="admin@example.com",
                display_name="Admin User",
                role="admin",
                workload="default",
                is_active=True,
            )
            db.add(admin_user)
            await db.commit()
            logger.info("Seeded admin user")

        security_user = await db.execute(
            select(User).where(User.oidc_sub == "security-sub-001")
        )
        if not security_user.scalar_one_or_none():
            sec_user = User(
                oidc_sub="security-sub-001",
                email="security@example.com",
                display_name="Security Reviewer",
                role="security_stakeholder",
                workload="default",
                is_active=True,
            )
            db.add(sec_user)
            await db.commit()
            logger.info("Seeded security user")

        workload_user = await db.execute(
            select(User).where(User.oidc_sub == "workload-sub-001")
        )
        if not workload_user.scalar_one_or_none():
            wl_user = User(
                oidc_sub="workload-sub-001",
                email="workload@example.com",
                display_name="Workload Owner",
                role="workload_stakeholder",
                workload="default",
                is_active=True,
            )
            db.add(wl_user)
            await db.commit()
            logger.info("Seeded workload user")

    yield
    logger.info("Shutting down application")


# ─── Create FastAPI app ────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Azure Firewall Rule Management Platform",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Security Middleware ────────────────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call):
    """Add security headers to all responses."""
    response = await call(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    
    # Request ID
    request_id = request.headers.get(settings.REQUEST_ID_HEADER, str(uuid.uuid4()))
    response.headers["X-Request-ID"] = request_id
    
    # Rate limit headers for auth endpoints
    if "/auth" in request.url.path:
        response.headers["X-RateLimit-Limit"] = "5"
        response.headers["X-RateLimit-Window"] = "60"
    
    return response


# ─── Request ID Middleware ──────────────────────────────────────────────────────

@app.middleware("http")
async def add_request_id(request: Request, call):
    """Ensure request ID is propagated through the request."""
    request_id = request.headers.get(settings.REQUEST_ID_HEADER)
    if not request_id:
        request_id = str(uuid.uuid4())
        request.headers[settings.REQUEST_ID_HEADER] = request_id
    
    from starlette.background import BackgroundTask
    
    async def log_response():
        await call(request)
    
    response = await call(request)
    response.headers[settings.REQUEST_ID_HEADER] = request_id
    return response


# ─── Health Check ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ─── Register Routers ──────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/v1")
app.include_router(firewalls.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
```

### Task 1.4: Enhanced Auth (`backend/app/auth/auth.py`)

Add token refresh with rotation and brute-force protection:

```python
"""Azure Entra ID authentication and JWT token management."""
from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Any, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt, JWTClaimsCheck
from jose.backends.base import BaseRSAKey
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings, Role
from app.database import get_db_session
from app.models import User
from app.schemas import TokenData

logger = logging.getLogger(__name__)


class AzureTokenInfo(BaseModel):
    """Parsed Azure AD access token claims."""
    iss: str
    sub: str
    iss_valid_until_utc: dt.datetime
    client_id: str
    tenant_id: str
    email: Optional[str] = None
    roles: list[str] | None = None

    def is_expired(self, leeway: int = 60) -> bool:
        now = dt.datetime.utcnow()
        return now > (self.iss_valid_until_utc - dt.timedelta(seconds=leeway))


def create_access_token(data: dict, expires_delta: Optional[dt.timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + (
        expires_delta if expires_delta else dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16),  # Unique token ID for revocation
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a refresh token with longer expiry."""
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_token(request: Request) -> str:
    """Extract the bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authorization header missing or invalid"
    )


async def get_current_user(request: Request) -> User:
    """FastAPI dependency that returns the current authenticated user."""
    token = await get_token(request)
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject"
            )
        roles = payload.get("roles", [])
        workload = payload.get("workload")
        workload_type = payload.get("workload_type")
    except HTTPException:
        raise

    db = get_db_session()
    try:
        user = db.execute(select(User).where(User.oidc_sub == sub)).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is disabled")
        return user
    finally:
        db.close()


def require_role(*required_roles: str):
    """Dependency factory that requires at least one of the given roles."""
    async def _check_role(user: User = Depends(get_current_user)) -> User:
        user_role = user.role if user.role else "viewer"
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_roles}, Got: {user_role}"
            )
        return user
    return _check_role


def require_any_role(*required_roles: str):
    """Require the user to have ANY of the specified roles (OR logic)."""
    async def _check(user: User = Depends(get_current_user)) -> User:
        user_role = user.role if user.role else "viewer"
        if user_role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Need any of {required_roles}"
            )
        return user
    return _check


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active."""
    if not user.is_active:
        raise HTTPException(403, "Inactive user")
    return user
```

### Task 1.5: Update `.env.example`

Create comprehensive `.env.example`:

```bash
# Application
APP_NAME="Azure Firewall Manager"
VERSION="1.0.0"
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/firewall_manager
DATABASE_SSL_MODE=prefer
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# Azure Entra ID
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_INSTANCE_METADATA=https://login.microsoftonline.com/common/.well-known/openid-configuration

# JWT
SECRET_KEY=change-me-to-a-random-secret-key-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:4200,http://localhost:3000

# Rate Limiting
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_DEFAULT=100/minute

# Approval Settings
DEFAULT_APPROVAL_LEVEL=security_and_workload
AUTO_APPROVE_AFTER_DAYS=30
```

### Task 1.6: Update `docker-compose.yml`

Replace hardcoded secrets with env var references:

```yaml
# Update these sections:
environment:
  - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fw_portal
  - REDIS_URL=redis://redis:6379/0
  - SECRET_KEY=${JWT_SECRET_KEY:-change-me-in-production}
  - DEBUG=True
  - ENVIRONMENT=development
  - AUTH_PROVIDER=azure_ad
  - AZURE_TENANT_ID=${AZURE_TENANT_ID}
  - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
  - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
```

### Task 1.7: Update `backend/requirements.txt`

Add new dependencies:

```
# Existing
fastapi==0.115.0
uvicorn==0.32.0
sqlalchemy==2.0.35
alembic==1.14.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.12
httpx==0.27.2
psycopg2-binary==2.9.9
bcrypt==4.2.0
python-dateutil==2.9.0

# Add for Session 1
asyncpg==0.30.0
slowapi==0.1.9
```

### Task 1.8: Update README.md

Add configuration section:

```markdown
## Configuration

Copy `.env.example` to `.env` and configure the values:

```bash
cp .env.example .env
```

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `AZURE_TENANT_ID` | Azure AD Tenant ID (production) | Yes |
| `AZURE_CLIENT_ID` | Azure AD Client ID (production) | Yes |
| `AZURE_CLIENT_SECRET` | Azure AD Client Secret (production) | Yes |
```

## Testing

After making all changes, verify:

1. `cd backend && python -c "from app.config import settings; print(settings)"`
2. `cd backend && python -c "from app.database import engine; print(engine)"`
3. `docker compose up --build` should start without hardcoded secret errors
4. `curl http://localhost:8000/health` returns status ok

## Acceptance Criteria

- [ ] All secrets come from environment variables
- [ ] Production validation raises errors for missing secrets
- [ ] Async database engine is working
- [ ] Security headers are present in all responses
- [ ] Request ID is propagated through requests
- [ ] Rate limiting is configured for auth endpoints
- [ ] Token refresh includes JTI for revocation tracking
- [ ] `.env.example` documents all variables
- [ ] docker-compose.yml uses env var references
- [ ] README.md updated with configuration guide