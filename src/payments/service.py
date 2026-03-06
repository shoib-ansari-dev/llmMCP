"""
Payment Service
High-level service that uses payment strategy and integrates with database.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .strategies import PaymentStrategy, get_payment_strategy
from .models import (
    SubscriptionTier, SubscriptionStatus,
    Subscription, Invoice, PaymentMethod, CheckoutSession, PortalSession,
    WebhookEvent, SUBSCRIPTION_PLANS, get_plan_by_tier
)
from .config import get_payment_settings

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Payment service that orchestrates payment operations.
    Uses strategy pattern for provider abstraction.
    """

    def __init__(
        self,
        db: AsyncSession,
        strategy: Optional[PaymentStrategy] = None
    ):
        self.db = db
        self.strategy = strategy or get_payment_strategy()
        self.settings = get_payment_settings()

    # ========================================================================
    # CUSTOMER MANAGEMENT
    # ========================================================================

    async def ensure_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None
    ) -> str:
        """
        Ensure user has a payment customer ID.
        Creates one if it doesn't exist.
        """
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id

        # Create new customer
        customer_id = await self.strategy.create_customer(
            user_id=user_id,
            email=email,
            name=name
        )

        # Update subscription with customer ID
        if subscription:
            subscription.stripe_customer_id = customer_id
            await self.db.flush()

        return customer_id

    # ========================================================================
    # CHECKOUT & BILLING PORTAL
    # ========================================================================

    async def create_checkout(
        self,
        user_id: str,
        email: str,
        tier: SubscriptionTier,
        name: Optional[str] = None,
        trial: bool = True
    ) -> CheckoutSession:
        """
        Create a checkout session for subscription.
        """
        # Ensure customer exists
        customer_id = await self.ensure_customer(user_id, email, name)

        # Determine trial days
        trial_days = self.settings.TRIAL_DAYS if trial else None

        # Create checkout session
        session = await self.strategy.create_checkout_session(
            customer_id=customer_id,
            tier=tier,
            success_url=self.settings.success_url,
            cancel_url=self.settings.cancel_url,
            trial_days=trial_days,
            metadata={"user_id": user_id}
        )

        logger.info(f"Created checkout for user {user_id}, tier: {tier.value}")
        return session

    async def create_billing_portal(
        self,
        user_id: str
    ) -> PortalSession:
        """
        Create a billing portal session for subscription management.
        """
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not subscription or not subscription.stripe_customer_id:
            raise ValueError("User has no payment account")

        session = await self.strategy.create_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=self.settings.APP_URL
        )

        return session

    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================

    async def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's current subscription with plan details.
        """
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        db_subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not db_subscription:
            return None

        # Get plan details
        plan = get_plan_by_tier(SubscriptionTier(db_subscription.tier.value))

        result = {
            "tier": db_subscription.tier.value,
            "status": db_subscription.status.value,
            "plan": plan.model_dump() if plan else None,
            "usage": {
                "docs_used": db_subscription.docs_used_this_month,
                "docs_limit": db_subscription.docs_per_month,
                "api_calls_used": db_subscription.api_calls_this_month,
                "api_calls_limit": db_subscription.api_calls_per_month
            },
            "current_period_end": db_subscription.current_period_end,
            "cancel_at_period_end": db_subscription.cancel_at_period_end
        }

        # If there's a Stripe subscription, get more details
        if db_subscription.stripe_subscription_id:
            stripe_sub = await self.strategy.get_subscription(
                db_subscription.stripe_subscription_id
            )
            if stripe_sub:
                result["payment_method"] = stripe_sub.payment_method
                result["trial_end"] = stripe_sub.trial_end

        return result

    async def upgrade_subscription(
        self,
        user_id: str,
        new_tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """
        Upgrade user's subscription to a new tier.
        """
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionTier as DBTier

        sub_repo = SubscriptionRepository(self.db)
        db_subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not db_subscription:
            raise ValueError("User has no subscription")

        current_tier = SubscriptionTier(db_subscription.tier.value)

        # Check if it's actually an upgrade
        tier_order = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PRO: 1,
            SubscriptionTier.BUSINESS: 2,
            SubscriptionTier.ENTERPRISE: 3
        }

        if tier_order[new_tier] <= tier_order[current_tier]:
            raise ValueError("Can only upgrade to a higher tier. Use billing portal for downgrades.")

        # If upgrading from free, need to create checkout
        if current_tier == SubscriptionTier.FREE:
            raise ValueError("Use checkout flow to upgrade from free tier")

        # Update Stripe subscription
        if db_subscription.stripe_subscription_id:
            await self.strategy.update_subscription(
                db_subscription.stripe_subscription_id,
                new_tier
            )

        # Update database
        await sub_repo.update_tier(
            uuid.UUID(user_id),
            DBTier(new_tier.value)
        )

        logger.info(f"Upgraded user {user_id} from {current_tier.value} to {new_tier.value}")
        return await self.get_subscription(user_id)

    async def cancel_subscription(
        self,
        user_id: str,
        cancel_at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel user's subscription.
        """
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        db_subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not db_subscription or not db_subscription.stripe_subscription_id:
            raise ValueError("No active subscription to cancel")

        # Cancel in Stripe
        await self.strategy.cancel_subscription(
            db_subscription.stripe_subscription_id,
            cancel_at_period_end
        )

        # Update database
        db_subscription.cancel_at_period_end = cancel_at_period_end
        await self.db.flush()

        logger.info(f"Cancelled subscription for user {user_id}")
        return await self.get_subscription(user_id)

    async def reactivate_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Reactivate a cancelled subscription.
        """
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        db_subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not db_subscription or not db_subscription.stripe_subscription_id:
            raise ValueError("No subscription to reactivate")

        # Reactivate in Stripe
        await self.strategy.reactivate_subscription(
            db_subscription.stripe_subscription_id
        )

        # Update database
        db_subscription.cancel_at_period_end = False
        await self.db.flush()

        logger.info(f"Reactivated subscription for user {user_id}")
        return await self.get_subscription(user_id)

    # ========================================================================
    # INVOICES & PAYMENT METHODS
    # ========================================================================

    async def get_invoices(self, user_id: str, limit: int = 10) -> List[Invoice]:
        """Get user's invoices."""
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not subscription or not subscription.stripe_customer_id:
            return []

        return await self.strategy.get_invoices(
            subscription.stripe_customer_id,
            limit
        )

    async def get_payment_methods(self, user_id: str) -> List[PaymentMethod]:
        """Get user's payment methods."""
        from src.database import SubscriptionRepository

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_user_id(uuid.UUID(user_id))

        if not subscription or not subscription.stripe_customer_id:
            return []

        return await self.strategy.get_payment_methods(
            subscription.stripe_customer_id
        )

    # ========================================================================
    # WEBHOOK HANDLING
    # ========================================================================

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle webhook from payment provider.
        Updates database based on event type.
        """
        event = await self.strategy.handle_webhook(payload, signature)

        logger.info(f"Processing webhook event: {event.type}")

        # Handle different event types (Stripe + Razorpay)
        handlers = {
            # Stripe events
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_payment_failed,
            # Razorpay events
            "subscription.activated": self._handle_razorpay_subscription_activated,
            "subscription.charged": self._handle_razorpay_subscription_charged,
            "subscription.cancelled": self._handle_razorpay_subscription_cancelled,
            "subscription.halted": self._handle_razorpay_subscription_halted,
            "payment.captured": self._handle_razorpay_payment_captured,
            "payment.failed": self._handle_razorpay_payment_failed,
        }

        handler = handlers.get(event.type)
        if handler:
            await handler(event)

        return {"status": "processed", "event_type": event.type}

    async def _handle_checkout_completed(self, event: WebhookEvent):
        """Handle successful checkout."""
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionTier as DBTier, SubscriptionStatus as DBStatus

        data = event.data
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        metadata = data.get("metadata", {})

        user_id = metadata.get("user_id")
        tier = metadata.get("tier", "pro")

        if user_id:
            sub_repo = SubscriptionRepository(self.db)
            await sub_repo.update_tier(
                uuid.UUID(user_id),
                DBTier(tier),
                stripe_subscription_id=subscription_id
            )
            logger.info(f"Checkout completed for user {user_id}")

    async def _handle_subscription_created(self, event: WebhookEvent):
        """Handle subscription creation."""
        logger.info(f"Subscription created: {event.data.get('id')}")

    async def _handle_subscription_updated(self, event: WebhookEvent):
        """Handle subscription update."""
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionTier as DBTier, SubscriptionStatus as DBStatus

        data = event.data
        subscription_id = data.get("id")
        status = data.get("status")
        metadata = data.get("metadata", {})
        tier = metadata.get("tier")

        # Find subscription by Stripe ID
        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_stripe_customer_id(data.get("customer"))

        if subscription:
            # Update status
            status_map = {
                "active": DBStatus.ACTIVE,
                "canceled": DBStatus.CANCELLED,
                "past_due": DBStatus.PAST_DUE,
                "trialing": DBStatus.TRIALING
            }
            if status in status_map:
                subscription.status = status_map[status]

            # Update tier if changed
            if tier:
                subscription.tier = DBTier(tier)

            # Update period
            if data.get("current_period_end"):
                subscription.current_period_end = datetime.fromtimestamp(
                    data["current_period_end"]
                )

            subscription.cancel_at_period_end = data.get("cancel_at_period_end", False)
            await self.db.flush()

            logger.info(f"Updated subscription: {subscription_id}")

    async def _handle_subscription_deleted(self, event: WebhookEvent):
        """Handle subscription deletion."""
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionTier as DBTier, SubscriptionStatus as DBStatus

        data = event.data

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_stripe_customer_id(data.get("customer"))

        if subscription:
            # Downgrade to free
            subscription.tier = DBTier.FREE
            subscription.status = DBStatus.ACTIVE
            subscription.stripe_subscription_id = None

            # Reset to free limits
            subscription.docs_per_month = 5
            subscription.pages_per_doc = 10
            subscription.api_calls_per_month = 100

            await self.db.flush()
            logger.info(f"Subscription deleted, downgraded user to free")

    async def _handle_invoice_paid(self, event: WebhookEvent):
        """Handle successful payment."""
        from src.database import SubscriptionRepository, UsageRepository

        data = event.data
        customer_id = data.get("customer")

        # Reset monthly usage on successful payment
        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_stripe_customer_id(customer_id)

        if subscription:
            await sub_repo.reset_monthly_usage(subscription.user_id)
            logger.info(f"Invoice paid, reset usage for customer: {customer_id}")

    async def _handle_payment_failed(self, event: WebhookEvent):
        """Handle failed payment."""
        data = event.data
        customer_id = data.get("customer")
        logger.warning(f"Payment failed for customer: {customer_id}")
        # TODO: Send notification email

    # ========================================================================
    # RAZORPAY WEBHOOK HANDLERS
    # ========================================================================

    async def _handle_razorpay_subscription_activated(self, event: WebhookEvent):
        """Handle Razorpay subscription activation."""
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionTier as DBTier, SubscriptionStatus as DBStatus

        data = event.data
        subscription_data = data.get("subscription", {}).get("entity", {})

        notes = subscription_data.get("notes", {})
        user_id = notes.get("user_id")
        tier = notes.get("tier", "pro")

        if user_id:
            sub_repo = SubscriptionRepository(self.db)
            await sub_repo.update_tier(
                uuid.UUID(user_id),
                DBTier(tier),
                stripe_subscription_id=subscription_data.get("id")
            )
            logger.info(f"Razorpay subscription activated for user {user_id}")

    async def _handle_razorpay_subscription_charged(self, event: WebhookEvent):
        """Handle Razorpay subscription charge (payment success)."""
        from src.database import SubscriptionRepository

        data = event.data
        subscription_data = data.get("subscription", {}).get("entity", {})
        customer_id = subscription_data.get("customer_id")

        # Reset monthly usage on successful payment
        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_stripe_customer_id(customer_id)

        if subscription:
            await sub_repo.reset_monthly_usage(subscription.user_id)
            logger.info(f"Razorpay subscription charged, reset usage for customer: {customer_id}")

    async def _handle_razorpay_subscription_cancelled(self, event: WebhookEvent):
        """Handle Razorpay subscription cancellation."""
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionTier as DBTier, SubscriptionStatus as DBStatus

        data = event.data
        subscription_data = data.get("subscription", {}).get("entity", {})
        customer_id = subscription_data.get("customer_id")

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_stripe_customer_id(customer_id)

        if subscription:
            # Downgrade to free
            subscription.tier = DBTier.FREE
            subscription.status = DBStatus.ACTIVE
            subscription.stripe_subscription_id = None
            subscription.docs_per_month = 5
            subscription.pages_per_doc = 10
            subscription.api_calls_per_month = 100
            await self.db.flush()
            logger.info(f"Razorpay subscription cancelled, downgraded to free")

    async def _handle_razorpay_subscription_halted(self, event: WebhookEvent):
        """Handle Razorpay subscription halted (payment issues)."""
        from src.database import SubscriptionRepository
        from src.database.models import SubscriptionStatus as DBStatus

        data = event.data
        subscription_data = data.get("subscription", {}).get("entity", {})
        customer_id = subscription_data.get("customer_id")

        sub_repo = SubscriptionRepository(self.db)
        subscription = await sub_repo.get_by_stripe_customer_id(customer_id)

        if subscription:
            subscription.status = DBStatus.PAST_DUE
            await self.db.flush()
            logger.warning(f"Razorpay subscription halted for customer: {customer_id}")

    async def _handle_razorpay_payment_captured(self, event: WebhookEvent):
        """Handle Razorpay payment capture."""
        data = event.data
        payment_data = data.get("payment", {}).get("entity", {})
        logger.info(f"Razorpay payment captured: {payment_data.get('id')}")

    async def _handle_razorpay_payment_failed(self, event: WebhookEvent):
        """Handle Razorpay payment failure."""
        data = event.data
        payment_data = data.get("payment", {}).get("entity", {})
        logger.warning(f"Razorpay payment failed: {payment_data.get('id')}")
        # TODO: Send notification email


# ============================================================================
# PLANS HELPERS
# ============================================================================

def get_all_plans() -> List[Dict[str, Any]]:
    """Get all subscription plans."""
    return [plan.model_dump() for plan in SUBSCRIPTION_PLANS]

