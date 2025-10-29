"""
Authentication-related Pydantic schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema


class LoginRequest(BaseSchema):
    """Schema for user login request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseSchema):
    """Schema for token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenRefreshRequest(BaseSchema):
    """Schema for token refresh request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenRefreshResponse(BaseSchema):
    """Schema for token refresh response."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class EmailVerificationRequest(BaseSchema):
    """Schema for email verification request."""
    
    token: str = Field(..., description="Email verification token")


class ForgotPasswordRequest(BaseSchema):
    """Schema for forgot password request."""
    
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseSchema):
    """Schema for password reset request."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")


class MessageResponse(BaseSchema):
    """Generic message response."""
    
    message: str = Field(..., description="Response message")
    detail: Optional[str] = Field(None, description="Additional details")


class TokenPayload(BaseSchema):
    """Schema for JWT token payload."""
    
    sub: str = Field(..., description="Subject (user ID or email)")
    exp: datetime = Field(..., description="Expiration time")
    type: str = Field(..., description="Token type: access, refresh, verification, reset")
    user_id: Optional[int] = Field(None, description="User ID")
