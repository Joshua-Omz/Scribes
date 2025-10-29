"""Pydantic schemas for request/response validation."""

from app.schemas.common import (
    BaseSchema,
    TimestampSchema,
    HealthResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    PasswordChange,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
    TokenPayload,
)

__all__ = [
    # Common
    "BaseSchema",
    "TimestampSchema",
    "HealthResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "PasswordChange",
    # Auth
    "LoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "EmailVerificationRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "MessageResponse",
    "TokenPayload",
]
