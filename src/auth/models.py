"""
User Models
Pydantic models for user data.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class AuthProvider(str, Enum):
    """Authentication provider types."""
    EMAIL = "email"
    GOOGLE = "google"


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """User registration model."""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response model (no sensitive data)."""
    id: str
    provider: AuthProvider
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """User model as stored in database."""
    id: str
    password_hash: Optional[str] = None
    provider: AuthProvider = AuthProvider.EMAIL
    google_id: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: str
    exp: int
    iat: int
    type: str  # "access" or "refresh"


class PasswordReset(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class GoogleAuthRequest(BaseModel):
    """Google OAuth callback model."""
    code: str
    state: Optional[str] = None


class DevUser(BaseModel):
    """Development mode user (auto-login)."""
    id: str = "dev-user-001"
    email: str = "dev@example.com"
    name: str = "Development User"
    provider: AuthProvider = AuthProvider.EMAIL
    is_active: bool = True
    is_verified: bool = True

