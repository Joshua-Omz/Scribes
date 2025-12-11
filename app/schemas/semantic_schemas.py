"""
Pydantic schemas for semantic search endpoints.
Keeps request/response models organized and reusable.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.note_schemas import NoteResponse


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=1000, 
        description="Search query text",
        examples=["faith and salvation", "grace in difficult times"]
    )
    limit: int = Field(
        default=10, 
        ge=1, 
        le=100, 
        description="Maximum number of results to return"
    )
    offset: int = Field(
        default=0, 
        ge=0, 
        description="Number of results to skip (for pagination)"
    )
    min_similarity: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity score threshold (0-1, higher = more similar)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "sermons about faith during trials",
                "limit": 20,
                "offset": 0,
                "min_similarity": 0.6
            }
        }


class SemanticSearchResult(BaseModel):
    """Single search result with similarity score."""
    note: NoteResponse
    similarity_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Cosine similarity score (0-1, higher = more similar)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "note": {
                    "id": 123,
                    "title": "Faith in Hard Times",
                    "content": "...",
                    "preacher": "John Doe",
                    "tags": "faith,trials,perseverance",
                    "created_at": "2025-01-15T10:30:00Z"
                },
                "similarity_score": 0.87
            }
        }


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    results: List[SemanticSearchResult] = Field(
        default_factory=list,
        description="List of matching notes with similarity scores"
    )
    query: str = Field(..., description="The search query that was executed")
    total_results: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Offset used for pagination")
    limit: int = Field(..., description="Limit used for pagination")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "note": {
                            "id": 123,
                            "title": "Faith in Hard Times",
                            "content": "...",
                        },
                        "similarity_score": 0.87
                    }
                ],
                "query": "faith during trials",
                "total_results": 1,
                "offset": 0,
                "limit": 10
            }
        }


class EmbeddingStatusResponse(BaseModel):
    """Response for embedding coverage status check."""
    total_notes: int = Field(..., description="Total number of notes for the user")
    notes_with_embeddings: int = Field(..., description="Number of notes that have embeddings")
    notes_without_embeddings: int = Field(..., description="Number of notes missing embeddings")
    coverage_percentage: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Percentage of notes with embeddings"
    )
    model_info: dict = Field(..., description="Information about the embedding model in use")

    class Config:
        json_schema_extra = {
            "example": {
                "total_notes": 1523,
                "notes_with_embeddings": 1498,
                "notes_without_embeddings": 25,
                "coverage_percentage": 98.36,
                "model_info": {
                    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "target_dimension": 1536,
                    "padding_used": True
                }
            }
        }


class RegenerationStatusResponse(BaseModel):
    """Response for background embedding regeneration status."""
    message: str = Field(..., description="Status message")
    status: str = Field(..., description="Task status (queued, processing, completed, failed)")
    task_id: Optional[str] = Field(
        None, 
        description="Task ID for tracking (if using task queue like Celery)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Embedding regeneration has been queued and will process in the background",
                "status": "queued",
                "task_id": None
            }
        }
