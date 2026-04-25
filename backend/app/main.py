"""Main FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import auth, firewalls, approvals

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables and seed on startup."""
    logger.info("Starting application...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Seed default users if not present
    from sqlalchemy import select
    from app.database import get_db
    from app.models import User

    db = next(get_db())
    admin = db.execute(
        select(User).where(User.oidc_sub == "dev-sub-001")
    ).scalar_one_or_none()
    if not admin:
        admin = User(
            oidc_sub="dev-sub-001",
            email="admin@example.com",
            display_name="Admin User",
            role="admin",
            workload="default",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Seeded admin user")

    security_user = db.execute(
        select(User).where(User.oidc_sub == "security-sub-001")
    ).scalar_one_or_none()
    if not security_user:
        security_user = User(
            oidc_sub="security-sub-001",
            email="security@example.com",
            display_name="Security Reviewer",
            role="security_stakeholder",
            workload="default",
            is_active=True,
        )
        db.add(security_user)
        db.commit()
        logger.info("Seeded security user")

    workload_user = db.execute(
        select(User).where(User.oidc_sub == "workload-sub-001")
    ).scalar_one_or_none()
    if not workload_user:
        workload_user = User(
            oidc_sub="workload-sub-001",
            email="workload@example.com",
            display_name="Workload Owner",
            role="workload_stakeholder",
            workload="default",
            is_active=True,
        )
        db.add(workload_user)
        db.commit()
        logger.info("Seeded workload user")

    db.close()

    yield

    # Shutdown cleanup
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Azure Firewall Rule Management Platform - API for managing Azure Firewall rules with RBAC, approval workflows, and audit logging.",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "ok", "version": settings.APP_VERSION}


# ─── Root ──────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else None,
    }


# ─── Middleware for CORS preflight & timing ────────────────────────────────────

@app.middleware("http")
async def add_cors_headers(request: Request, call):
    """Add CORS headers to all responses."""
    response = await call(request)
    response.headers["Access-Control-Allow-Origin"] = settings.FRONTEND_URL
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# ─── Register Routers ──────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(firewalls.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")


# ─── Error Handlers ────────────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status": 500,
        },
    )