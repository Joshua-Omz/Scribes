"""
Pydantic schemas for the AI Assistant feature.

Defines request/response models for assistant queries, chunks, and context.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ChunkMetadata(BaseModel):
    """
    Metadata about a retrieved chunk.
    
    Used for tracking chunk provenance and relevance scoring.
    """
    note_id: int = Field(..., description="ID of the parent note")
    chunk_idx: int = Field(..., description="Index of chunk within note (0-based)")
    relevance_score: float = Field(..., description="Cosine similarity score (0-1, higher is better)")
    token_count: int = Field(..., description="Number of tokens in chunk")
    
    # Optional note metadata for context
    note_title: Optional[str] = Field(None, description="Title of source note")
    preacher: Optional[str] = Field(None, description="Preacher name from note")
    scripture_refs: Optional[str] = Field(None, description="Scripture references")
    created_at: Optional[datetime] = Field(None, description="When note was created")
    
    model_config = ConfigDict(from_attributes=True)


class ContextMetadata(BaseModel):
    """
    Metadata about the context used for generation.
    
    Tracks what was retrieved and how tokens were allocated.
    """
    total_chunks_retrieved: int = Field(..., description="Total chunks from vector search")
    chunks_used: int = Field(..., description="Chunks actually included in context")
    total_tokens_used: int = Field(..., description="Actual tokens used for context")
    token_budget: int = Field(..., description="Maximum tokens allowed for context")
    truncated: bool = Field(default=False, description="Whether context was truncated")
    compression_applied: bool = Field(default=False, description="Whether compression was used")
    
    model_config = ConfigDict(from_attributes=True)


class SourceCitation(BaseModel):
    """
    Citation for a source note used in the answer.
    """
    note_id: int = Field(..., description="ID of source note")
    note_title: Optional[str] = Field(None, description="Title of source note")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    chunk_indices: List[int] = Field(..., description="Which chunks were used from this note")
    
    model_config = ConfigDict(from_attributes=True)


class AssistantQueryRequest(BaseModel):
    """
    Request schema for assistant query.
    
    Example:
        {
            "query": "What did the pastor say about faith?",
            "max_sources": 5,
            "include_metadata": true
        }
    """
    query: str = Field(
        ...,
        description="User's question or prompt",
        min_length=1,
        max_length=500,
        json_schema_extra={"example": "What did the pastor say about faith?"}
    )
    max_sources: int = Field(
        default=5,
        description="Maximum number of source notes to cite",
        ge=1,
        le=20
    )
    include_metadata: bool = Field(
        default=True,
        description="Include context metadata in response"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the main points about grace in my sermon notes?",
                "max_sources": 5,
                "include_metadata": True
            }
        }
    )


class AssistantResponse(BaseModel):
    """
    Response schema for assistant query.
    
    Contains the generated answer, source citations, and metadata.
    """
    answer: str = Field(..., description="Generated answer from the assistant")
    sources: List[SourceCitation] = Field(..., description="Source notes used for answer")
    
    # Optional metadata (returned if include_metadata=True)
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about context and token usage"
    )
    
    # Performance metrics
    query_tokens: int = Field(..., description="Tokens in user query")
    answer_tokens: int = Field(..., description="Tokens in generated answer")
    latency_ms: int = Field(..., description="Total query latency in milliseconds")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Based on your notes, the main themes about faith include...",
                "sources": [
                    {
                        "note_id": 123,
                        "note_title": "Sermon on Faith - Matthew 17",
                        "relevance_score": 0.89,
                        "chunk_indices": [0, 2]
                    }
                ],
                "context_metadata": {
                    "total_chunks_retrieved": 50,
                    "chunks_used": 8,
                    "total_tokens_used": 1650,
                    "token_budget": 1800,
                    "truncated": False,
                    "compression_applied": False
                },
                "query_tokens": 12,
                "answer_tokens": 247,
                "latency_ms": 1850,
                "timestamp": "2025-11-23T10:30:00Z"
            }
        }
    )


class AssistantError(BaseModel):
    """Error response for assistant queries."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "CONTEXT_RETRIEVAL_FAILED",
                "message": "No relevant notes found for your query",
                "details": {"query_tokens": 15, "retrieved_chunks": 0}
            }
        }
    )


# NoteChunk schema (for API responses involving chunks)
class NoteChunkResponse(BaseModel):
    """Response schema for note chunk."""
    id: int = Field(..., description="Chunk database ID")
    note_id: int = Field(..., description="Parent note ID")
    chunk_idx: int = Field(..., description="Chunk index within note")
    chunk_text: str = Field(..., description="Chunk text content")
    token_count_estimate: int = Field(..., description="Estimated token count")
    created_at: datetime = Field(..., description="When chunk was created")
    
    model_config = ConfigDict(from_attributes=True)

