"""
Unit tests for ChunkingService.

Tests note chunking with token awareness.
"""

import pytest
from app.services.chunking_service import ChunkingService, get_chunking_service


class TestChunkingService:
    """Test suite for ChunkingService."""
    
    @pytest.fixture
    def chunking_service(self):
        """Fixture providing chunking service instance."""
        return get_chunking_service()
    
    def test_chunk_note_basic(self, chunking_service):
        """Test basic note chunking."""
        note_content = "This is a sermon about faith and grace. " * 50
        chunks = chunking_service.chunk_note(note_content)
        
        assert len(chunks) > 0
        assert all("chunk_idx" in c for c in chunks)
        assert all("chunk_text" in c for c in chunks)
        assert all("token_count" in c for c in chunks)
        
        # Verify chunks are in order
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_idx"] == i
    
    def test_chunk_note_with_metadata(self, chunking_service):
        """Test chunking with metadata attachment."""
        note_content = "Sermon note content."
        metadata = {"note_id": 123, "title": "Faith"}
        
        chunks = chunking_service.chunk_note(note_content, metadata=metadata)
        
        assert all("metadata" in c for c in chunks)
        assert all(c["metadata"]["note_id"] == 123 for c in chunks)
    
    def test_chunk_note_empty_content(self, chunking_service):
        """Test chunking empty note."""
        chunks = chunking_service.chunk_note("")
        assert chunks == []
        
        chunks = chunking_service.chunk_note("   ")
        assert chunks == []
    
    def test_chunk_note_custom_size(self, chunking_service):
        """Test chunking with custom chunk size."""
        note_content = "Word " * 500
        chunk_size = 50
        
        chunks = chunking_service.chunk_note(note_content, chunk_size=chunk_size)
        
        for chunk in chunks:
            assert chunk["token_count"] <= chunk_size
    
    def test_chunk_notes_batch(self, chunking_service):
        """Test batch chunking multiple notes."""
        notes = [
            {"id": 1, "content": "Note 1 content " * 50, "title": "Faith"},
            {"id": 2, "content": "Note 2 content " * 50, "title": "Hope"},
            {"id": 3, "content": "Note 3 content " * 50, "title": "Love"},
        ]
        
        all_chunks = chunking_service.chunk_notes_batch(notes)
        
        assert len(all_chunks) > len(notes)  # Each note produces multiple chunks
        
        # Verify all chunks have metadata with note_id
        note_ids = {c["metadata"]["note_id"] for c in all_chunks}
        assert note_ids == {1, 2, 3}
    
    def test_chunk_notes_batch_skip_empty(self, chunking_service):
        """Test batch chunking skips empty notes."""
        notes = [
            {"id": 1, "content": "Valid content", "title": "Test"},
            {"id": 2, "content": "", "title": "Empty"},
            {"id": 3, "content": "   ", "title": "Whitespace"},
        ]
        
        all_chunks = chunking_service.chunk_notes_batch(notes)
        
        # Only note 1 should produce chunks
        assert all(c["metadata"]["note_id"] == 1 for c in all_chunks)
    
    def test_should_chunk(self, chunking_service):
        """Test chunk necessity detection."""
        short_note = "Brief sermon note."
        long_note = "Very long sermon note. " * 500
        
        assert not chunking_service.should_chunk(short_note)
        assert chunking_service.should_chunk(long_note)
    
    def test_estimate_chunk_count(self, chunking_service):
        """Test chunk count estimation."""
        note_content = "This is content. " * 200
        estimate = chunking_service.estimate_chunk_count(note_content)
        
        actual_chunks = chunking_service.chunk_note(note_content)
        
        # Estimate should be close to actual
        assert abs(estimate - len(actual_chunks)) <= 2
    
    def test_invalid_chunk_parameters(self, chunking_service):
        """Test error handling for invalid chunk parameters."""
        with pytest.raises(ValueError):
            # overlap >= chunk_size should raise error
            chunking_service.chunk_note("Content", chunk_size=50, overlap=60)
    
    def test_singleton_pattern(self):
        """Test that get_chunking_service returns same instance."""
        service1 = get_chunking_service()
        service2 = get_chunking_service()
        
        assert service1 is service2

