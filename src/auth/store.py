"""
User Store
Database-backed user storage with SQLite (local) or PostgreSQL (production).
Falls back to in-memory storage if database is not available.
"""

from typing import Dict, Optional
from datetime import datetime
import uuid
import logging

from .models import UserInDB, AuthProvider
from .password import hash_password

logger = logging.getLogger(__name__)


class InMemoryUserStore:
    """
    In-memory user store for fallback.
    Used when database is not configured.
    """

    def __init__(self):
        self._users: Dict[str, UserInDB] = {}
        self._email_index: Dict[str, str] = {}  # email -> user_id
        self._google_index: Dict[str, str] = {}  # google_id -> user_id

    async def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        name: Optional[str] = None,
        provider: AuthProvider = AuthProvider.EMAIL,
        google_id: Optional[str] = None,
        is_verified: bool = False
    ) -> UserInDB:
        """Create a new user."""
        # Check if email already exists
        if email.lower() in self._email_index:
            raise ValueError("Email already registered")

        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        user = UserInDB(
            id=user_id,
            email=email.lower(),
            name=name,
            password_hash=hash_password(password) if password else None,
            provider=provider,
            google_id=google_id,
            is_active=True,
            is_verified=is_verified,
            created_at=now,
            updated_at=now
        )

        self._users[user_id] = user
        self._email_index[email.lower()] = user_id

        if google_id:
            self._google_index[google_id] = user_id

        return user

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        user_id = self._email_index.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None

    async def get_by_google_id(self, google_id: str) -> Optional[UserInDB]:
        """Get user by Google ID."""
        user_id = self._google_index.get(google_id)
        if user_id:
            return self._users.get(user_id)
        return None

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user's password."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        return True

    async def verify_email(self, user_id: str) -> bool:
        """Mark user's email as verified."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.is_verified = True
        user.updated_at = datetime.utcnow()
        return True

    async def link_google_account(self, user_id: str, google_id: str) -> bool:
        """Link Google account to existing user."""
        user = self._users.get(user_id)
        if not user:
            return False

        user.google_id = google_id
        user.updated_at = datetime.utcnow()
        self._google_index[google_id] = user_id
        return True


class DatabaseUserStore:
    """
    Database-backed user store.
    Uses SQLAlchemy with SQLite or PostgreSQL.
    """

    def __init__(self):
        self._session_factory = None
        self._initialized = False

    async def _get_session(self):
        """Get database session."""
        if not self._initialized:
            try:
                from ..database.connection import SessionLocal, init_db
                # Initialize database tables
                await init_db()
                self._session_factory = SessionLocal
                self._initialized = True
                logger.info("Database user store initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
        return self._session_factory()

    async def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        name: Optional[str] = None,
        provider: AuthProvider = AuthProvider.EMAIL,
        google_id: Optional[str] = None,
        is_verified: bool = False
    ) -> UserInDB:
        """Create a new user in database."""
        from ..database.models import User as DBUser, AuthProvider as DBAuthProvider
        from sqlalchemy import select

        async with await self._get_session() as session:
            # Check if email exists
            result = await session.execute(
                select(DBUser).where(DBUser.email == email.lower())
            )
            if result.scalar_one_or_none():
                raise ValueError("Email already registered")

            # Create user
            db_user = DBUser(
                email=email.lower(),
                name=name,
                password_hash=hash_password(password) if password else None,
                provider=DBAuthProvider.EMAIL if provider == AuthProvider.EMAIL else DBAuthProvider.GOOGLE,
                google_id=google_id,
                is_active=True,
                is_verified=is_verified
            )

            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

            return self._db_to_user(db_user)

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID from database."""
        from ..database.models import User as DBUser
        from sqlalchemy import select
        import uuid as uuid_module

        async with await self._get_session() as session:
            try:
                uid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
            except ValueError:
                return None

            result = await session.execute(
                select(DBUser).where(DBUser.id == uid)
            )
            db_user = result.scalar_one_or_none()
            return self._db_to_user(db_user) if db_user else None

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email from database."""
        from ..database.models import User as DBUser
        from sqlalchemy import select

        async with await self._get_session() as session:
            result = await session.execute(
                select(DBUser).where(DBUser.email == email.lower())
            )
            db_user = result.scalar_one_or_none()
            return self._db_to_user(db_user) if db_user else None

    async def get_by_google_id(self, google_id: str) -> Optional[UserInDB]:
        """Get user by Google ID from database."""
        from ..database.models import User as DBUser
        from sqlalchemy import select

        async with await self._get_session() as session:
            result = await session.execute(
                select(DBUser).where(DBUser.google_id == google_id)
            )
            db_user = result.scalar_one_or_none()
            return self._db_to_user(db_user) if db_user else None

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user's password in database."""
        from ..database.models import User as DBUser
        from sqlalchemy import select
        import uuid as uuid_module

        async with await self._get_session() as session:
            try:
                uid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
            except ValueError:
                return False

            result = await session.execute(
                select(DBUser).where(DBUser.id == uid)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return False

            db_user.password_hash = hash_password(new_password)
            db_user.updated_at = datetime.utcnow()
            await session.commit()
            return True

    async def verify_email(self, user_id: str) -> bool:
        """Mark user's email as verified in database."""
        from ..database.models import User as DBUser
        from sqlalchemy import select
        import uuid as uuid_module

        async with await self._get_session() as session:
            try:
                uid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
            except ValueError:
                return False

            result = await session.execute(
                select(DBUser).where(DBUser.id == uid)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return False

            db_user.is_verified = True
            db_user.updated_at = datetime.utcnow()
            await session.commit()
            return True

    async def link_google_account(self, user_id: str, google_id: str) -> bool:
        """Link Google account to existing user in database."""
        from ..database.models import User as DBUser
        from sqlalchemy import select
        import uuid as uuid_module

        async with await self._get_session() as session:
            try:
                uid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
            except ValueError:
                return False

            result = await session.execute(
                select(DBUser).where(DBUser.id == uid)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                return False

            db_user.google_id = google_id
            db_user.updated_at = datetime.utcnow()
            await session.commit()
            return True

    def _db_to_user(self, db_user) -> UserInDB:
        """Convert database user to UserInDB model."""
        from ..database.models import AuthProvider as DBAuthProvider

        return UserInDB(
            id=str(db_user.id),
            email=db_user.email,
            name=db_user.name,
            password_hash=db_user.password_hash,
            provider=AuthProvider.EMAIL if db_user.provider == DBAuthProvider.EMAIL else AuthProvider.GOOGLE,
            google_id=db_user.google_id,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )


# Type alias for user store
UserStore = InMemoryUserStore | DatabaseUserStore

# Singleton instance
_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """
    Get user store singleton.
    Uses database store by default, falls back to in-memory if not available.
    """
    global _user_store
    if _user_store is None:
        try:
            from ..database.config import get_db_settings
            settings = get_db_settings()
            logger.info(f"Using {settings.db_type.value} database for user storage")
            _user_store = DatabaseUserStore()
        except Exception as e:
            logger.warning(f"Database not available, using in-memory store: {e}")
            _user_store = InMemoryUserStore()
    return _user_store


def reset_user_store():
    """Reset user store (for testing)."""
    global _user_store
    _user_store = None


