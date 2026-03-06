"""
Payment Strategy Pattern
Abstract base and concrete implementations for payment providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from .config import get_payment_settings, PaymentProvider
from .models import (
    SubscriptionTier, SubscriptionStatus, PaymentStatus,
    Subscription, PaymentIntent, Invoice, PaymentMethod,
    CheckoutSession, PortalSession, WebhookEvent,
    get_plan_by_tier
)

logger = logging.getLogger(__name__)


# ============================================================================
# ABSTRACT STRATEGY
# ============================================================================

class PaymentStrategy(ABC):
    """
    Abstract payment strategy.
    Defines the interface for all payment providers.
    """

    @abstractmethod
    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a customer in the payment provider.
        Returns: customer_id
        """
        pass

    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer details."""
        pass

    @abstractmethod
    async def create_checkout_session(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CheckoutSession:
        """Create a checkout session for subscription."""
        pass

    @abstractmethod
    async def create_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> PortalSession:
        """Create a billing portal session."""
        pass

    @abstractmethod
    async def get_subscription(
        self,
        subscription_id: str
    ) -> Optional[Subscription]:
        """Get subscription details."""
        pass

    @abstractmethod
    async def update_subscription(
        self,
        subscription_id: str,
        tier: SubscriptionTier
    ) -> Subscription:
        """Update subscription to a new tier."""
        pass

    @abstractmethod
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Subscription:
        """Cancel a subscription."""
        pass

    @abstractmethod
    async def reactivate_subscription(
        self,
        subscription_id: str
    ) -> Subscription:
        """Reactivate a cancelled subscription."""
        pass

    @abstractmethod
    async def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Invoice]:
        """Get customer invoices."""
        pass

    @abstractmethod
    async def get_payment_methods(
        self,
        customer_id: str
    ) -> List[PaymentMethod]:
        """Get customer payment methods."""
        pass

    @abstractmethod
    async def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """Set default payment method."""
        pass

    @abstractmethod
    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        """Verify and parse webhook event."""
        pass


# ============================================================================
# STRIPE STRATEGY
# ============================================================================

class StripePaymentStrategy(PaymentStrategy):
    """
    Stripe payment strategy implementation.
    """

    def __init__(self):
        self.settings = get_payment_settings()
        self._stripe = None

    @property
    def stripe(self):
        """Lazy load Stripe library."""
        if self._stripe is None:
            import stripe
            stripe.api_key = self.settings.STRIPE_SECRET_KEY
            self._stripe = stripe
        return self._stripe

    def _get_price_id(self, tier: SubscriptionTier) -> str:
        """Get Stripe price ID for tier."""
        price_map = {
            SubscriptionTier.FREE: self.settings.STRIPE_PRICE_FREE,
            SubscriptionTier.PRO: self.settings.STRIPE_PRICE_PRO,
            SubscriptionTier.BUSINESS: self.settings.STRIPE_PRICE_BUSINESS,
            SubscriptionTier.ENTERPRISE: self.settings.STRIPE_PRICE_ENTERPRISE
        }
        return price_map.get(tier, "")

    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a Stripe customer."""
        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": user_id,
                    **(metadata or {})
                }
            )
            logger.info(f"Created Stripe customer: {customer.id} for user: {user_id}")
            return customer.id
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get Stripe customer details."""
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": datetime.fromtimestamp(customer.created),
                "metadata": dict(customer.metadata)
            }
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting customer: {e}")
            return None

    async def create_checkout_session(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CheckoutSession:
        """Create a Stripe Checkout session."""
        try:
            price_id = self._get_price_id(tier)

            session_params = {
                "customer": customer_id,
                "mode": "subscription",
                "line_items": [{
                    "price": price_id,
                    "quantity": 1
                }],
                "success_url": f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": cancel_url,
                "metadata": {
                    "tier": tier.value,
                    **(metadata or {})
                },
                "subscription_data": {
                    "metadata": {
                        "tier": tier.value
                    }
                }
            }

            # Add trial if specified
            if trial_days and trial_days > 0:
                session_params["subscription_data"]["trial_period_days"] = trial_days

            session = self.stripe.checkout.Session.create(**session_params)

            logger.info(f"Created checkout session: {session.id}")
            return CheckoutSession(
                id=session.id,
                url=session.url,
                expires_at=datetime.fromtimestamp(session.expires_at)
            )
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise

    async def create_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> PortalSession:
        """Create a Stripe Billing Portal session."""
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            logger.info(f"Created portal session: {session.id}")
            return PortalSession(
                id=session.id,
                url=session.url
            )
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise

    async def get_subscription(
        self,
        subscription_id: str
    ) -> Optional[Subscription]:
        """Get Stripe subscription details."""
        try:
            sub = self.stripe.Subscription.retrieve(
                subscription_id,
                expand=["default_payment_method"]
            )

            payment_method = None
            if sub.default_payment_method:
                pm = sub.default_payment_method
                if hasattr(pm, 'card') and pm.card:
                    payment_method = PaymentMethod(
                        id=pm.id,
                        type="card",
                        brand=pm.card.brand,
                        last4=pm.card.last4,
                        exp_month=pm.card.exp_month,
                        exp_year=pm.card.exp_year,
                        is_default=True
                    )

            tier_value = sub.metadata.get("tier", "free")
            tier = SubscriptionTier(tier_value)

            status_map = {
                "active": SubscriptionStatus.ACTIVE,
                "canceled": SubscriptionStatus.CANCELLED,
                "past_due": SubscriptionStatus.PAST_DUE,
                "trialing": SubscriptionStatus.TRIALING,
                "incomplete": SubscriptionStatus.INCOMPLETE,
                "unpaid": SubscriptionStatus.UNPAID
            }

            return Subscription(
                id=sub.id,
                user_id=sub.metadata.get("user_id", ""),
                tier=tier,
                status=status_map.get(sub.status, SubscriptionStatus.ACTIVE),
                current_period_start=datetime.fromtimestamp(sub.current_period_start),
                current_period_end=datetime.fromtimestamp(sub.current_period_end),
                cancel_at_period_end=sub.cancel_at_period_end,
                cancelled_at=datetime.fromtimestamp(sub.canceled_at) if sub.canceled_at else None,
                trial_start=datetime.fromtimestamp(sub.trial_start) if sub.trial_start else None,
                trial_end=datetime.fromtimestamp(sub.trial_end) if sub.trial_end else None,
                stripe_subscription_id=sub.id,
                stripe_customer_id=sub.customer,
                payment_method=payment_method
            )
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscription: {e}")
            return None

    async def update_subscription(
        self,
        subscription_id: str,
        tier: SubscriptionTier
    ) -> Subscription:
        """Update Stripe subscription to new tier."""
        try:
            # Get current subscription
            sub = self.stripe.Subscription.retrieve(subscription_id)

            # Get new price ID
            new_price_id = self._get_price_id(tier)

            # Update subscription
            updated_sub = self.stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": sub["items"]["data"][0].id,
                    "price": new_price_id
                }],
                metadata={"tier": tier.value},
                proration_behavior="create_prorations"
            )

            logger.info(f"Updated subscription {subscription_id} to tier: {tier.value}")
            return await self.get_subscription(subscription_id)
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Subscription:
        """Cancel Stripe subscription."""
        try:
            if cancel_at_period_end:
                # Cancel at end of billing period
                self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Cancel immediately
                self.stripe.Subscription.cancel(subscription_id)

            logger.info(f"Cancelled subscription: {subscription_id}")
            return await self.get_subscription(subscription_id)
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            raise

    async def reactivate_subscription(
        self,
        subscription_id: str
    ) -> Subscription:
        """Reactivate a cancelled Stripe subscription."""
        try:
            self.stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"Reactivated subscription: {subscription_id}")
            return await self.get_subscription(subscription_id)
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error reactivating subscription: {e}")
            raise

    async def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Invoice]:
        """Get customer invoices from Stripe."""
        try:
            invoices = self.stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )

            return [
                Invoice(
                    id=inv.id,
                    number=inv.number,
                    amount_due=inv.amount_due,
                    amount_paid=inv.amount_paid,
                    currency=inv.currency,
                    status=inv.status,
                    paid=inv.paid,
                    created_at=datetime.fromtimestamp(inv.created),
                    due_date=datetime.fromtimestamp(inv.due_date) if inv.due_date else None,
                    pdf_url=inv.invoice_pdf,
                    hosted_invoice_url=inv.hosted_invoice_url
                )
                for inv in invoices.data
            ]
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting invoices: {e}")
            return []

    async def get_payment_methods(
        self,
        customer_id: str
    ) -> List[PaymentMethod]:
        """Get customer payment methods from Stripe."""
        try:
            # Get customer to find default payment method
            customer = self.stripe.Customer.retrieve(customer_id)
            default_pm_id = customer.invoice_settings.default_payment_method

            # Get all payment methods
            payment_methods = self.stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )

            return [
                PaymentMethod(
                    id=pm.id,
                    type="card",
                    brand=pm.card.brand,
                    last4=pm.card.last4,
                    exp_month=pm.card.exp_month,
                    exp_year=pm.card.exp_year,
                    is_default=(pm.id == default_pm_id)
                )
                for pm in payment_methods.data
            ]
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting payment methods: {e}")
            return []

    async def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """Set default payment method in Stripe."""
        try:
            self.stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            logger.info(f"Set default payment method for customer: {customer_id}")
            return True
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error setting default payment method: {e}")
            return False

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        """Verify and parse Stripe webhook event."""
        try:
            event = self.stripe.Webhook.construct_event(
                payload,
                signature,
                self.settings.STRIPE_WEBHOOK_SECRET
            )

            return WebhookEvent(
                id=event.id,
                type=event.type,
                data=event.data.object,
                created_at=datetime.fromtimestamp(event.created)
            )
        except self.stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise ValueError("Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise


# ============================================================================
# RAZORPAY STRATEGY
# ============================================================================

class RazorpayPaymentStrategy(PaymentStrategy):
    """
    Razorpay payment strategy implementation.
    Popular payment gateway in India.
    """

    def __init__(self):
        self.settings = get_payment_settings()
        self._client = None

    @property
    def client(self):
        """Lazy load Razorpay client."""
        if self._client is None:
            import razorpay
            self._client = razorpay.Client(
                auth=(self.settings.RAZORPAY_KEY_ID, self.settings.RAZORPAY_KEY_SECRET)
            )
        return self._client

    def _get_plan_id(self, tier: SubscriptionTier) -> str:
        """Get Razorpay plan ID for tier."""
        plan_map = {
            SubscriptionTier.FREE: self.settings.RAZORPAY_PLAN_FREE,
            SubscriptionTier.PRO: self.settings.RAZORPAY_PLAN_PRO,
            SubscriptionTier.BUSINESS: self.settings.RAZORPAY_PLAN_BUSINESS,
            SubscriptionTier.ENTERPRISE: self.settings.RAZORPAY_PLAN_ENTERPRISE
        }
        return plan_map.get(tier, "")

    def _get_amount_in_paise(self, tier: SubscriptionTier) -> int:
        """Get amount in paise (smallest currency unit) for tier."""
        # Prices in INR
        price_map = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.PRO: 1499 * 100,  # ₹1,499
            SubscriptionTier.BUSINESS: 3999 * 100,  # ₹3,999
            SubscriptionTier.ENTERPRISE: 14999 * 100  # ₹14,999
        }
        return price_map.get(tier, 0)

    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a Razorpay customer."""
        try:
            customer = self.client.customer.create({
                "name": name or email.split("@")[0],
                "email": email,
                "notes": {
                    "user_id": user_id,
                    **(metadata or {})
                }
            })
            logger.info(f"Created Razorpay customer: {customer['id']} for user: {user_id}")
            return customer["id"]
        except Exception as e:
            logger.error(f"Razorpay error creating customer: {e}")
            raise

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get Razorpay customer details."""
        try:
            customer = self.client.customer.fetch(customer_id)
            return {
                "id": customer["id"],
                "email": customer.get("email"),
                "name": customer.get("name"),
                "contact": customer.get("contact"),
                "created": datetime.fromtimestamp(customer.get("created_at", 0)),
                "metadata": customer.get("notes", {})
            }
        except Exception as e:
            logger.error(f"Razorpay error getting customer: {e}")
            return None

    async def create_checkout_session(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CheckoutSession:
        """Create a Razorpay subscription checkout."""
        try:
            plan_id = self._get_plan_id(tier)

            # Create subscription
            subscription_data = {
                "plan_id": plan_id,
                "customer_id": customer_id,
                "total_count": 12,  # 12 billing cycles
                "notes": {
                    "tier": tier.value,
                    **(metadata or {})
                }
            }

            # Add trial if specified
            if trial_days and trial_days > 0:
                subscription_data["start_at"] = int(
                    (datetime.utcnow() + timedelta(days=trial_days)).timestamp()
                )

            subscription = self.client.subscription.create(subscription_data)

            # Generate checkout URL
            # Razorpay uses a different flow - we return subscription details
            # Frontend uses Razorpay.js to handle the payment
            checkout_url = f"{self.settings.APP_URL}/checkout/razorpay?subscription_id={subscription['id']}"

            logger.info(f"Created Razorpay subscription: {subscription['id']}")
            return CheckoutSession(
                id=subscription["id"],
                url=checkout_url,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
        except Exception as e:
            logger.error(f"Razorpay error creating subscription: {e}")
            raise

    async def create_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> PortalSession:
        """
        Razorpay doesn't have a hosted billing portal like Stripe.
        Return a custom portal URL from our app.
        """
        # We'll handle this in our own UI
        portal_url = f"{self.settings.APP_URL}/account/billing"
        return PortalSession(
            id=f"portal_{customer_id}",
            url=portal_url
        )

    async def get_subscription(
        self,
        subscription_id: str
    ) -> Optional[Subscription]:
        """Get Razorpay subscription details."""
        try:
            sub = self.client.subscription.fetch(subscription_id)

            tier_value = sub.get("notes", {}).get("tier", "free")
            tier = SubscriptionTier(tier_value)

            status_map = {
                "active": SubscriptionStatus.ACTIVE,
                "cancelled": SubscriptionStatus.CANCELLED,
                "pending": SubscriptionStatus.INCOMPLETE,
                "halted": SubscriptionStatus.PAST_DUE,
                "completed": SubscriptionStatus.CANCELLED
            }

            current_start = datetime.fromtimestamp(sub.get("current_start", 0))
            current_end = datetime.fromtimestamp(sub.get("current_end", 0))

            return Subscription(
                id=sub["id"],
                user_id=sub.get("notes", {}).get("user_id", ""),
                tier=tier,
                status=status_map.get(sub["status"], SubscriptionStatus.ACTIVE),
                current_period_start=current_start,
                current_period_end=current_end,
                cancel_at_period_end=sub.get("ended_at") is not None,
                cancelled_at=datetime.fromtimestamp(sub["ended_at"]) if sub.get("ended_at") else None,
                stripe_subscription_id=sub["id"],  # Using same field for Razorpay ID
                stripe_customer_id=sub.get("customer_id"),
                payment_method=None  # Razorpay handles this differently
            )
        except Exception as e:
            logger.error(f"Razorpay error getting subscription: {e}")
            return None

    async def update_subscription(
        self,
        subscription_id: str,
        tier: SubscriptionTier
    ) -> Subscription:
        """Update Razorpay subscription to new tier."""
        try:
            new_plan_id = self._get_plan_id(tier)

            # Razorpay requires cancelling and creating new subscription
            # for plan changes, or use update with plan_id
            self.client.subscription.update(subscription_id, {
                "plan_id": new_plan_id,
                "notes": {"tier": tier.value}
            })

            logger.info(f"Updated Razorpay subscription {subscription_id} to tier: {tier.value}")
            return await self.get_subscription(subscription_id)
        except Exception as e:
            logger.error(f"Razorpay error updating subscription: {e}")
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Subscription:
        """Cancel Razorpay subscription."""
        try:
            if cancel_at_period_end:
                # Cancel at end of current cycle
                self.client.subscription.cancel(subscription_id, {
                    "cancel_at_cycle_end": 1
                })
            else:
                # Cancel immediately
                self.client.subscription.cancel(subscription_id)

            logger.info(f"Cancelled Razorpay subscription: {subscription_id}")
            return await self.get_subscription(subscription_id)
        except Exception as e:
            logger.error(f"Razorpay error cancelling subscription: {e}")
            raise

    async def reactivate_subscription(
        self,
        subscription_id: str
    ) -> Subscription:
        """
        Reactivate a Razorpay subscription.
        Razorpay doesn't support reactivation directly - need to create new.
        """
        try:
            # Get current subscription to get customer and plan
            sub = self.client.subscription.fetch(subscription_id)

            if sub["status"] != "cancelled":
                raise ValueError("Subscription is not cancelled")

            # Create a new subscription with same details
            new_sub = self.client.subscription.create({
                "plan_id": sub["plan_id"],
                "customer_id": sub["customer_id"],
                "total_count": 12,
                "notes": sub.get("notes", {})
            })

            logger.info(f"Reactivated Razorpay subscription: {new_sub['id']}")
            return await self.get_subscription(new_sub["id"])
        except Exception as e:
            logger.error(f"Razorpay error reactivating subscription: {e}")
            raise

    async def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Invoice]:
        """Get customer invoices from Razorpay."""
        try:
            invoices = self.client.invoice.all({
                "customer_id": customer_id,
                "count": limit
            })

            return [
                Invoice(
                    id=inv["id"],
                    number=inv.get("invoice_number"),
                    amount_due=inv.get("amount_due", 0),
                    amount_paid=inv.get("amount_paid", 0),
                    currency=inv.get("currency", "inr"),
                    status=inv.get("status", ""),
                    paid=inv.get("status") == "paid",
                    created_at=datetime.fromtimestamp(inv.get("created_at", 0)),
                    due_date=datetime.fromtimestamp(inv.get("expire_by", 0)) if inv.get("expire_by") else None,
                    pdf_url=inv.get("short_url"),
                    hosted_invoice_url=inv.get("short_url")
                )
                for inv in invoices.get("items", [])
            ]
        except Exception as e:
            logger.error(f"Razorpay error getting invoices: {e}")
            return []

    async def get_payment_methods(
        self,
        customer_id: str
    ) -> List[PaymentMethod]:
        """
        Get customer payment methods.
        Razorpay doesn't store payment methods the same way as Stripe.
        """
        # Razorpay uses tokens which are single-use
        # For recurring, it uses emandate/UPI autopay
        return []

    async def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """Razorpay handles payment methods differently."""
        return True

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        """Verify and parse Razorpay webhook event."""
        import hmac
        import hashlib
        import json

        try:
            # Verify signature
            expected_signature = hmac.new(
                self.settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_signature, signature):
                raise ValueError("Invalid webhook signature")

            # Parse payload
            data = json.loads(payload)
            event_type = data.get("event", "")

            return WebhookEvent(
                id=data.get("payload", {}).get("payment", {}).get("entity", {}).get("id", ""),
                type=event_type,
                data=data.get("payload", {}),
                created_at=datetime.utcnow()
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Razorpay webhook error: {e}")
            raise


# ============================================================================
# STRATEGY FACTORY
# ============================================================================

_payment_strategy: Optional[PaymentStrategy] = None


def get_payment_strategy() -> PaymentStrategy:
    """
    Get the configured payment strategy.
    Factory function for dependency injection.
    """
    global _payment_strategy

    if _payment_strategy is None:
        settings = get_payment_settings()

        if settings.PAYMENT_PROVIDER == PaymentProvider.STRIPE:
            _payment_strategy = StripePaymentStrategy()
        elif settings.PAYMENT_PROVIDER == PaymentProvider.RAZORPAY:
            _payment_strategy = RazorpayPaymentStrategy()
        else:
            # Default to Stripe
            _payment_strategy = StripePaymentStrategy()

    return _payment_strategy


def set_payment_strategy(strategy: PaymentStrategy) -> None:
    """
    Set payment strategy (useful for testing).
    """
    global _payment_strategy
    _payment_strategy = strategy

