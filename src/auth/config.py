"""
Authentication Configuration
Handles JWT settings, Google OAuth, and development mode.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthConfig:
    """Authentication configuration."""

    # Development mode - bypasses authentication
    dev_mode: bool = False

    # JWT Settings
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    # Email Settings (for password reset)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Frontend URL (for password reset links)
    frontend_url: str = "http://localhost:3000"

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load configuration from environment variables."""
        return cls(
            # Dev mode - set to true for local development
            dev_mode=os.getenv("AUTH_DEV_MODE", "false").lower() == "true",

            # JWT
            jwt_secret=os.getenv("JWT_SECRET", "dev-secret-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),

            # Google OAuth
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            google_redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"),

            # Email (SMTP)
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from_email=os.getenv("SMTP_FROM_EMAIL", ""),

            # Frontend
            frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
        )


# Singleton config instance
_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """Get authentication configuration."""
    global _config
    if _config is None:
        _config = AuthConfig.from_env()
    return _config

