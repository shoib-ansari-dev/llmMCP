"""
Database Repositories
Data access layer for all database operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets

from .models import (
    User, Document, DocumentChunk, Subscription, UsageLog, APIKey,
    PasswordResetToken, RefreshToken, AuthProvider, SubscriptionTier,
    SubscriptionStatus, DocumentStatus, DocumentType
)


# ============================================================================
# USER REPOSITORY
# ============================================================================

class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        password_hash: Optional[str] = None,
        name: Optional[str] = None,
        provider: AuthProvider = AuthProvider.EMAIL,
        google_id: Optional[str] = None,
        is_verified: bool = False
    ) -> User:
        """Create a new user."""
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            name=name,
            provider=provider,
            google_id=google_id,
            is_verified=is_verified
        )
        self.session.add(user)
        await self.session.flush()

        # Create default free subscription
        subscription = Subscription(
            user_id=user.id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            docs_per_month=5,
            pages_per_doc=10,
            api_calls_per_month=100
        )
        self.session.add(subscription)
        await self.session.flush()

        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        result = await self.session.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> bool:
        """Update user password."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def verify_email(self, user_id: uuid.UUID) -> bool:
        """Mark user email as verified."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update last login timestamp."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )

    async def deactivate(self, user_id: uuid.UUID) -> bool:
        """Deactivate user account."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0

    # Password Reset Tokens
    async def create_password_reset_token(
        self,
        user_id: uuid.UUID,
        expires_in_hours: int = 24
    ) -> str:
        """Create password reset token."""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
        )
        self.session.add(reset_token)
        await self.session.flush()

        return token

    async def verify_password_reset_token(self, token: str) -> Optional[uuid.UUID]:
        """Verify and consume password reset token. Returns user_id if valid."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await self.session.execute(
            select(PasswordResetToken)
            .where(
                and_(
                    PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.expires_at > datetime.utcnow(),
                    PasswordResetToken.used_at.is_(None)
                )
            )
        )
        reset_token = result.scalar_one_or_none()

        if reset_token:
            # Mark as used
            reset_token.used_at = datetime.utcnow()
            await self.session.flush()
            return reset_token.user_id

        return None

    # Refresh Tokens
    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_in_days: int = 30
    ) -> str:
        """Create refresh token."""
        token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        self.session.add(refresh_token)
        await self.session.flush()

        return token

    async def verify_refresh_token(self, token: str) -> Optional[User]:
        """Verify refresh token and return user."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await self.session.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.expires_at > datetime.utcnow(),
                    RefreshToken.revoked_at.is_(None)
                )
            )
        )
        refresh_token = result.scalar_one_or_none()

        if refresh_token:
            return refresh_token.user
        return None

    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def revoke_all_refresh_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke all refresh tokens for a user."""
        result = await self.session.execute(
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None)
                )
            )
            .values(revoked_at=datetime.utcnow())
        )
        return result.rowcount


# ============================================================================
# DOCUMENT REPOSITORY
# ============================================================================

class DocumentRepository:
    """Repository for document operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        owner_id: uuid.UUID,
        filename: str,
        original_filename: str,
        file_type: DocumentType,
        file_size: int,
        blob_name: str,
        mime_type: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Document:
        """Create a new document record."""
        document = Document(
            owner_id=owner_id,
            filename=filename,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            blob_name=blob_name,
            mime_type=mime_type,
            source_url=source_url,
            status=DocumentStatus.PENDING
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_by_id(
        self,
        document_id: uuid.UUID,
        include_chunks: bool = False
    ) -> Optional[Document]:
        """Get document by ID."""
        query = select(Document).where(Document.id == document_id)
        if include_chunks:
            query = query.options(selectinload(Document.chunks))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_documents(
        self,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[DocumentStatus] = None
    ) -> List[Document]:
        """Get documents for a user with pagination."""
        query = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status:
            query = query.where(Document.status == status)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_documents(
        self,
        owner_id: uuid.UUID,
        since: Optional[datetime] = None
    ) -> int:
        """Count documents for a user."""
        query = select(func.count(Document.id)).where(Document.owner_id == owner_id)
        if since:
            query = query.where(Document.created_at >= since)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update document processing status."""
        values = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if status == DocumentStatus.COMPLETED:
            values["processed_at"] = datetime.utcnow()
        if error_message:
            values["error_message"] = error_message

        result = await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(**values)
        )
        return result.rowcount > 0

    async def update_analysis(
        self,
        document_id: uuid.UUID,
        summary: Optional[str] = None,
        key_insights: Optional[List[str]] = None,
        page_count: Optional[int] = None,
        word_count: Optional[int] = None
    ) -> bool:
        """Update document analysis results."""
        values = {"updated_at": datetime.utcnow()}
        if summary:
            values["summary"] = summary
        if key_insights:
            values["key_insights"] = key_insights
        if page_count:
            values["page_count"] = page_count
        if word_count:
            values["word_count"] = word_count

        result = await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(**values)
        )
        return result.rowcount > 0

    async def delete(self, document_id: uuid.UUID) -> bool:
        """Delete a document."""
        result = await self.session.execute(
            delete(Document).where(Document.id == document_id)
        )
        return result.rowcount > 0

    # Document Chunks
    async def create_chunks(
        self,
        document_id: uuid.UUID,
        chunks: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Create document chunks in bulk."""
        chunk_objects = []
        for idx, chunk_data in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=chunk_data["content"],
                page_number=chunk_data.get("page_number"),
                section_title=chunk_data.get("section_title"),
                char_count=len(chunk_data["content"]),
                embedding_id=chunk_data.get("embedding_id")
            )
            self.session.add(chunk)
            chunk_objects.append(chunk)

        await self.session.flush()
        return chunk_objects

    async def get_chunks(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())


