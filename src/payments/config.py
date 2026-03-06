"""
Payment Configuration
Settings for payment providers.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from enum import Enum


class PaymentProvider(str, Enum):
    """Supported payment providers."""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    # Future: PAYPAL = "paypal"


class PaymentSettings(BaseSettings):
    """Payment configuration from environment variables."""

    # Active provider
    PAYMENT_PROVIDER: PaymentProvider = PaymentProvider.STRIPE

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Stripe Product/Price IDs
    STRIPE_PRICE_FREE: str = ""  # Free tier (no charge)
    STRIPE_PRICE_PRO: str = ""  # Pro tier monthly
    STRIPE_PRICE_BUSINESS: str = ""  # Business tier monthly
    STRIPE_PRICE_ENTERPRISE: str = ""  # Enterprise tier monthly

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # Razorpay Plan IDs
    RAZORPAY_PLAN_FREE: str = ""
    RAZORPAY_PLAN_PRO: str = ""
    RAZORPAY_PLAN_BUSINESS: str = ""
    RAZORPAY_PLAN_ENTERPRISE: str = ""

    # Application URLs
    APP_URL: str = "http://localhost:5173"
    PAYMENT_SUCCESS_URL: str = "/payment/success"
    PAYMENT_CANCEL_URL: str = "/payment/cancel"

    # Trial settings
    TRIAL_DAYS: int = 14

    # Currency settings
    DEFAULT_CURRENCY: str = "usd"  # Use "inr" for Razorpay in India

    @property
    def success_url(self) -> str:
        return f"{self.APP_URL}{self.PAYMENT_SUCCESS_URL}"

    @property
    def cancel_url(self) -> str:
        return f"{self.APP_URL}{self.PAYMENT_CANCEL_URL}"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_payment_settings() -> PaymentSettings:
    """Get cached payment settings."""
    return PaymentSettings()


# Price ID mapping for tiers
TIER_PRICE_MAP = {
    "free": "STRIPE_PRICE_FREE",
    "pro": "STRIPE_PRICE_PRO",
    "business": "STRIPE_PRICE_BUSINESS",
    "enterprise": "STRIPE_PRICE_ENTERPRISE"
}

