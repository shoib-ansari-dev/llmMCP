"""
Authentication Dependencies
FastAPI dependencies for authentication.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .config import get_auth_config
from .jwt import verify_token
from .models import TokenPayload, DevUser, UserResponse, AuthProvider
from .store import get_user_store

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserResponse]:
    """
    Get current user if authenticated, None otherwise.
    In dev mode, returns a dev user.
    """
    config = get_auth_config()

    # Dev mode - return dev user without authentication
    if config.dev_mode:
        dev_user = DevUser()
        return UserResponse(
            id=dev_user.id,
            email=dev_user.email,
            name=dev_user.name,
            provider=dev_user.provider,
            is_active=dev_user.is_active,
            is_verified=dev_user.is_verified,
            created_at=__import__('datetime').datetime.utcnow()
        )

    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if not payload:
        return None

    # Get user from store
    store = get_user_store()
    user = await store.get_by_id(payload.sub)

    if not user or not user.is_active:
        return None

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        provider=user.provider,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """
    Get current authenticated user.
    Raises 401 if not authenticated.
    In dev mode, returns a dev user.
    """
    config = get_auth_config()

    # Dev mode - return dev user without authentication
    if config.dev_mode:
        dev_user = DevUser()
        return UserResponse(
            id=dev_user.id,
            email=dev_user.email,
            name=dev_user.name,
            provider=dev_user.provider,
            is_active=dev_user.is_active,
            is_verified=dev_user.is_verified,
            created_at=__import__('datetime').datetime.utcnow()
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user from store
    store = get_user_store()
    user = await store.get_by_id(payload.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        provider=user.provider,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


async def get_verified_user(
    user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user and verify their email is verified.
    Raises 403 if not verified.
    """
    config = get_auth_config()

    # Skip verification check in dev mode
    if config.dev_mode:
        return user

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )

    return user

