"""
Database Configuration
Switches between SQLite (local development) and PostgreSQL (production).
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from enum import Enum


class DatabaseType(str, Enum):
    """Database type."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DatabaseSettings(BaseSettings):
    """Database configuration from environment variables."""

    # Environment - determines default database type
    ENVIRONMENT: str = "development"

    # Explicit database type override
    DATABASE_TYPE: str = ""

    # SQLite settings (local development)
    SQLITE_PATH: str = "./data/app.db"

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "docanalysis"
    POSTGRES_PASSWORD: str = "docanalysis_secret"
    POSTGRES_DB: str = "docanalysis"

    # Connection pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "documents"
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""

    @property
    def db_type(self) -> DatabaseType:
        """Determine database type based on environment."""
        # Explicit override
        if self.DATABASE_TYPE.lower() == "postgresql":
            return DatabaseType.POSTGRESQL
        elif self.DATABASE_TYPE.lower() == "sqlite":
            return DatabaseType.SQLITE

        # Based on environment
        if self.ENVIRONMENT.lower() in ("production", "prod", "staging"):
            return DatabaseType.POSTGRESQL

        # Default to SQLite for development
        return DatabaseType.SQLITE

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.db_type == DatabaseType.SQLITE

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod", "staging")

    @property
    def database_url(self) -> str:
        """Build database connection URL (async)."""
        if self.is_sqlite:
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        else:
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

    @property
    def database_url_sync(self) -> str:
        """Build sync database connection URL (for migrations)."""
        if self.is_sqlite:
            return f"sqlite:///{self.SQLITE_PATH}"
        else:
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get cached database settings."""
    return DatabaseSettings()

