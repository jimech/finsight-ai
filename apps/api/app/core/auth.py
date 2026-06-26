from functools import lru_cache
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.types import AuthenticatedUser
from app.db.session import get_db
from app.models.user import User
from app.services.users import get_or_create_user_from_auth

_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_email_from_claims(claims: Dict[str, Any]) -> Optional[str]:
    email = claims.get("email")
    if isinstance(email, str) and email:
        return email

    for key in ("primary_email_address", "email_address"):
        value = claims.get(key)
        if isinstance(value, str) and value:
            return value

    return None


@lru_cache
def _get_jwks_client() -> PyJWKClient:
    if not settings.clerk_jwks_url:
        raise RuntimeError("CLERK_JWKS_URL is not configured")
    return PyJWKClient(settings.clerk_jwks_url)


def _verify_clerk_token(token: str) -> Dict[str, Any]:
    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not configured",
        )

    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    claims = _verify_clerk_token(credentials.credentials)
    clerk_user_id = claims.get("sub")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return AuthenticatedUser(
        clerk_user_id=clerk_user_id,
        email=_extract_email_from_claims(claims),
        claims=claims,
    )


def get_current_db_user(
    authenticated_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return get_or_create_user_from_auth(db, authenticated_user)
