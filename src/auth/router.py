"""
Authentication Router
FastAPI routes for authentication endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import RedirectResponse
from typing import Optional

from .config import get_auth_config
from .models import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordReset, PasswordResetConfirm, GoogleAuthRequest,
    AuthProvider
)
from .jwt import (
    create_tokens, refresh_access_token,
    create_password_reset_token, verify_password_reset_token
)
from .password import verify_password
from .store import get_user_store
from .google_oauth import get_google_oauth
from .email_service import get_email_service
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =================================
# Email/Password Authentication
# =================================

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """
    Register a new user with email and password.
    """
    config = get_auth_config()
    store = get_user_store()

    # Check if email already exists
    existing = await store.get_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    try:
        user = await store.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            provider=AuthProvider.EMAIL,
            is_verified=config.dev_mode  # Auto-verify in dev mode
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Create tokens
    return create_tokens(user.id, user.email)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login with email and password.
    """
    store = get_user_store()

    # Get user by email
    user = await store.get_by_email(credentials.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user registered with Google
    if user.provider == AuthProvider.GOOGLE and not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google sign-in. Please login with Google."
        )

    # Verify password
    if not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create tokens
    return create_tokens(user.id, user.email)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    """
    tokens = refresh_access_token(refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user.
    """
    return user


@router.post("/logout")
async def logout():
    """
    Logout user (client should discard tokens).
    """
    return {"message": "Logged out successfully"}


# =================================
# Password Reset
# =================================

@router.post("/forgot-password")
async def forgot_password(data: PasswordReset):
    """
    Request password reset email.
    """
    store = get_user_store()
    email_service = get_email_service()

    # Get user by email
    user = await store.get_by_email(data.email)

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If an account exists with this email, a reset link has been sent."}

    # Check if user uses Google auth
    if user.provider == AuthProvider.GOOGLE and not user.password_hash:
        return {"message": "If an account exists with this email, a reset link has been sent."}

    # Create reset token
    reset_token = create_password_reset_token(user.id, user.email)

    # Send email
    await email_service.send_password_reset_email(user.email, reset_token)

    return {"message": "If an account exists with this email, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    """
    Reset password using reset token.
    """
    store = get_user_store()

    # Verify token
    payload = verify_password_reset_token(data.token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    success = await store.update_password(payload.sub, data.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": "Password reset successfully"}


# =================================
# Google OAuth
# =================================

@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth login.
    Redirects to Google's authorization page.
    """
    config = get_auth_config()

    if not config.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )

    google = get_google_oauth()
    auth_url = google.get_authorization_url()

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None):
    """
    Handle Google OAuth callback.
    """
    config = get_auth_config()
    store = get_user_store()
    google = get_google_oauth()

    # Authenticate with Google
    user_info = await google.authenticate(code)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with Google"
        )

    google_id = user_info["google_id"]
    email = user_info["email"]
    name = user_info.get("name")

    # Check if user exists with this Google ID
    user = await store.get_by_google_id(google_id)

    if not user:
        # Check if email exists
        user = await store.get_by_email(email)

        if user:
            # Link Google account to existing user
            await store.link_google_account(user.id, google_id)
        else:
            # Create new user
            user = await store.create_user(
                email=email,
                name=name,
                provider=AuthProvider.GOOGLE,
                google_id=google_id,
                is_verified=True  # Google emails are verified
            )

    # Create tokens
    tokens = create_tokens(user.id, user.email)

    # Redirect to frontend with tokens
    redirect_url = f"{config.frontend_url}/auth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"

    return RedirectResponse(url=redirect_url)


# =================================
# Dev Mode Check
# =================================

@router.get("/dev-mode")
async def check_dev_mode():
    """
    Check if authentication is in development mode.
    """
    config = get_auth_config()
    return {
        "dev_mode": config.dev_mode,
        "message": "Authentication bypassed" if config.dev_mode else "Authentication required"
    }

