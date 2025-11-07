"""
Note-related Pydantic schemas for request/response validation.
"""

from typing import Optional, List
from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class NoteBase(BaseSchema):
    """Base note schema with common fields."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Note title",
        examples=["Sunday Sermon - Grace and Mercy"]
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Note content (supports markdown)",
        examples=["# Main Points\n\n1. Grace is unmerited favor...\n2. Mercy is..."]
    )
    preacher: Optional[str] = Field(
        None,
        max_length=100,
        description="Name of the preacher (optional)",
        examples=["Pastor John Smith"]
    )
    tags: Optional[str] = Field(
        None,
        max_length=255,
        description="Comma-separated tags",
        examples=["grace, mercy, salvation"]
    )
    scripture_refs: Optional[str] = Field(
        None,
        max_length=255,
        description="Scripture references (comma-separated)",
        examples=["John 3:16, Romans 5:8, Ephesians 2:8-9"]
    )


class NoteCreate(NoteBase):
    """Schema for creating a note."""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Sunday Sermon - Grace and Mercy",
                    "content": "# Main Points\n\n1. Grace is unmerited favor from God\n2. Mercy is not receiving the punishment we deserve",
                    "preacher": "Pastor John Smith",
                    "tags": "grace, mercy, salvation",
                    "scripture_refs": "John 3:16, Romans 5:8, Ephesians 2:8-9"
                }
            ]
        }
    }


class NoteUpdate(BaseSchema):
    """
    Schema for partially updating a note (PATCH semantics).
    
    All fields are optional. Only provide the fields you want to change.
    Omitted fields will remain unchanged in the database.
    
    Example - Update only the title:
        {"title": "New Title"}
    
    Example - Update title and tags:
        {"title": "New Title", "tags": "faith, hope"}
    """
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated title",
        examples=["Updated Note Title"]
    )
    content: Optional[str] = Field(
        None,
        min_length=1,
        description="Updated content",
        examples=["# Updated Content\n\nNew information..."]
    )
    preacher: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated preacher name",
        examples=["Pastor Jane Doe"]
    )
    tags: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated tags",
        examples=["faith, hope, love"]
    )
    scripture_refs: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated scripture references",
        examples=["Matthew 5:1-12, Luke 6:20-26"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Updated Note Title",
                    "content": "Updated note content...",
                    "tags": "faith, hope, love"
                }
            ]
        }
    }


class NoteResponse(NoteBase, TimestampSchema):
    """Schema for note response."""
    
    id: int
    user_id: int = Field(..., description="User who created the note")
    
    model_config = BaseSchema.model_config


class NoteDetailResponse(NoteResponse):
    """Schema for detailed note response with relationships."""
    
    reminders_count: Optional[int] = Field(0, description="Number of reminders for this note")
    annotations_count: Optional[int] = Field(0, description="Number of annotations on this note")
    cross_refs_count: Optional[int] = Field(0, description="Number of cross-references")
    shared_circles_count: Optional[int] = Field(0, description="Number of circles this note is shared in")
    
    model_config = BaseSchema.model_config


class NoteListResponse(BaseSchema):
    """Schema for paginated list of notes."""
    
    items: List[NoteResponse]
    total: int
    page: int
    page_size: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 50,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


class NoteSearchRequest(BaseSchema):
    """Schema for note search request."""
    
    query: Optional[str] = Field(
        None,
        min_length=1,
        description="Search query string",
        examples=["grace salvation"]
    )
    tags: Optional[str] = Field(
        None,
        description="Filter by tags (comma-separated)",
        examples=["grace, mercy"]
    )
    preacher: Optional[str] = Field(
        None,
        description="Filter by preacher name",
        examples=["Pastor John"]
    )
    scripture_ref: Optional[str] = Field(
        None,
        description="Filter by scripture reference",
        examples=["John 3:16"]
    )
    date_from: Optional[str] = Field(
        None,
        description="Filter notes from this date (ISO format)",
        examples=["2025-01-01"]
    )
    date_to: Optional[str] = Field(
        None,
        description="Filter notes up to this date (ISO format)",
        examples=["2025-12-31"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "grace salvation",
                    "tags": "grace, mercy",
                    "date_from": "2025-01-01"
                }
            ]
        }
    }
