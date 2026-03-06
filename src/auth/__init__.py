"""
Authentication Module
Provides user authentication with email/password and Google OAuth.
"""

from .config import AuthConfig, get_auth_config
from .models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordReset, PasswordResetConfirm, AuthProvider, DevUser
)
from .jwt import create_tokens, verify_token, refresh_access_token
from .password import hash_password, verify_password
from .store import UserStore, get_user_store
from .google_oauth import GoogleOAuth, get_google_oauth
from .email_service import EmailService, get_email_service
from .dependencies import get_current_user, get_current_user_optional, get_verified_user
from .router import router as auth_router

__all__ = [
    # Config
    "AuthConfig",
    "get_auth_config",

    # Models
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "PasswordReset",
    "PasswordResetConfirm",
    "AuthProvider",
    "DevUser",

    # JWT
    "create_tokens",
    "verify_token",
    "refresh_access_token",

    # Password
    "hash_password",
    "verify_password",

    # Store
    "UserStore",
    "get_user_store",

    # Google OAuth
    "GoogleOAuth",
    "get_google_oauth",

    # Email
    "EmailService",
    "get_email_service",

    # Dependencies
    "get_current_user",
    "get_current_user_optional",
    "get_verified_user",

    # Router
    "auth_router",
]

