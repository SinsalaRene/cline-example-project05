"""Authentication API routes."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.auth import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.auth import verify_oidc_token
from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login-azure")
async def login_azure(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Azure Entra ID OAuth2 authorization code flow.

    In production, this would exchange the code for an ID token via the
    Azure token endpoint, then verify it and create a session JWT.

    For local/dev, it creates a mock user if not found.
    """
    # In production:
    # 1. Exchange code for ID token
    # 2. Verify ID token signature
    # 3. Extract claims (sub, email, etc.)
    # 4. Look up or create user in our DB
    # 5. Issue our own JWT

    # For local/dev: simulate the flow
    if settings.DEBUG and not settings.AZURE_CLIENT_ID:
        # Mock user for local development
        user = db.execute(
            select(User).where(User.email == "dev@example.com")
        ).scalar_one_or_none()

        if not user:
            user = User(
                oidc_sub="dev-sub-001",
                email="dev@example.com",
                display_name="Developer User",
                role="admin",
                workload="default",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    else:
        # Production: verify the Azure token
        try:
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.split(" ")[1] if " " in auth_header else code
            token_info = await verify_oidc_token(token)

            user = db.execute(
                select(User).where(User.oidc_sub == token_info.sub)
            ).scalar_one_or_none()

            if not user:
                user = User(
                    oidc_sub=token_info.sub,
                    email=token_info.email or f"{token_info.sub}@azure.external",
                    display_name=token_info.sub,
                    role="viewer",
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        except Exception as e:
            logger.error(f"Auth error: {e}")
            raise HTTPException(401, "Failed to authenticate with Azure")

    # Issue our own JWT
    access_token = create_access_token({
        "sub": user.oidc_sub,
        "email": user.email,
        "role": user.role,
        "workload": user.workload,
        "workload_type": user.workload_type.value if user.workload_type else None,
    })

    refresh_token = create_refresh_token({
        "sub": user.oidc_sub,
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "workload": user.workload,
        },
    }


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    """Refresh an access token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")

        user = db.execute(
            select(User).where(User.oidc_sub == payload["sub"])
        ).scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(401, "User not found or inactive")

        new_access = create_access_token({
            "sub": user.oidc_sub,
            "email": user.email,
            "role": user.role,
            "workload": user.workload,
        })

        return {
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, f"Invalid refresh token: {str(e)}")


@router.get("/me")
async def get_current_user_info(
    user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "workload": user.workload,
        "workload_type": user.workload_type.value if user.workload_type else None,
        "is_active": user.is_active,
    }