"""
Authentication API routes.
Handles user registration, login, and token management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_active_user, get_current_admin_user
from app.models.user_model import User
from app.schemas.user_schemas import (
    UserCreate, 
    UserResponse, 
    PasswordChange, 
    UserListResponse,
    UserUpdate
)
from app.schemas.auth_schemas import (
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)
from app.services.business.auth_service import AuthService


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
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Resend verification email to an existing unverified user."
)
async def resend_verification(
    request: ForgotPasswordRequest,  # Reuse schema (just needs email)
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Resend verification email.
    
    - **email**: User email address
    
    Generates a new verification token and sends it via email.
    Always returns success to prevent email enumeration.
    """
    from app.repositories.user_repository import UserRepository
    from app.core.security import create_verification_token
    from app.utils.email import send_verification_email
    from app.core.config import settings
    
    user_repo = UserRepository(db)
    
    # Get user by email
    user = await user_repo.get_by_email(request.email)
    
    # Always return success to prevent email enumeration
    if not user:
        return MessageResponse(
            message="If the email exists and is unverified, a verification email has been sent",
            detail="Check your inbox and spam folder"
        )
    
    # Check if already verified
    if user.is_verified:
        return MessageResponse(
            message="If the email exists and is unverified, a verification email has been sent",
            detail="Check your inbox and spam folder"
        )
    
    # Generate new verification token
    verification_token = create_verification_token(user.email)
    
    # DEBUG: Print token in development mode
    if settings.debug:
        print(f"\n{'='*70}")
        print(f"🔑 RESENT VERIFICATION TOKEN (DEVELOPMENT MODE ONLY)")
        print(f"{'='*70}")
        print(f"📧 Email: {user.email}")
        print(f"🎫 Token: {verification_token}")
        print(f"{'='*70}")
        print(f"Use this token in POST /auth/verify-email")
        print(f"{'='*70}\n")
    
    # Send verification email
    try:
        await send_verification_email(user.email, verification_token)
    except Exception as e:
        print(f"Failed to send verification email: {str(e)}")
    
    return MessageResponse(
        message="If the email exists and is unverified, a verification email has been sent",
        detail="Check your inbox and spam folder"
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
    
    This is a hard delete
    """
    from app.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    
    # Deactivate account instead of hard delete
    await user_repo.delete(current_user.id)
    await db.commit()
    
    return MessageResponse(
        message="Account deleted successfully",
        detail="Your account has been deleted permanently , meaning all data regarding the user is gone"
    )

@router.put(
        "/me",
        response_model=MessageResponse,
        summary="Deactivate account",
        description= "Deactivate the current account you are logged in on"
)
async def deactivate_accout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)

)-> MessageResponse:
    """
    Deactivate user account
    
    Requires authentication (bearer token) and the account.
    
    Deactivates the account (soft delete)"""
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)

    await user_repo.deactivate(current_user.id)
    await db.commit()

    return MessageResponse(
        message="Account deleted successfully",
        detail= "your account has been deactivated"
    )

@router.put(
        "/me",
        response_model=MessageResponse,
        summary="Reactivate account",
        description= "Reactivate the current account you are logged in on"
)
async def reactivate_accout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)

)-> MessageResponse:
    """
    Deactivate user account
    
    Requires authentication (bearer token) and the account.
    
    reeactivates the account that has been previously deactivated"""
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)

    await user_repo.deactivate(current_user.id)
    await db.commit()

    return MessageResponse(
        message="Account deleted successfully",
        detail= "your account has been deactivated"
    )




@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Get all users",
    description="Fetch all users from the database with optional filtering and pagination."
)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserListResponse:
    """
    Get all users with pagination and filtering.
    
    Requires authentication (Bearer token).
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 100)
    - **is_active**: Filter by active status (optional)
    
    Returns paginated list of users.
    """
    from app.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    
    # Validate limit
    if limit > 100:
        limit = 100
    
    # Fetch users
    users = await user_repo.list_users(skip=skip, limit=limit, is_active=is_active)
    
    # Get total count
    total = await user_repo.count_users(is_active=is_active)
    
    # Convert to response schema
    user_responses = [UserResponse.model_validate(user) for user in users]
    
    return UserListResponse(
        users=user_responses,
        total=total,
        skip=skip,
        limit=limit
    )


# ==================== ADMIN MANAGEMENT ENDPOINTS ====================


@router.post(
    "/admin/verify-user/{user_id}",
    response_model=UserResponse,
    summary="Manually verify user email",
    description="Admin endpoint to manually verify a user's email (bypasses token requirement)."
)
async def admin_verify_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Manually verify a user's email (admin only).
    
    Requires admin privileges.
    
    - **user_id**: ID of user to verify
    
    Returns updated user data with is_verified=true.
    """
    from app.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    
    # Get target user
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email is already verified"
        )
    
    # Verify user
    verified_user = await user_repo.verify_email(user_id)
    await db.commit()
    
    return UserResponse.model_validate(verified_user)


