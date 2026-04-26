"""Azure Entra ID authentication and JWT token management."""
from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Any, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
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


class OIDCTokenInfo(BaseModel):
    """Parsed OIDC token info for auth router compatibility."""
    sub: str
    email: Optional[str] = None


async def verify_oidc_token(token: str) -> OIDCTokenInfo:
    """
    Verify an Azure AD access token and extract claims.
    
    In production, this would use the JWKS endpoint to verify the signature.
    For dev/local, it decodes a mock token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return OIDCTokenInfo(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OIDC token: {str(e)}",
        )


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active."""
    if not user.is_active:
        raise HTTPException(403, "Inactive user")
    return user
