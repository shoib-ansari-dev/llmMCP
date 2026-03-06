"""
Database Module
PostgreSQL database with SQLAlchemy ORM.
"""

from .connection import (
    get_db,
    init_db,
    close_db,
    engine,
    SessionLocal,
    Base
)
from .models import (
    User,
    Document,
    DocumentChunk,
    Subscription,
    UsageLog,
    APIKey,
    PasswordResetToken,
    RefreshToken
)
from .repositories import (
    UserRepository,
    DocumentRepository,
    SubscriptionRepository,
    UsageRepository,
    APIKeyRepository
)

__all__ = [
    # Connection
    "get_db",
    "init_db",
    "close_db",
    "engine",
    "SessionLocal",
    "Base",
    # Models
    "User",
    "Document",
    "DocumentChunk",
    "Subscription",
    "UsageLog",
    "APIKey",
    "PasswordResetToken",
    "RefreshToken",
    # Repositories
    "UserRepository",
    "DocumentRepository",
    "SubscriptionRepository",
    "UsageRepository",
    "APIKeyRepository",
]