@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admin user",
    description="Create a new user with admin privileges (requires admin access)."
)
async def create_admin_user(
    user_data: UserCreate,
    is_superuser: bool = True,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Create a new admin user.
    
    Requires admin privileges.
    
    - **email**: Valid email address (unique)
    - **username**: Username (unique, 3-50 chars)
    - **password**: Strong password (min 8 chars, upper, lower, digit)
    - **full_name**: Optional full name
    - **is_superuser**: Whether user should be superuser (default: True)
    
    Returns created admin user data.
    """
    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password
    
    user_repo = UserRepository(db)
    
    # Check if email already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await user_repo.get_by_username(user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create admin user
    user = await user_repo.create_admin(user_data, hashed_password, is_superuser)
    await db.commit()
    
    return UserResponse.model_validate(user)


@router.patch(
    "/admin/users/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role",
    description="Change a user's role between 'user' and 'admin' (requires admin access)."
)
async def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update a user's role.
    
    Requires admin privileges.
    
    - **user_id**: ID of user to update
    - **role**: New role ('user' or 'admin')
    
    Returns updated user data.
    """
    from app.repositories.user_repository import UserRepository
    
    # Validate role
    if role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )
    
    user_repo = UserRepository(db)
    
    # Get target user
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-demotion
    if user.id == current_user.id and role == "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin role"
        )
    
    # Update role
    updated_user = await user_repo.update_role(user_id, role)
    await db.commit()
    
    return UserResponse.model_validate(updated_user)


@router.patch(
    "/admin/users/{user_id}/superuser",
    response_model=UserResponse,
    summary="Update superuser status",
    description="Toggle a user's superuser status (requires admin access)."
)
async def update_superuser_status(
    user_id: int,
    is_superuser: bool,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update a user's superuser status.
    
    Requires admin privileges.
    
    - **user_id**: ID of user to update
    - **is_superuser**: Superuser status (true or false)
    
    Returns updated user data.
    """
    from app.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db)
    
    # Get target user
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-demotion
    if user.id == current_user.id and not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own superuser status"
        )
    
    # Update superuser status
    updated_user = await user_repo.update_superuser(user_id, is_superuser)
    await db.commit()
    
    return UserResponse.model_validate(updated_user)


@router.patch(
    "/admin/users/{user_id}/privileges",
    response_model=UserResponse,
    summary="Update user privileges",
    description="Update multiple user privileges at once (requires admin access)."
)
async def update_user_privileges(
    user_id: int,
    role: Optional[str] = None,
    is_superuser: Optional[bool] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update multiple user privileges at once.
    
    Requires admin privileges.
    
    - **user_id**: ID of user to update
    - **role**: New role ('user' or 'admin') - optional
    - **is_superuser**: Superuser status - optional
    - **is_active**: Active status - optional
    
    Returns updated user data.
    """
    from app.repositories.user_repository import UserRepository
    
    # Validate inputs
    if role is not None and role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )
    
    if role is None and is_superuser is None and is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one privilege must be specified"
        )
    
    user_repo = UserRepository(db)
    
    # Get target user
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-demotion
    if user.id == current_user.id:
        if role == "user" or (is_superuser is not None and not is_superuser):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote your own privileges"
            )
    
    # Update privileges
    updated_user = await user_repo.update_privileges(
        user_id,
        role=role,
        is_superuser=is_superuser,
        is_active=is_active
    )
    await db.commit()
    
    return UserResponse.model_validate(updated_user)
