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
        if not await admin.scalar_one_or_none():
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
        if not await security_user.scalar_one_or_none():
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
        if not await workload_user.scalar_one_or_none():
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