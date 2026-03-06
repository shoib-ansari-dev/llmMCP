"""
Payment Router
FastAPI endpoints for payment operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from src.database import get_db
from src.auth.dependencies import get_current_user, get_current_user_optional
from src.auth.models import UserInDB

from .service import PaymentService, get_all_plans
from .models import (
    CreateCheckoutRequest, CreatePortalRequest,
    UpdateSubscriptionRequest, CancelSubscriptionRequest,
    SubscriptionTier, CheckoutSession, PortalSession,
    Invoice, PaymentMethod, SUBSCRIPTION_PLANS
)

router = APIRouter(prefix="/payments", tags=["payments"])


# ============================================================================
# PLANS (Public)
# ============================================================================

@router.get("/plans")
async def get_plans():
    """
    Get all available subscription plans.
    Public endpoint.
    """
    return {
        "plans": get_all_plans()
    }


@router.get("/plans/{tier}")
async def get_plan(tier: str):
    """
    Get a specific plan by tier.
    """
    try:
        subscription_tier = SubscriptionTier(tier)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plan not found")

    for plan in SUBSCRIPTION_PLANS:
        if plan.tier == subscription_tier:
            return plan.model_dump()

    raise HTTPException(status_code=404, detail="Plan not found")


# ============================================================================
# CHECKOUT
# ============================================================================

@router.post("/checkout", response_model=CheckoutSession)
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Checkout session for subscription.
    """
    if request.tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=400,
            detail="Cannot checkout for free tier"
        )

    service = PaymentService(db)

    try:
        session = await service.create_checkout(
            user_id=current_user.id,
            email=current_user.email,
            tier=request.tier,
            name=current_user.name
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal", response_model=PortalSession)
async def create_billing_portal(
    request: CreatePortalRequest = None,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Billing Portal session.
    Users can manage subscriptions, payment methods, and invoices.
    """
    service = PaymentService(db)

    try:
        session = await service.create_billing_portal(user_id=current_user.id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUBSCRIPTION
# ============================================================================

@router.get("/subscription")
async def get_subscription(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription details.
    """
    service = PaymentService(db)
    subscription = await service.get_subscription(user_id=current_user.id)

    if not subscription:
        return {
            "tier": "free",
            "status": "active",
            "usage": {
                "docs_used": 0,
                "docs_limit": 5,
                "api_calls_used": 0,
                "api_calls_limit": 100
            }
        }

    return subscription


@router.post("/subscription/upgrade")
async def upgrade_subscription(
    request: UpdateSubscriptionRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upgrade subscription to a higher tier.
    For free -> paid, use checkout endpoint instead.
    """
    service = PaymentService(db)

    try:
        subscription = await service.upgrade_subscription(
            user_id=current_user.id,
            new_tier=request.tier
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest = None,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel subscription.
    By default, cancels at end of billing period.
    """
    cancel_at_period_end = True
    if request:
        cancel_at_period_end = request.cancel_at_period_end

    service = PaymentService(db)

    try:
        subscription = await service.cancel_subscription(
            user_id=current_user.id,
            cancel_at_period_end=cancel_at_period_end
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription/reactivate")
async def reactivate_subscription(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reactivate a cancelled subscription (before period ends).
    """
    service = PaymentService(db)

    try:
        subscription = await service.reactivate_subscription(
            user_id=current_user.id
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INVOICES & PAYMENT METHODS
# ============================================================================

@router.get("/invoices", response_model=List[Invoice])
async def get_invoices(
    limit: int = 10,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's invoices.
    """
    service = PaymentService(db)
    return await service.get_invoices(user_id=current_user.id, limit=limit)


@router.get("/payment-methods", response_model=List[PaymentMethod])
async def get_payment_methods(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's payment methods.
    """
    service = PaymentService(db)
    return await service.get_payment_methods(user_id=current_user.id)


# ============================================================================
# WEBHOOKS
# ============================================================================

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    This endpoint should be configured in Stripe Dashboard.
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    payload = await request.body()

    service = PaymentService(db)

    try:
        result = await service.handle_webhook(payload, stripe_signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Razorpay webhook events.
    This endpoint should be configured in Razorpay Dashboard.
    """
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay signature")

    payload = await request.body()

    service = PaymentService(db)

    try:
        result = await service.handle_webhook(payload, x_razorpay_signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUCCESS/CANCEL PAGES (Optional API endpoints)
# ============================================================================

@router.get("/success")
async def payment_success(
    session_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Payment success callback.
    Frontend usually handles this, but API can verify the session.
    """
    return {
        "status": "success",
        "message": "Payment completed successfully",
        "session_id": session_id
    }


@router.get("/cancel")
async def payment_cancel():
    """
    Payment cancellation callback.
    """
    return {
        "status": "cancelled",
        "message": "Payment was cancelled"
    }

