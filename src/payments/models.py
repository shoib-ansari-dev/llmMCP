"""
Payment Models
Pydantic models for payment operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    UNPAID = "unpaid"


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    tier: SubscriptionTier
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreatePortalRequest(BaseModel):
    """Request to create a billing portal session."""
    return_url: Optional[str] = None


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription tier."""
    tier: SubscriptionTier


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription."""
    cancel_at_period_end: bool = True
    reason: Optional[str] = None


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SubscriptionPlan(BaseModel):
    """Subscription plan details."""
    tier: SubscriptionTier
    name: str
    description: str
    price_monthly: float
    price_yearly: Optional[float] = None
    features: List[str]
    limits: Dict[str, int]
    stripe_price_id: Optional[str] = None


class PaymentMethod(BaseModel):
    """Payment method details."""
    id: str
    type: str  # card, bank_account, etc.
    brand: Optional[str] = None  # visa, mastercard, etc.
    last4: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False


class Subscription(BaseModel):
    """User subscription details."""
    id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None


class PaymentIntent(BaseModel):
    """Payment intent details."""
    id: str
    amount: int  # In cents
    currency: str = "usd"
    status: PaymentStatus
    client_secret: Optional[str] = None
    created_at: datetime


class Invoice(BaseModel):
    """Invoice details."""
    id: str
    number: Optional[str] = None
    amount_due: int
    amount_paid: int
    currency: str = "usd"
    status: str
    paid: bool
    created_at: datetime
    due_date: Optional[datetime] = None
    pdf_url: Optional[str] = None
    hosted_invoice_url: Optional[str] = None


class CheckoutSession(BaseModel):
    """Checkout session details."""
    id: str
    url: str
    expires_at: datetime


class PortalSession(BaseModel):
    """Billing portal session."""
    id: str
    url: str


class WebhookEvent(BaseModel):
    """Webhook event from payment provider."""
    id: str
    type: str
    data: Dict[str, Any]
    created_at: datetime


# ============================================================================
# PLAN DEFINITIONS
# ============================================================================

SUBSCRIPTION_PLANS: List[SubscriptionPlan] = [
    SubscriptionPlan(
        tier=SubscriptionTier.FREE,
        name="Free",
        description="Get started with basic features",
        price_monthly=0,
        features=[
            "5 documents per month",
            "10 pages per document",
            "Basic AI summarization",
            "Email support"
        ],
        limits={
            "docs_per_month": 5,
            "pages_per_doc": 10,
            "api_calls_per_month": 100
        }
    ),
    SubscriptionPlan(
        tier=SubscriptionTier.PRO,
        name="Pro",
        description="For professionals and small teams",
        price_monthly=19.00,
        price_yearly=190.00,
        features=[
            "100 documents per month",
            "50 pages per document",
            "Advanced AI analysis",
            "Priority support",
            "API access",
            "Export to PDF/Word"
        ],
        limits={
            "docs_per_month": 100,
            "pages_per_doc": 50,
            "api_calls_per_month": 5000
        }
    ),
    SubscriptionPlan(
        tier=SubscriptionTier.BUSINESS,
        name="Business",
        description="For growing businesses",
        price_monthly=49.00,
        price_yearly=490.00,
        features=[
            "1000 documents per month",
            "200 pages per document",
            "Custom AI prompts",
            "Team collaboration",
            "Dedicated support",
            "SSO integration",
            "Analytics dashboard"
        ],
        limits={
            "docs_per_month": 1000,
            "pages_per_doc": 200,
            "api_calls_per_month": 50000
        }
    ),
    SubscriptionPlan(
        tier=SubscriptionTier.ENTERPRISE,
        name="Enterprise",
        description="For large organizations",
        price_monthly=199.00,
        price_yearly=1990.00,
        features=[
            "Unlimited documents",
            "Unlimited pages",
            "Custom AI models",
            "White-label option",
            "24/7 support",
            "On-premise deployment",
            "Custom integrations",
            "SLA guarantee"
        ],
        limits={
            "docs_per_month": 999999,
            "pages_per_doc": 999999,
            "api_calls_per_month": 999999
        }
    )
]


def get_plan_by_tier(tier: SubscriptionTier) -> Optional[SubscriptionPlan]:
    """Get subscription plan by tier."""
    for plan in SUBSCRIPTION_PLANS:
        if plan.tier == tier:
            return plan
    return None

