"""
Authentication API routes.
Handles user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.user_model import User
from app.schemas.user import UserCreate, UserResponse, PasswordChange
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account. Returns user data and sends verification email."
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register a new user.
    
    - **email**: Valid email address (unique)
    - **username**: Username (unique, 3-50 chars)
    - **password**: Strong password (min 8 chars, upper, lower, digit)
    - **full_name**: Optional full name
    
    Returns user data (without password) and sends verification email.
    """
    auth_service = AuthService(db)
    
    user, verification_token = await auth_service.register(user_data)
    
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return access and refresh tokens."
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Login user with email and password.
    
    - **email**: User email address
    - **password**: User password
    
    Returns access token and refresh token.
    """
    auth_service = AuthService(db)
    
    return await auth_service.login(credentials.email, credentials.password)


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh access token",
    description="Generate new access token using refresh token."
)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenRefreshResponse:
    """
    Refresh access token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token.
    """
    auth_service = AuthService(db)
    
    access_token = await auth_service.refresh_access_token(request.refresh_token)
    
    from app.core.config import settings
    
    return TokenRefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email",
    description="Verify user email with verification token."
)
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Verify user email.
    
    - **token**: Email verification token from email
    
    Marks user as verified.
    """
    auth_service = AuthService(db)
    
    await auth_service.verify_email(request.token)
    
    return MessageResponse(
        message="Email verified successfully",
        detail="You can now access all features"
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Send password reset email to user."
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Request password reset.
    
    - **email**: User email address
    
    Sends password reset email if user exists.
    Always returns success to prevent email enumeration.
    """
    auth_service = AuthService(db)
    
    await auth_service.forgot_password(request.email)
    
    return MessageResponse(
        message="Password reset email sent",
        detail="Check your email for password reset instructions"
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset user password with reset token."
)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Reset user password.
    
    - **token**: Password reset token from email
    - **new_password**: New password
    
    Updates password and revokes all refresh tokens.
    """
    auth_service = AuthService(db)
    
    await auth_service.reset_password(request.token, request.new_password)
    
    return MessageResponse(
        message="Password reset successfully",
        detail="Please login with your new password"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get current authenticated user information."
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user profile.
    
    Requires authentication (Bearer token).
    
    Returns current user data.
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update current user profile information."
)
async def update_me(
    user_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update current user profile.
    
    Requires authentication (Bearer token) and active account.
    
    - **email**: New email (optional)
    - **username**: New username (optional)
    - **full_name**: New full name (optional)
    
    Returns updated user data.
    """
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import UserUpdate
    
    user_repo = UserRepository(db)
    
    # Create update schema
    update_data = UserUpdate(**user_data)
    
    # Update user
    updated_user = await user_repo.update(current_user.id, update_data)
    await db.commit()
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(updated_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change current user password."
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Change user password.
    
    Requires authentication (Bearer token) and active account.
    
    - **current_password**: Current password
    - **new_password**: New password
    
    Updates password and revokes all refresh tokens.
    """
    from app.core.security import verify_password, hash_password
    from app.repositories.user_repository import UserRepository
    from app.models.refresh_model import RefreshToken
    from sqlalchemy import update
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    hashed_password = hash_password(password_data.new_password)
    
    # Update password
    user_repo = UserRepository(db)
    await user_repo.update_password(current_user.id, hashed_password)
    
    # Revoke all refresh tokens
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .values(revoked=True)
    )
    
    await db.commit()
    
    return MessageResponse(
        message="Password changed successfully",
        detail="Please login again with your new password"
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logout user by revoking refresh token."
)
async def logout(
    request: TokenRefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Logout user.
    
    Requires authentication (Bearer token).
    
    - **refresh_token**: Refresh token to revoke
    
    Revokes the refresh token.
    """
    auth_service = AuthService(db)
    
    await auth_service.revoke_refresh_token(request.refresh_token)
    
    return MessageResponse(
        message="Logged out successfully",
        detail="Refresh token has been revoked"
    )


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete account",
    description="Delete current user account (soft delete by deactivating)."
)
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete user account.
    
    Requires authentication (Bearer token) and active account.
    
    Deactivates the account (soft delete).
    """
    from app.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    
    # Deactivate account instead of hard delete
    await user_repo.deactivate(current_user.id)
    await db.commit()
    
    return MessageResponse(
        message="Account deactivated successfully",
        detail="Your account has been deactivated"
    )
