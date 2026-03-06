"""
Database Models
SQLAlchemy ORM models compatible with SQLite and PostgreSQL.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, Index, BigInteger, UniqueConstraint,
    TypeDecorator
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .connection import Base
from .config import get_db_settings

# Check if using PostgreSQL
_settings = get_db_settings()
_use_postgres = not _settings.is_sqlite

# Import PostgreSQL types only if using PostgreSQL
if _use_postgres:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY

    # Use PostgreSQL UUID
    def get_uuid_type():
        return PG_get_uuid_type()
else:
    # Use String for SQLite
    class UUIDString(TypeDecorator):
        """Store UUID as string for SQLite compatibility."""
        impl = String(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is not None:
                return str(value)
            return value

        def process_result_value(self, value, dialect):
            if value is not None:
                return uuid.UUID(value) if isinstance(value, str) else value
            return value

    def get_uuid_type():
        return UUIDString()

# Create a consistent UUID column type
UUIDColumn = get_uuid_type()


# ============================================================================
# ENUMS
# ============================================================================

class AuthProvider(str, enum.Enum):
    """User authentication provider."""
    EMAIL = "email"
    GOOGLE = "google"


class SubscriptionTier(str, enum.Enum):
    """Subscription pricing tiers."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    """Supported document types."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    WORD = "word"
    WEB = "web"
    TEXT = "text"


# ============================================================================
# USER & AUTHENTICATION
# ============================================================================

class User(Base):
    """
    User account model.
    Stores user profile and authentication details.
    """
    __tablename__ = "users"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)  # Null for OAuth users

    # Auth provider
    provider = Column(Enum(AuthProvider), default=AuthProvider.EMAIL, nullable=False)
    google_id = Column(String(255), unique=True, nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Profile
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class PasswordResetToken(Base):
    """
    Password reset tokens.
    Short-lived tokens sent via email for password reset.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_type(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Index for cleanup of expired tokens
    __table_args__ = (
        Index("ix_password_reset_tokens_expires", "expires_at"),
    )


class RefreshToken(Base):
    """
    Refresh tokens for JWT authentication.
    Allows token refresh without re-authentication.
    """
    __tablename__ = "refresh_tokens"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_type(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(String(500), nullable=True)  # User agent, device type
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_expires", "expires_at"),
    )


# ============================================================================
# SUBSCRIPTION & BILLING
# ============================================================================

class Subscription(Base):
    """
    User subscription model.
    Tracks subscription tier, status, and Stripe integration.
    """
    __tablename__ = "subscriptions"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_type(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Plan details
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)

    # Stripe integration
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Billing period
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)

    # Usage limits (based on tier)
    docs_per_month = Column(Integer, default=5)  # Free tier default
    pages_per_doc = Column(Integer, default=10)  # Free tier default
    api_calls_per_month = Column(Integer, default=100)

    # Current usage
    docs_used_this_month = Column(Integer, default=0)
    api_calls_this_month = Column(Integer, default=0)
    usage_reset_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, tier={self.tier})>"


# ============================================================================
# DOCUMENTS
# ============================================================================

class Document(Base):
    """
    Uploaded document model.
    Stores metadata; actual file in Azure Blob Storage.
    """
    __tablename__ = "documents"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    owner_id = Column(get_uuid_type(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(Enum(DocumentType), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Bytes
    mime_type = Column(String(100), nullable=True)

    # Azure Blob Storage
    blob_name = Column(String(500), nullable=False, unique=True)  # Full path in container
    blob_url = Column(String(1000), nullable=True)  # SAS URL (short-lived)

    # Processing
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Analysis results
    summary = Column(Text, nullable=True)
    key_insights = Column(JSON, nullable=True)  # List of insights
    extracted_entities = Column(JSON, nullable=True)  # Named entities

    # Source URL (for web documents)
    source_url = Column(String(2000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_documents_owner_created", "owner_id", "created_at"),
        Index("ix_documents_status", "status"),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    """
    Document chunks for RAG.
    Each document is split into chunks for vector search.
    """
    __tablename__ = "document_chunks"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    document_id = Column(get_uuid_type(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Chunk content
    chunk_index = Column(Integer, nullable=False)  # Position in document
    content = Column(Text, nullable=False)

    # Metadata
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(500), nullable=True)
    char_count = Column(Integer, nullable=False)

    # Vector embedding reference (stored in ChromaDB)
    embedding_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("ix_document_chunks_doc_index", "document_id", "chunk_index"),
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )

    def __repr__(self):
        return f"<DocumentChunk(doc={self.document_id}, index={self.chunk_index})>"


# ============================================================================
# API & USAGE TRACKING
# ============================================================================

class APIKey(Base):
    """
    API keys for programmatic access.
    Users can generate API keys for integration.
    """
    __tablename__ = "api_keys"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_type(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Key details
    name = Column(String(100), nullable=False)  # User-defined name
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    key_hash = Column(String(255), nullable=False, unique=True)

    # Permissions (JSON array for SQLite compatibility)
    scopes = Column(JSON, default=["read", "write"])  # read, write, admin

    # Rate limits
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    # Timestamps
    expires_at = Column(DateTime, nullable=True)  # Null = never expires
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, prefix={self.key_prefix})>"


class UsageLog(Base):
    """
    Usage tracking for billing and analytics.
    Records each significant action for metering.
    """
    __tablename__ = "usage_logs"

    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_type(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # upload, analyze, query, etc.
    resource_type = Column(String(50), nullable=True)  # document, api, etc.
    resource_id = Column(get_uuid_type(), nullable=True)

    # Usage metrics
    tokens_used = Column(Integer, default=0)  # LLM tokens
    pages_processed = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    api_key_id = Column(get_uuid_type(), nullable=True)

    # Cost tracking
    cost_usd = Column(Float, default=0.0)  # Estimated cost

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")

    # Indexes for analytics queries
    __table_args__ = (
        Index("ix_usage_logs_user_action", "user_id", "action"),
        Index("ix_usage_logs_created", "created_at"),
    )

    def __repr__(self):
        return f"<UsageLog(user={self.user_id}, action={self.action})>"

