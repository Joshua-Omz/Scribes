"""
Authentication service - Business logic for auth operations.
"""

from datetime import timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_verification_token,
    create_reset_token,
    decode_token,
)
from app.core.config import settings
from app.models.user_model import User
from app.models.refresh_model import RefreshToken
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import UserCreate
from app.schemas.auth_schemas import TokenResponse
from app.utils.email import send_verification_email, send_password_reset_email


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize auth service."""
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def register(self, user_data: UserCreate) -> Tuple[User, str]:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Tuple[User, str]: Created user and verification token
            
        Raises:
            HTTPException: If email or username already exists
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        existing_username = await self.user_repo.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user
        user = await self.user_repo.create(user_data, hashed_password)
        await self.db.commit()
        
        # Generate verification token
        verification_token = create_verification_token(user.email)
        
        # DEBUG: Print verification token in development mode
        if settings.debug:
            print(f"\n{'='*70}")
            print(f"🔑 EMAIL VERIFICATION TOKEN (DEVELOPMENT MODE ONLY)")
            print(f"{'='*70}")
            print(f"📧 Email: {user.email}")
            print(f"🎫 Token: {verification_token}")
            print(f"{'='*70}")
            print(f"Use this token in POST /auth/verify-email")
            print(f"{'='*70}\n")
        
        # Send verification email (async, non-blocking)
        try:
            await send_verification_email(user.email, verification_token)
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
            # Don't fail registration if email fails
        
        return user, verification_token
    
    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            TokenResponse: Access and refresh tokens
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        refresh_token_str = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Store refresh token in database
        from datetime import datetime, timedelta
        refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days),
            revoked=False
        )
        self.db.add(refresh_token)
        await self.db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
    
    async def verify_email(self, token: str) -> User:
        """
        Verify user email with token.
        
        Args:
            token: Verification token
            
        Returns:
            User: Verified user
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        # Decode token
        payload = decode_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        if payload.get("type") != "verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload"
            )
        
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Verify email
        user = await self.user_repo.verify_email(user.id)
        await self.db.commit()
        
        return user
    
    async def refresh_access_token(self, refresh_token_str: str) -> str:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token_str: Refresh token
            
        Returns:
            str: New access token
            
        Raises:
            HTTPException: If refresh token is invalid or revoked
        """
        # Decode refresh token
        payload = decode_token(refresh_token_str)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Check if refresh token exists and is not revoked
        from sqlalchemy import select
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token_str,
                RefreshToken.revoked == False
            )
        )
        refresh_token = result.scalar_one_or_none()
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or revoked"
            )
        
        # Get user
        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        
        return access_token
    
    async def forgot_password(self, email: str) -> bool:
        """
        Send password reset email.
        
        Args:
            email: User email
            
        Returns:
            bool: True if email sent successfully
        """
        # Get user
        user = await self.user_repo.get_by_email(email)
        
        # Always return success to prevent email enumeration
        if not user:
            return True
        
        # Generate reset token
        reset_token = create_reset_token(user.email)
        
        # Send reset email
        try:
            await send_password_reset_email(user.email, reset_token)
            return True
        except Exception as e:
            print(f"Failed to send password reset email: {str(e)}")
            return False
    
    async def reset_password(self, token: str, new_password: str) -> User:
        """
        Reset user password with token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            User: Updated user
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        # Decode token
        payload = decode_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        if payload.get("type") != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload"
            )
        
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update password
        user = await self.user_repo.update_password(user.id, hashed_password)
        await self.db.commit()
        
        # Revoke all refresh tokens for this user
        from sqlalchemy import update
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(revoked=True)
        )
        await self.db.commit()
        
        return user
    
    async def revoke_refresh_token(self, refresh_token_str: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token_str: Refresh token to revoke
            
        Returns:
            bool: True if revoked successfully
        """
        from sqlalchemy import select, update
        
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_str)
        )
        refresh_token = result.scalar_one_or_none()
        
        if not refresh_token:
            return False
        
        refresh_token.revoked = True
        await self.db.commit()
        
        return True
