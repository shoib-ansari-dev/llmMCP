"""
Database Connection
SQLAlchemy async engine and session management.
Supports SQLite (local) and PostgreSQL (production).
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from typing import AsyncGenerator
import logging

from .config import get_db_settings

logger = logging.getLogger(__name__)

settings = get_db_settings()

# Log which database we're using
logger.info(f"Database type: {settings.db_type.value}")
logger.info(f"Database URL: {settings.database_url.split('@')[0]}@***" if '@' in settings.database_url else f"Database: {settings.database_url}")

# Create async engine with appropriate settings
if settings.is_sqlite:
    # SQLite configuration
    # Ensure data directory exists
    sqlite_dir = os.path.dirname(settings.SQLITE_PATH)
    if sqlite_dir and not os.path.exists(sqlite_dir):
        os.makedirs(sqlite_dir, exist_ok=True)

    engine = create_async_engine(
        settings.database_url,
        echo=False,  # Set True for SQL debugging
        connect_args={"check_same_thread": False}  # SQLite specific
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Check connection health
        echo=False,  # Set True for SQL debugging
    )

# Session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    async with engine.begin() as conn:
        # Import models to register them with Base
        from . import models  # noqa
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    Close database connections.
    Call this on application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")

