"""User schemas.

This module defines Pydantic schemas for user-related requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator

from app.schemas.common import BaseSchema, TimestampSchema


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None

    @validator('username')
    def username_must_be_valid(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.strip().lower()

    @validator('full_name')
    def full_name_must_be_valid(cls, v):
        if v is not None and len(v.strip()) > 100:
            raise ValueError('Full name must be at most 100 characters long')
        return v.strip() if v else v


class UserCreate(UserBase):
    """Schema for user creation requests."""
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserUpdate(BaseModel):
    """Schema for user update requests."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None

    @validator('username')
    def username_must_be_valid(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError('Username cannot be empty')
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username must be at most 50 characters long')
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            return v.strip().lower()
        return v

    @validator('full_name')
    def full_name_must_be_valid(cls, v):
        if v is not None and len(v.strip()) > 100:
            raise ValueError('Full name must be at most 100 characters long')
        return v.strip() if v else v

    @validator('password')
    def password_must_be_strong(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not any(char.isdigit() for char in v):
                raise ValueError('Password must contain at least one digit')
            if not any(char.isupper() for char in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(char.islower() for char in v):
                raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserInDB(UserBase):
    """Schema for user data from the database."""
    id: int
    role: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """Schema for user responses (without sensitive data)."""
    pass
    


class UserProfileResponse(UserResponse):
    """Schema for detailed user profile responses."""
    notes_count: int = 0
    reminders_count: int = 0
    active_reminders_count: int = 0


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    superuser_count: int
    recent_registrations: int


class ChangePasswordRequest(BaseModel):
    """Schema for password change requests."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


# Alias for backward compatibility
PasswordChange = ChangePasswordRequest


class UserSearchRequest(BaseModel):
    """Schema for user search and filtering."""
    query: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)


class Token(BaseModel):
    """Schema for token responses."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload data."""
    sub: Optional[int] = None
    exp: Optional[datetime] = None
    token_type: Optional[str] = None


class TokenData(BaseModel):
    """Schema for data extracted from a token."""
    user_id: Optional[int] = None

