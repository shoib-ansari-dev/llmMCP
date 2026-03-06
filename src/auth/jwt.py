"""
JWT Token Utilities
Handles token creation, validation, and refresh.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets

from .config import get_auth_config
from .models import TokenPayload, TokenResponse


def create_access_token(user_id: str, email: str) -> str:
    """Create a new access token."""
    config = get_auth_config()

    now = datetime.utcnow()
    expire = now + timedelta(minutes=config.access_token_expire_minutes)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access"
    }

    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a new refresh token."""
    config = get_auth_config()

    now = datetime.utcnow()
    expire = now + timedelta(days=config.refresh_token_expire_days)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh"
    }

    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def create_tokens(user_id: str, email: str) -> TokenResponse:
    """Create both access and refresh tokens."""
    config = get_auth_config()

    return TokenResponse(
        access_token=create_access_token(user_id, email),
        refresh_token=create_refresh_token(user_id, email),
        token_type="bearer",
        expires_in=config.access_token_expire_minutes * 60
    )


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """
    Verify a JWT token.

    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenPayload if valid, None if invalid
    """
    config = get_auth_config()

    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm]
        )

        # Check token type
        if payload.get("type") != token_type:
            return None

        return TokenPayload(**payload)

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[TokenResponse]:
    """
    Create a new access token using a refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        New TokenResponse if valid, None if invalid
    """
    payload = verify_token(refresh_token, token_type="refresh")

    if not payload:
        return None

    return create_tokens(payload.sub, payload.email)


def create_password_reset_token(user_id: str, email: str) -> str:
    """Create a password reset token (short-lived)."""
    config = get_auth_config()

    now = datetime.utcnow()
    expire = now + timedelta(hours=1)  # 1 hour expiry

    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "password_reset"
    }

    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def verify_password_reset_token(token: str) -> Optional[TokenPayload]:
    """Verify a password reset token."""
    return verify_token(token, token_type="password_reset")


def generate_state_token() -> str:
    """Generate a random state token for OAuth."""
    return secrets.token_urlsafe(32)
