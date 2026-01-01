"""Background job schemas for API request/response validation.

This module defines Pydantic schemas for background job tracking.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration."""
    EMBEDDING_REGENERATION = "embedding_regeneration"
    EXPORT = "export"
    REMINDER_BATCH = "reminder_batch"
    NOTE_IMPORT = "note_import"


class BackgroundJobBase(BaseModel):
    """Base schema for background jobs."""
    job_type: str = Field(..., description="Type of background job")
    

class BackgroundJobCreate(BackgroundJobBase):
    """Schema for creating a new background job."""
    user_id: Optional[int] = Field(None, description="User ID who initiated the job")
    total_items: Optional[int] = Field(None, description="Total number of items to process")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_type": "embedding_regeneration",
                "user_id": 1,
                "total_items": 150
            }
        }
    )


class BackgroundJobUpdate(BaseModel):
    """Schema for updating background job progress."""
    status: Optional[JobStatus] = Field(None, description="Updated job status")
    progress_percent: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    processed_items: Optional[int] = Field(None, ge=0, description="Number of items processed")
    failed_items: Optional[int] = Field(None, ge=0, description="Number of items that failed")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Result data as JSON")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "running",
                "progress_percent": 45,
                "processed_items": 68,
                "failed_items": 2
            }
        }
    )


class BackgroundJobResponse(BackgroundJobBase):
    """Schema for background job response."""
    id: int = Field(..., description="Database ID")
    job_id: UUID = Field(..., description="Unique job identifier")
    user_id: Optional[int] = Field(None, description="User ID who initiated the job")
    status: str = Field(..., description="Current job status")
    progress_percent: int = Field(0, description="Progress percentage (0-100)")
    total_items: Optional[int] = Field(None, description="Total items to process")
    processed_items: int = Field(0, description="Items successfully processed")
    failed_items: int = Field(0, description="Items that failed processing")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": 1,
                "job_type": "embedding_regeneration",
                "status": "running",
                "progress_percent": 67,
                "total_items": 150,
                "processed_items": 100,
                "failed_items": 1,
                "result_data": None,
                "error_message": None,
                "created_at": "2025-11-18T00:30:00Z",
                "started_at": "2025-11-18T00:30:05Z",
                "completed_at": None
            }
        }
    )


class BackgroundJobListResponse(BaseModel):
    """Schema for listing multiple background jobs."""
    jobs: list[BackgroundJobResponse] = Field(..., description="List of background jobs")
    total: int = Field(..., description="Total number of jobs")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "jobs": [
                    {
                        "id": 1,
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": 1,
                        "job_type": "embedding_regeneration",
                        "status": "completed",
                        "progress_percent": 100,
                        "total_items": 150,
                        "processed_items": 149,
                        "failed_items": 1,
                        "result_data": {"embeddings_generated": 149},
                        "error_message": None,
                        "created_at": "2025-11-18T00:30:00Z",
                        "started_at": "2025-11-18T00:30:05Z",
                        "completed_at": "2025-11-18T00:32:45Z"
                    }
                ],
                "total": 1
            }
        }
    )


class BackgroundJobStatusResponse(BaseModel):
    """Simple status response for job queries."""
    job_id: UUID = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    progress_percent: int = Field(0, description="Progress percentage (0-100)")
    message: str = Field(..., description="Human-readable status message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "progress_percent": 67,
                "message": "Processing embeddings: 100/150 completed, 1 failed"
            }
        }
    )
