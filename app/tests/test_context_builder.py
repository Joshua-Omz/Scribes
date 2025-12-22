"""
Unit tests for ContextBuilder.
"""

import pytest
from app.services.ai.context_builder import ContextBuilder, get_context_builder


class TestContextBuilder:
    """Test suite for ContextBuilder."""
    
    def test_initialization(self):
        """Test service initializes correctly."""
        builder = ContextBuilder()
        
        assert builder.default_budget == 1200  # Updated value
        assert builder.tokenizer is not None
    
    def test_singleton_pattern(self):
        """Test that get_context_builder returns same instance."""
        builder1 = get_context_builder()
        builder2 = get_context_builder()
        
        assert builder1 is builder2
    
    def test_build_context_basic(self):
        """Test basic context building with high-relevance chunks."""
        builder = ContextBuilder()
        
        # Mock high-relevance chunks
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": "Faith is the assurance of things hoped for.",
                "relevance_score": 0.95,
                "note_title": "Sermon on Faith",
                "preacher": "Pastor John",
                "scripture_refs": "Hebrews 11:1"
            },
            {
                "chunk_id": 2,
                "note_id": 100,
                "chunk_idx": 1,
                "chunk_text": "Without faith it is impossible to please God.",
                "relevance_score": 0.88,
                "note_title": "Sermon on Faith",
                "preacher": "Pastor John",
                "scripture_refs": "Hebrews 11:6"
            }
        ]
        
        low_rel = []
        
        result = builder.build_context(high_rel, low_rel, token_budget=1000)
        
        # Assertions
        assert result["context_text"] != ""
        assert len(result["chunks_used"]) <= 2
        assert result["total_tokens"] <= 1000
        assert result["token_budget"] == 1000
        assert len(result["sources"]) == 1  # Both chunks from same note
        assert result["sources"][0]["note_id"] == 100
        assert result["sources"][0]["chunk_count"] == len(result["chunks_used"])
        assert isinstance(result["truncated"], bool)
    
    def test_empty_chunks(self):
        """Test handling of empty chunk list."""
        builder = ContextBuilder()
        
        result = builder.build_context([], [], token_budget=1000)
        
        assert result["context_text"] == ""
        assert result["chunks_used"] == []
        assert result["total_tokens"] == 0
        assert result["truncated"] is False
        assert result["sources"] == []
    
    def test_budget_exceeded(self):
        """Test that chunks are skipped when budget exceeded."""
        builder = ContextBuilder()
        
        # Create a chunk with lots of text
        long_text = "Faith and hope and love. " * 100  # ~500 words
        
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": long_text,
                "relevance_score": 0.95,
                "note_title": "Long Sermon",
                "preacher": "Pastor John",
                "scripture_refs": "1 Cor 13"
            },
            {
                "chunk_id": 2,
                "note_id": 101,
                "chunk_idx": 0,
                "chunk_text": long_text,
                "relevance_score": 0.90,
                "note_title": "Another Sermon",
                "preacher": "Pastor Jane",
                "scripture_refs": "Rom 8"
            }
        ]
        
        # Very small budget - should only fit 1 chunk
        result = builder.build_context(high_rel, [], token_budget=300)
        
        assert len(result["chunks_used"]) < len(high_rel)  # Not all chunks fit
        assert result["truncated"] is True
        assert len(result["chunks_skipped"]) > 0
        assert result["total_tokens"] <= 300
    
    def test_chunk_sorting_by_relevance(self):
        """Test that chunks are sorted by relevance score."""
        builder = ContextBuilder()
        
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": "Lower relevance chunk.",
                "relevance_score": 0.70,
                "note_title": "Note 1",
                "preacher": None,
                "scripture_refs": None
            },
            {
                "chunk_id": 2,
                "note_id": 101,
                "chunk_idx": 0,
                "chunk_text": "Higher relevance chunk.",
                "relevance_score": 0.95,
                "note_title": "Note 2",
                "preacher": None,
                "scripture_refs": None
            },
            {
                "chunk_id": 3,
                "note_id": 102,
                "chunk_idx": 0,
                "chunk_text": "Medium relevance chunk.",
                "relevance_score": 0.85,
                "note_title": "Note 3",
                "preacher": None,
                "scripture_refs": None
            }
        ]
        
        result = builder.build_context(high_rel, [], token_budget=1000)
        
        # First chunk used should be highest relevance
        if result["chunks_used"]:
            assert result["chunks_used"][0]["relevance_score"] == 0.95
    
    def test_chunk_formatting(self):
        """Test that chunks are formatted correctly."""
        builder = ContextBuilder()
        
        chunk = {
            "chunk_id": 1,
            "note_id": 100,
            "chunk_idx": 0,
            "chunk_text": "Test content",
            "relevance_score": 0.85,
            "note_title": "Test Note",
            "preacher": "Test Preacher",
            "scripture_refs": "John 3:16"
        }
        
        formatted = builder._format_chunk(chunk)
        
        assert "Test Note" in formatted
        assert "Test Preacher" in formatted
        assert "John 3:16" in formatted
        assert "0.85" in formatted  # Relevance score
        assert "Test content" in formatted
        assert "---" in formatted  # Separator
        assert "Source:" in formatted
        assert "Relevance:" in formatted
        assert "Content:" in formatted
    
    def test_chunk_formatting_without_optional_fields(self):
        """Test chunk formatting when preacher/scripture are None."""
        builder = ContextBuilder()
        
        chunk = {
            "chunk_id": 1,
            "note_id": 100,
            "chunk_idx": 0,
            "chunk_text": "Test content",
            "relevance_score": 0.85,
            "note_title": "Test Note",
            "preacher": None,
            "scripture_refs": None
        }
        
        formatted = builder._format_chunk(chunk)
        
        assert "Test Note" in formatted
        assert "Test content" in formatted
        # Should not crash with None values
        assert "---" in formatted
    
    def test_source_extraction(self):
        """Test extracting unique sources from chunks."""
        builder = ContextBuilder()
        
        chunks = [
            {"note_id": 100, "note_title": "Note A", "chunk_idx": 0, "preacher": "John", "scripture_refs": "Gen 1", "tags": "creation"},
            {"note_id": 100, "note_title": "Note A", "chunk_idx": 1, "preacher": "John", "scripture_refs": "Gen 1", "tags": "creation"},
            {"note_id": 200, "note_title": "Note B", "chunk_idx": 0, "preacher": "Jane", "scripture_refs": "Rom 8", "tags": "faith"},
        ]
        
        sources = builder._extract_sources(chunks)
        
        assert len(sources) == 2  # Two unique notes
        assert sources[0]["note_id"] == 100  # Most-cited first
        assert sources[0]["chunk_count"] == 2
        assert sources[0]["chunk_indices"] == [0, 1]
        assert sources[1]["note_id"] == 200
        assert sources[1]["chunk_count"] == 1
        assert sources[1]["chunk_indices"] == [0]
    
    def test_low_relevance_preservation(self):
        """Test that low-relevance chunks are preserved in metadata."""
        builder = ContextBuilder()
        
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": "High relevance content",
                "relevance_score": 0.90,
                "note_title": "High Note",
                "preacher": None,
                "scripture_refs": None
            }
        ]
        
        low_rel = [
            {
                "chunk_id": 2,
                "note_id": 200,
                "chunk_idx": 0,
                "chunk_text": "Low relevance content",
                "relevance_score": 0.45,
                "note_title": "Low Note",
                "preacher": None,
                "scripture_refs": None
            },
            {
                "chunk_id": 3,
                "note_id": 201,
                "chunk_idx": 0,
                "chunk_text": "Another low relevance",
                "relevance_score": 0.30,
                "note_title": "Another Low",
                "preacher": None,
                "scripture_refs": None
            }
        ]
        
        result = builder.build_context(high_rel, low_rel, token_budget=1000)
        
        assert len(result["low_relevance_chunks"]) == 2
        assert result["low_relevance_chunks"] == low_rel
    
    def test_preview_context(self):
        """Test preview functionality."""
        builder = ContextBuilder()
        
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": "First chunk",
                "relevance_score": 0.95,
                "note_title": "Note 1",
                "preacher": "Pastor A",
                "scripture_refs": "Gen 1"
            },
            {
                "chunk_id": 2,
                "note_id": 101,
                "chunk_idx": 0,
                "chunk_text": "Second chunk",
                "relevance_score": 0.85,
                "note_title": "Note 2",
                "preacher": "Pastor B",
                "scripture_refs": "John 1"
            },
            {
                "chunk_id": 3,
                "note_id": 102,
                "chunk_idx": 0,
                "chunk_text": "Third chunk",
                "relevance_score": 0.75,
                "note_title": "Note 3",
                "preacher": "Pastor C",
                "scripture_refs": "Rom 1"
            }
        ]
        
        preview = builder.preview_context(high_rel, max_chunks=2)
        
        assert "[Chunk 1]" in preview
        assert "[Chunk 2]" in preview
        assert "... and 1 more chunks" in preview
        assert "First chunk" in preview
        assert "Second chunk" in preview
    
    def test_default_token_budget(self):
        """Test that default token budget is used when not specified."""
        builder = ContextBuilder()
        
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": "Test content",
                "relevance_score": 0.90,
                "note_title": "Test",
                "preacher": None,
                "scripture_refs": None
            }
        ]
        
        # Don't specify token_budget
        result = builder.build_context(high_rel, [])
        
        assert result["token_budget"] == 1200  # Default from config
    
    def test_multiple_notes_source_diversity(self):
        """Test that sources from multiple notes are extracted correctly."""
        builder = ContextBuilder()
        
        high_rel = [
            {
                "chunk_id": 1,
                "note_id": 100,
                "chunk_idx": 0,
                "chunk_text": "Content A1",
                "relevance_score": 0.95,
                "note_title": "Note A",
                "preacher": "Pastor 1",
                "scripture_refs": "Gen 1",
                "tags": "creation"
            },
            {
                "chunk_id": 2,
                "note_id": 200,
                "chunk_idx": 0,
                "chunk_text": "Content B1",
                "relevance_score": 0.90,
                "note_title": "Note B",
                "preacher": "Pastor 2",
                "scripture_refs": "John 1",
                "tags": "gospel"
            },
            {
                "chunk_id": 3,
                "note_id": 100,
                "chunk_idx": 1,
                "chunk_text": "Content A2",
                "relevance_score": 0.85,
                "note_title": "Note A",
                "preacher": "Pastor 1",
                "scripture_refs": "Gen 1",
                "tags": "creation"
            }
        ]
        
        result = builder.build_context(high_rel, [], token_budget=2000)
        
        # Should have 2 unique sources
        assert len(result["sources"]) == 2
        
        # Note A should be first (2 chunks)
        assert result["sources"][0]["note_id"] == 100
        assert result["sources"][0]["chunk_count"] == 2
        
        # Note B should be second (1 chunk)
        assert result["sources"][1]["note_id"] == 200
        assert result["sources"][1]["chunk_count"] == 1
