"""
Export job-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class ExportJobBase(BaseSchema):
    """Base export job schema with common fields."""
    
    export_format: str = Field(
        ...,
        description="Export format: pdf, markdown, docx, html",
        examples=["pdf"]
    )
    export_type: str = Field(
        ...,
        description="Export type: single_note, multiple_notes, all_notes, circle_notes",
        examples=["single_note"]
    )


class ExportJobCreate(ExportJobBase):
    """Schema for creating export job."""
    
    note_id: Optional[int] = Field(
        None,
        description="Note ID (for single_note export type)",
        examples=[1]
    )
    note_ids: Optional[List[int]] = Field(
        None,
        description="List of note IDs (for multiple_notes export type)",
        examples=[[1, 2, 3]]
    )
    circle_id: Optional[int] = Field(
        None,
        description="Circle ID (for circle_notes export type)",
        examples=[1]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "export_format": "pdf",
                    "export_type": "single_note",
                    "note_id": 1
                },
                {
                    "export_format": "markdown",
                    "export_type": "multiple_notes",
                    "note_ids": [1, 2, 3]
                }
            ]
        }
    }


class ExportJobResponse(ExportJobBase, TimestampSchema):
    """Schema for export job response."""
    
    id: int
    user_id: int = Field(..., description="User who requested the export")
    note_id: Optional[int] = Field(None, description="Note ID (if single note export)")
    status: str = Field(
        ...,
        description="Job status: pending, processing, completed, failed",
        examples=["pending"]
    )
    file_path: Optional[str] = Field(None, description="Path to exported file")
    file_url: Optional[str] = Field(None, description="URL to download file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    model_config = BaseSchema.model_config


class ExportJobListResponse(BaseSchema):
    """Schema for list of export jobs with pagination."""
    
    items: List[ExportJobResponse]
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
