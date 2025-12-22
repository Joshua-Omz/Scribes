"""
Unit tests for TokenizerService.

Tests token counting, truncation, and chunking functionality.
"""

import pytest
from app.services.tokenizer_service import TokenizerService, get_tokenizer_service


class TestTokenizerService:
    """Test suite for TokenizerService."""
    
    @pytest.fixture
    def tokenizer_service(self):
        """Fixture providing tokenizer service instance."""
        return get_tokenizer_service()
    
    def test_count_tokens_basic(self, tokenizer_service):
        """Test basic token counting."""
        text = "Hello, world!"
        count = tokenizer_service.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)
    
    def test_count_tokens_empty(self, tokenizer_service):
        """Test token counting with empty string."""
        assert tokenizer_service.count_tokens("") == 0
        assert tokenizer_service.count_tokens(None) == 0
    
    def test_encode_decode_roundtrip(self, tokenizer_service):
        """Test encoding and decoding roundtrip."""
        text = "This is a test sermon note about faith."
        tokens = tokenizer_service.encode(text)
        decoded = tokenizer_service.decode(tokens)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert decoded.strip() == text.strip()
    
    def test_truncate_to_tokens(self, tokenizer_service):
        """Test truncation to token limit."""
        long_text = "This is a very long sermon note. " * 100
        max_tokens = 50
        
        truncated = tokenizer_service.truncate_to_tokens(long_text, max_tokens)
        truncated_count = tokenizer_service.count_tokens(truncated)
        
        assert truncated_count <= max_tokens
        assert len(truncated) < len(long_text)
    
    def test_truncate_already_short(self, tokenizer_service):
        """Test truncation when text already fits."""
        short_text = "Short note."
        truncated = tokenizer_service.truncate_to_tokens(short_text, 100)
        
        assert truncated == short_text
    
    def test_chunk_text_basic(self, tokenizer_service):
        """Test basic text chunking."""
        long_text = "This is a sermon about faith. " * 50
        chunks = tokenizer_service.chunk_text(long_text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 1
        for chunk in chunks:
            token_count = tokenizer_service.count_tokens(chunk)
            assert token_count <= 100
    
    def test_chunk_text_short_input(self, tokenizer_service):
        """Test chunking with text shorter than chunk_size."""
        short_text = "Brief note."
        chunks = tokenizer_service.chunk_text(short_text, chunk_size=100, overlap=20)
        
        assert len(chunks) == 1
        assert chunks[0] == short_text
    
    def test_chunk_text_overlap(self, tokenizer_service):
        """Test that chunks have proper overlap."""
        text = "Word " * 200  # Repetitive text for easy overlap detection
        chunks = tokenizer_service.chunk_text(text, chunk_size=50, overlap=10)
        
        # Verify we have multiple chunks
        assert len(chunks) > 2
        
        # TODO: Verify overlap content (requires more sophisticated comparison)
    
    def test_estimate_tokens(self, tokenizer_service):
        """Test fast token estimation."""
        text = "This is a test note."
        estimate = tokenizer_service.estimate_tokens(text)
        actual = tokenizer_service.count_tokens(text)
        
        # Estimate should be in ballpark (within 50% margin)
        assert abs(estimate - actual) < actual * 0.5
    
    def test_singleton_pattern(self):
        """Test that get_tokenizer_service returns same instance."""
        service1 = get_tokenizer_service()
        service2 = get_tokenizer_service()
        
        assert service1 is service2