# ============================================================================
# SUBSCRIPTION REPOSITORY
# ============================================================================

class SubscriptionRepository:
    """Repository for subscription operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Subscription]:
        """Get subscription for a user."""
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, customer_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe customer ID."""
        result = await self.session.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    async def update_tier(
        self,
        user_id: uuid.UUID,
        tier: SubscriptionTier,
        stripe_subscription_id: Optional[str] = None,
        stripe_price_id: Optional[str] = None
    ) -> bool:
        """Update subscription tier."""
        # Get tier limits
        limits = self._get_tier_limits(tier)

        result = await self.session.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                tier=tier,
                stripe_subscription_id=stripe_subscription_id,
                stripe_price_id=stripe_price_id,
                **limits,
                updated_at=datetime.utcnow()
            )
        )
        return result.rowcount > 0

    async def increment_usage(
        self,
        user_id: uuid.UUID,
        docs_used: int = 0,
        api_calls: int = 0
    ) -> bool:
        """Increment usage counters."""
        subscription = await self.get_by_user_id(user_id)
        if not subscription:
            return False

        subscription.docs_used_this_month += docs_used
        subscription.api_calls_this_month += api_calls
        subscription.updated_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def reset_monthly_usage(self, user_id: uuid.UUID) -> bool:
        """Reset monthly usage counters."""
        result = await self.session.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                docs_used_this_month=0,
                api_calls_this_month=0,
                usage_reset_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        return result.rowcount > 0

    async def check_limits(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Check if user is within usage limits."""
        subscription = await self.get_by_user_id(user_id)
        if not subscription:
            return {"allowed": False, "reason": "No subscription found"}

        return {
            "allowed": True,
            "tier": subscription.tier.value,
            "docs_remaining": subscription.docs_per_month - subscription.docs_used_this_month,
            "api_calls_remaining": subscription.api_calls_per_month - subscription.api_calls_this_month,
            "can_upload": subscription.docs_used_this_month < subscription.docs_per_month,
            "can_call_api": subscription.api_calls_this_month < subscription.api_calls_per_month
        }

    def _get_tier_limits(self, tier: SubscriptionTier) -> Dict[str, int]:
        """Get limits for a subscription tier."""
        limits = {
            SubscriptionTier.FREE: {
                "docs_per_month": 5,
                "pages_per_doc": 10,
                "api_calls_per_month": 100
            },
            SubscriptionTier.PRO: {
                "docs_per_month": 100,
                "pages_per_doc": 50,
                "api_calls_per_month": 5000
            },
            SubscriptionTier.BUSINESS: {
                "docs_per_month": 1000,
                "pages_per_doc": 200,
                "api_calls_per_month": 50000
            },
            SubscriptionTier.ENTERPRISE: {
                "docs_per_month": 999999,  # Unlimited
                "pages_per_doc": 999999,
                "api_calls_per_month": 999999
            }
        }
        return limits.get(tier, limits[SubscriptionTier.FREE])


# ============================================================================
# USAGE REPOSITORY
# ============================================================================

class UsageRepository:
    """Repository for usage logging and analytics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        tokens_used: int = 0,
        pages_processed: int = 0,
        processing_time_ms: int = 0,
        cost_usd: float = 0.0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        api_key_id: Optional[uuid.UUID] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> UsageLog:
        """Log a usage event."""
        log = UsageLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tokens_used=tokens_used,
            pages_processed=pages_processed,
            processing_time_ms=processing_time_ms,
            cost_usd=cost_usd,
            ip_address=ip_address,
            user_agent=user_agent,
            api_key_id=api_key_id,
            success=success,
            error_message=error_message
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_user_usage(
        self,
        user_id: uuid.UUID,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        action: Optional[str] = None
    ) -> List[UsageLog]:
        """Get usage logs for a user."""
        query = select(UsageLog).where(UsageLog.user_id == user_id)

        if since:
            query = query.where(UsageLog.created_at >= since)
        if until:
            query = query.where(UsageLog.created_at <= until)
        if action:
            query = query.where(UsageLog.action == action)

        query = query.order_by(UsageLog.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_usage_summary(
        self,
        user_id: uuid.UUID,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage summary for a user."""
        query = select(
            func.count(UsageLog.id).label("total_requests"),
            func.sum(UsageLog.tokens_used).label("total_tokens"),
            func.sum(UsageLog.pages_processed).label("total_pages"),
            func.sum(UsageLog.cost_usd).label("total_cost")
        ).where(UsageLog.user_id == user_id)

        if since:
            query = query.where(UsageLog.created_at >= since)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "total_requests": row.total_requests or 0,
            "total_tokens": row.total_tokens or 0,
            "total_pages": row.total_pages or 0,
            "total_cost": float(row.total_cost or 0)
        }


# ============================================================================
# API KEY REPOSITORY
# ============================================================================

class APIKeyRepository:
    """Repository for API key operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        scopes: List[str] = None,
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns (APIKey, raw_key)."""
        # Generate key
        raw_key = f"dk_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:10]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes or ["read", "write"],
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
        )
        self.session.add(api_key)
        await self.session.flush()

        return api_key, raw_key

    async def verify(self, raw_key: str) -> Optional[APIKey]:
        """Verify an API key and return it if valid."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        result = await self.session.execute(
            select(APIKey)
            .options(selectinload(APIKey.user))
            .where(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True,
                    APIKey.revoked_at.is_(None),
                    or_(
                        APIKey.expires_at.is_(None),
                        APIKey.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key:
            # Update last used
            api_key.last_used_at = datetime.utcnow()
            await self.session.flush()

        return api_key

    async def get_user_keys(self, user_id: uuid.UUID) -> List[APIKey]:
        """Get all API keys for a user."""
        result = await self.session.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke(self, key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Revoke an API key."""
        result = await self.session.execute(
            update(APIKey)
            .where(
                and_(
                    APIKey.id == key_id,
                    APIKey.user_id == user_id
                )
            )
            .values(revoked_at=datetime.utcnow(), is_active=False)
        )
        return result.rowcount > 0

