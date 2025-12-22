"""
Unit tests for assistant schemas.

Tests Pydantic schema validation and serialization.
"""

import pytest
from datetime import datetime
from app.schemas.assistant_schemas import (
    AssistantQueryRequest,
    AssistantResponse,
    ChunkMetadata,
    ContextMetadata,
    SourceCitation,
    AssistantError
)


class TestAssistantSchemas:
    """Test suite for assistant Pydantic schemas."""
    
    def test_assistant_query_request_valid(self):
        """Test valid query request."""
        request = AssistantQueryRequest(
            query="What did the pastor say about faith?",
            max_sources=5,
            include_metadata=True
        )
        
        assert request.query == "What did the pastor say about faith?"
        assert request.max_sources == 5
        assert request.include_metadata is True
    
    def test_assistant_query_request_defaults(self):
        """Test query request with defaults."""
        request = AssistantQueryRequest(query="Test query")
        
        assert request.max_sources == 5  # default
        assert request.include_metadata is True  # default
    
    def test_assistant_query_request_validation(self):
        """Test query request validation."""
        # Empty query should fail
        with pytest.raises(ValueError):
            AssistantQueryRequest(query="")
        
        # Query too long should fail
        with pytest.raises(ValueError):
            AssistantQueryRequest(query="x" * 1000)
        
        # max_sources out of range
        with pytest.raises(ValueError):
            AssistantQueryRequest(query="Test", max_sources=0)
        
        with pytest.raises(ValueError):
            AssistantQueryRequest(query="Test", max_sources=100)
    
    def test_chunk_metadata(self):
        """Test ChunkMetadata schema."""
        metadata = ChunkMetadata(
            note_id=123,
            chunk_idx=0,
            relevance_score=0.89,
            token_count=256,
            note_title="Sermon on Faith",
            preacher="Pastor John",
            scripture_refs="Matthew 17:20",
            created_at=datetime.utcnow()
        )
        
        assert metadata.note_id == 123
        assert metadata.chunk_idx == 0
        assert 0 <= metadata.relevance_score <= 1
        assert metadata.token_count == 256
    
    def test_context_metadata(self):
        """Test ContextMetadata schema."""
        metadata = ContextMetadata(
            total_chunks_retrieved=50,
            chunks_used=8,
            total_tokens_used=1650,
            token_budget=1800,
            truncated=False,
            compression_applied=False
        )
        
        assert metadata.total_chunks_retrieved == 50
        assert metadata.chunks_used == 8
        assert metadata.total_tokens_used <= metadata.token_budget
    
    def test_source_citation(self):
        """Test SourceCitation schema."""
        citation = SourceCitation(
            note_id=123,
            note_title="Sermon on Faith",
            relevance_score=0.89,
            chunk_indices=[0, 2, 5]
        )
        
        assert citation.note_id == 123
        assert len(citation.chunk_indices) == 3
        assert 0 <= citation.relevance_score <= 1
    
    def test_assistant_response_complete(self):
        """Test complete AssistantResponse."""
        response = AssistantResponse(
            answer="Based on your notes, faith is...",
            sources=[
                SourceCitation(
                    note_id=123,
                    note_title="Faith Sermon",
                    relevance_score=0.89,
                    chunk_indices=[0, 1]
                )
            ],
            context_metadata=ContextMetadata(
                total_chunks_retrieved=50,
                chunks_used=8,
                total_tokens_used=1650,
                token_budget=1800
            ),
            query_tokens=12,
            answer_tokens=247,
            latency_ms=1850
        )
        
        assert len(response.answer) > 0
        assert len(response.sources) == 1
        assert response.latency_ms > 0
        assert isinstance(response.timestamp, datetime)
    
    def test_assistant_error(self):
        """Test AssistantError schema."""
        error = AssistantError(
            error="CONTEXT_RETRIEVAL_FAILED",
            message="No relevant notes found",
            details={"query_tokens": 15}
        )
        
        assert error.error == "CONTEXT_RETRIEVAL_FAILED"
        assert error.details["query_tokens"] == 15
    
    def test_schema_json_serialization(self):
        """Test that schemas can be serialized to JSON."""
        request = AssistantQueryRequest(query="Test")
        json_data = request.model_dump_json()
        
        assert isinstance(json_data, str)
        assert "Test" in json_data

