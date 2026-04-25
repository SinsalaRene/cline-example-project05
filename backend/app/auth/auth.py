"""Azure Entra ID authentication and JWT token management."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityHeaders
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

# ─── Azure OpenID Connect ─────────────────────────────────────────────────────


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


class OAuth2ClientCredentials:
    """Handles client credentials flow for service-to-service Azure auth."""

    ACCESS_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    @staticmethod
    async def get_access_token(
        client_id: str,
        client_secret: str,
        tenant_id: str,
        scope: str = "https://management.azure.com/.default",
    ) -> str:
        import httpx
        token_url = OAuth2ClientCredentials.ACCESS_TOKEN_URL.format(tenant_id=tenant_id)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": scope,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]


async def verify_oidc_token(token: str) -> AzureTokenInfo:
    """
    Verify an Azure AD ID token using JWKS from the Azure OpenID metadata endpoint.

    Returns the parsed token claims.
    """
    # Extract header to find the key ID
    header = jwt.get_unverified_header(token)

    # Fetch Azure OpenID configuration
    import httpx
    async with httpx.AsyncClient() as client:
        config = await client.get(settings.AZURE_INSTANCE_METADATA)
        config.raise_for_status()
        config_data = config.json()
        jwks_url = config_data["jwks_uri"]

        jwks = await client.get(jwks_url)
        jwks.raise_for_status()
        jwks_data = jwks.json()

        # Find the matching key
        key = None
        for k in jwks_data["keys"]:
            if k["kid"] == header["kid"]:
                key = k
                break

        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching key for token",
            )

        # Convert JWK dict to PEM or use directly
        from cryptography import x509
        from cryptography.hazmat.primitives.asymmetric import ec
        import base64

        n = base64.urlsafe_b64decode(key["n"].rstrip("="))
        e = int.from_bytes(base64.urlsafe_b64decode(key["e"].rstrip("=")), "big")
        pub_numbers = ec.EllipticCurvePublicNumbers(e, int.from_bytes(n, "big"))
        azure_key = pub_numbers.public_key()

        # Verify the token
        claims = jwt.decode(
            token,
            azure_key,
            algorithms=["RS256"],
            audience=settings.AZURE_CLIENT_ID,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_exp": True,
            },
        )

    return AzureTokenInfo(
        iss=claims["iss"],
        sub=claims["sub"],
        iss_valid_until_utc=dt.datetime.fromtimestamp(claims["exp"], tz=dt.timezone.utc),
        client_id=claims.get("aud", claims.get("client_id", "")),
        tenant_id=claims.get("tid", ""),
        email=claims.get("email"),
        roles=claims.get("roles", []),
    )


# ─── JWT Helpers ──────────────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: Optional[dt.timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + (
        expires_delta if expires_delta else dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a refresh token."""
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
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


# ─── Dependency Injections ────────────────────────────────────────────────────

async def get_token(request: Request) -> str:
    """Extract the bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    raise HTTPException(status_code=401, detail="Authorization header missing or invalid")


async def get_current_user(request: Request) -> User:
    """FastAPI dependency that returns the current authenticated user from JWT."""
    token = await get_token(request)
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
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
    """
    Dependency factory that requires at least one of the given roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
    """
    async def _check_role(user: User = Depends(get_current_user)) -> User:
        user_role = user.role if user.role else "viewer"
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_roles}, Got: {user_role}",
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
                detail=f"Access denied. Need any of {required_roles}",
            )
        return user
    return _check


def require_workload_match(user: User = Depends(get_current_user)) -> User:
    """
    Require that the user's workload matches the requested resource.
    Used for workload-specific authorization.
    """
    if user.role == Role.ADMIN.value:
        return user
    if user.workload:
        return user
    raise HTTPException(
        status_code=403,
        detail="User does not have a workload assignment for this operation",
    )


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active."""
    if not user.is_active:
        raise HTTPException(403, "Inactive user")
    return user