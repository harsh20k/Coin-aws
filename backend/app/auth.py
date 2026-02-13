from functools import lru_cache
from typing import Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _get_jwks_cached():
    """Sync fetch JWKS (cached). Use in startup or first request."""
    with httpx.Client() as client:
        r = client.get(settings.cognito_jwks_url)
        r.raise_for_status()
        return r.json()


async def _get_jwks():
    """Async wrapper; fetches and caches JWKS."""
    try:
        return _get_jwks_cached()
    except Exception:
        async with httpx.AsyncClient() as client:
            r = await client.get(settings.cognito_jwks_url)
            r.raise_for_status()
            return r.json()


def _verify_cognito_token(token: str) -> dict:
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            raise JWTError("missing kid")
        jwks = _get_jwks_cached()
        key_dict = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_dict:
            raise JWTError("key not found")
        key = jwk.construct(key_dict)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            options={"verify_exp": True},
        )
        issuer = settings.cognito_issuer
        if payload.get("iss") != issuer:
            raise JWTError("invalid issuer")
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    if not credentials or credentials.credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    token = credentials.credentials
    if not settings.cognito_user_pool_id or not settings.cognito_app_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured",
        )
    try:
        payload = _verify_cognito_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing sub in token")
    result = await db.execute(select(User).where(User.cognito_sub == sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Call PUT /users/me to register.",
        )
    return user.id


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Validate JWT and return payload (for upsert user). Does not require user in DB."""
    if not credentials or credentials.credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    token = credentials.credentials
    if not settings.cognito_user_pool_id or not settings.cognito_app_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured",
        )
    try:
        return _verify_cognito_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[UUID]:
    """Use only for routes that can work without auth (e.g. health)."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user_id(credentials, db)
    except HTTPException:
        return None
