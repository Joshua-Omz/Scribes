"""
Notification-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class NotificationBase(BaseSchema):
    """Base notification schema with common fields."""
    
    title: str = Field(
        ...,
        max_length=200,
        description="Notification title",
        examples=["New reminder due"]
    )
    message: str = Field(
        ...,
        description="Notification message",
        examples=["Your reminder for 'Bible Study' is due in 1 hour"]
    )
    notification_type: Optional[str] = Field(
        "info",
        description="Notification type: info, warning, error, success, reminder",
        examples=["reminder"]
    )
    priority: Optional[str] = Field(
        "medium",
        description="Priority level: low, medium, high",
        examples=["medium"]
    )
    action_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to navigate when notification is clicked",
        examples=["/notes/123"]
    )
    extra_data: Optional[str] = Field(
        None,
        description="Additional data as JSON string (renamed from metadata to avoid conflicts)",
        examples=['{"note_id": 123, "reminder_id": 456}']
    )


class NotificationCreate(NotificationBase):
    """Schema for creating notification (internal use)."""
    
    user_id: int = Field(..., description="User ID to send notification to", examples=[1])
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "title": "New reminder due",
                    "message": "Your reminder for 'Bible Study' is due in 1 hour",
                    "notification_type": "reminder",
                    "priority": "high",
                    "action_url": "/notes/123"
                }
            ]
        }
    }


class NotificationUpdate(BaseSchema):
    """Schema for updating notification."""
    
    is_read: Optional[bool] = Field(
        None,
        description="Mark notification as read/unread",
        examples=[True]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_read": True
                }
            ]
        }
    }


class NotificationResponse(NotificationBase):
    """Schema for notification response."""
    
    id: int
    user_id: int = Field(..., description="User who received the notification")
    is_read: bool = Field(..., description="Read status")
    created_at: datetime = Field(..., description="When notification was created")
    read_at: Optional[datetime] = Field(None, description="When notification was read")
    
    model_config = BaseSchema.model_config


class NotificationListResponse(BaseSchema):
    """Schema for list of notifications with pagination."""
    
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 50,
                    "unread_count": 5,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


class NotificationMarkAllReadRequest(BaseSchema):
    """Schema for marking all notifications as read."""
    
    notification_ids: Optional[List[int]] = Field(
        None,
        description="Specific notification IDs to mark as read (if None, marks all)",
        examples=[[1, 2, 3]]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "notification_ids": [1, 2, 3]
                },
                {}
            ]
        }
    }
