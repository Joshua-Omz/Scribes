"""
Circle-related Pydantic schemas for request/response validation.
"""

from typing import Optional, List
from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class CircleBase(BaseSchema):
    """Base circle schema with common fields."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Circle name",
        examples=["Bible Study Group"]
    )
    description: Optional[str] = Field(
        None,
        description="Circle description",
        examples=["A group dedicated to studying the Bible together"]
    )
    is_private: Optional[bool] = Field(
        False,
        description="Whether the circle is private or public",
        examples=[False]
    )


class CircleCreate(CircleBase):
    """Schema for creating a circle."""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Bible Study Group",
                    "description": "A group dedicated to studying the Bible together",
                    "is_private": False
                }
            ]
        }
    }


class CircleUpdate(BaseSchema):
    """Schema for updating a circle."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated circle name",
        examples=["Updated Circle Name"]
    )
    description: Optional[str] = Field(
        None,
        description="Updated description",
        examples=["Updated description"]
    )
    is_private: Optional[bool] = Field(
        None,
        description="Updated privacy setting",
        examples=[True]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Circle Name",
                    "description": "Updated description",
                    "is_private": True
                }
            ]
        }
    }


class CircleResponse(CircleBase, TimestampSchema):
    """Schema for circle response."""
    
    id: int
    owner_id: int = Field(..., description="User ID of the circle owner")
    
    model_config = BaseSchema.model_config


class CircleDetailResponse(CircleResponse):
    """Schema for detailed circle response with member count."""
    
    members_count: Optional[int] = Field(0, description="Number of members in the circle")
    notes_count: Optional[int] = Field(0, description="Number of notes shared in the circle")
    
    model_config = BaseSchema.model_config


class CircleListResponse(BaseSchema):
    """Schema for paginated list of circles."""
    
    items: List[CircleResponse]
    total: int
    page: int
    page_size: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 10,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


# Circle Member Schemas

class CircleMemberBase(BaseSchema):
    """Base circle member schema."""
    
    user_id: int = Field(..., description="User ID to add as member", examples=[1])
    role: Optional[str] = Field(
        "member",
        description="Member role: owner, admin, member",
        examples=["member"]
    )


class CircleMemberCreate(CircleMemberBase):
    """Schema for adding a member to a circle."""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "role": "member"
                }
            ]
        }
    }


class CircleMemberUpdate(BaseSchema):
    """Schema for updating a circle member."""
    
    role: Optional[str] = Field(
        None,
        description="Updated role: admin, member",
        examples=["admin"]
    )
    status: Optional[str] = Field(
        None,
        description="Updated status: invited, active, inactive",
        examples=["active"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "admin",
                    "status": "active"
                }
            ]
        }
    }


class CircleMemberResponse(BaseSchema):
    """Schema for circle member response."""
    
    id: int
    circle_id: int = Field(..., description="Circle ID")
    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="Member role")
    status: str = Field(..., description="Membership status")
    joined_at: str = Field(..., description="Join timestamp")
    invited_by: Optional[int] = Field(None, description="User ID who invited this member")
    
    model_config = BaseSchema.model_config


class CircleMemberListResponse(BaseSchema):
    """Schema for list of circle members."""
    
    items: List[CircleMemberResponse]
    total: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 5
                }
            ]
        }
    }


# Circle Note Schemas

class CircleNoteCreate(BaseSchema):
    """Schema for sharing a note to a circle."""
    
    note_id: int = Field(..., description="Note ID to share", examples=[1])
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "note_id": 1
                }
            ]
        }
    }


class CircleNoteResponse(BaseSchema):
    """Schema for circle note response."""
    
    id: int
    circle_id: int = Field(..., description="Circle ID")
    note_id: int = Field(..., description="Note ID")
    shared_at: str = Field(..., description="Share timestamp")
    
    model_config = BaseSchema.model_config
