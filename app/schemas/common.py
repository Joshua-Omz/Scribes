"""Common Pydantic schemas used across the application."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None


class HealthResponse(BaseSchema):
    """Health check response schema."""
    
    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime


class ErrorResponse(BaseSchema):
    """Standard error response schema."""
    
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime


class PaginationParams(BaseSchema):
    """Pagination parameters schema."""
    
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
