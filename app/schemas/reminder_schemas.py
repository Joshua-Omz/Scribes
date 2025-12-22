"""
Reminder-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, TimestampSchema


class ReminderBase(BaseSchema):
    """Base reminder schema with common fields."""
    
    note_id: int = Field(
        ...,
        description="Note ID to set reminder for",
        examples=[1]
    )
    scheduled_at: datetime = Field(
        ...,
        description="When to trigger the reminder (ISO format)",
        examples=["2025-11-01T10:00:00Z"]
    )


class ReminderCreate(ReminderBase):
    """Schema for creating a reminder."""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "note_id": 1,
                    "scheduled_at": "2025-11-01T10:00:00Z"
                }
            ]
        }
    }
    
    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: datetime) -> datetime:
        """Ensure scheduled_at is in the future."""
        if v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v


class ReminderUpdate(BaseSchema):
    """Schema for updating a reminder."""
    
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Updated reminder time",
        examples=["2025-11-02T10:00:00Z"]
    )
    status: Optional[str] = Field(
        None,
        description="Updated status: pending, sent, cancelled",
        examples=["cancelled"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scheduled_at": "2025-11-02T10:00:00Z",
                    "status": "pending"
                }
            ]
        }
    }
    
    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled_at is in the future if provided."""
        if v and v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v


class ReminderResponse(ReminderBase, TimestampSchema):
    """Schema for reminder response."""
    
    id: int
    user_id: int = Field(..., description="User who set the reminder")
    status: str = Field(
        ...,
        description="Reminder status: pending, sent, cancelled",
        examples=["pending"]
    )
    
    model_config = BaseSchema.model_config


class ReminderDetailResponse(ReminderResponse):
    """Schema for detailed reminder response with note info."""
    
    note_title: Optional[str] = Field(None, description="Title of the associated note")
    note_content_preview: Optional[str] = Field(
        None,
        description="Preview of the note content",
        examples=["This note discusses..."]
    )
    
    model_config = BaseSchema.model_config


class ReminderListResponse(BaseSchema):
    """Schema for paginated list of reminders."""
    
    items: List[ReminderResponse]
    total: int
    page: int
    page_size: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 15,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


class ReminderFilterRequest(BaseSchema):
    """Schema for filtering reminders."""
    
    status: Optional[str] = Field(
        None,
        description="Filter by status: pending, sent, cancelled",
        examples=["pending"]
    )
    date_from: Optional[str] = Field(
        None,
        description="Filter reminders from this date (ISO format)",
        examples=["2025-11-01"]
    )
    date_to: Optional[str] = Field(
        None,
        description="Filter reminders up to this date (ISO format)",
        examples=["2025-11-30"]
    )
    note_id: Optional[int] = Field(
        None,
        description="Filter by specific note ID",
        examples=[1]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "pending",
                    "date_from": "2025-11-01",
                    "date_to": "2025-11-30"
                }
            ]
        }
    }
