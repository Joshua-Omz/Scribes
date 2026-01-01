"""
User profile-related Pydantic schemas for request/response validation.
"""

from typing import Optional
from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, TimestampSchema


class UserProfileBase(BaseSchema):
    """Base user profile schema with common fields."""
    
    bio: Optional[str] = Field(
        None,
        max_length=1000,
        description="User biography",
        examples=["Passionate about theology and scripture study"]
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Avatar/profile picture URL",
        examples=["https://example.com/avatar.jpg"]
    )
    phone_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Phone number",
        examples=["+1234567890"]
    )
    location: Optional[str] = Field(
        None,
        max_length=100,
        description="User location",
        examples=["San Francisco, CA"]
    )
    website: Optional[str] = Field(
        None,
        max_length=500,
        description="Personal website URL",
        examples=["https://johndoe.com"]
    )
    preferences: Optional[str] = Field(
        None,
        description="User preferences as JSON string",
        examples=['{"theme": "dark", "notifications": true}']
    )


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile."""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bio": "Passionate about theology and scripture study",
                    "location": "San Francisco, CA",
                    "preferences": '{"theme": "dark", "notifications": true}'
                }
            ]
        }
    }


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile."""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bio": "Updated biography",
                    "avatar_url": "https://example.com/new-avatar.jpg"
                }
            ]
        }
    }


class UserProfileResponse(UserProfileBase, TimestampSchema):
    """Schema for user profile response."""
    
    id: int
    user_id: int = Field(..., description="Associated user ID")
    
    model_config = BaseSchema.model_config
