"""
Unit tests for RetrievalService.
"""

import pytest
from app.services.retrieval_service import RetrievalService


class TestRetrievalService:
    """Test suite for RetrievalService."""
    
    def test_initialization(self):
        """Test service initializes with correct threshold."""
        service = RetrievalService()
        
        assert service.relevance_threshold == 0.6
        assert service is not None
    
    def test_set_relevance_threshold(self):
        """Test updating relevance threshold."""
        service = RetrievalService()
        
        # Valid threshold
        service.set_relevance_threshold(0.7)
        assert service.relevance_threshold == 0.7
        
        # Invalid threshold (should raise error)
        with pytest.raises(ValueError):
            service.set_relevance_threshold(1.5)  # > 1.0
        
        with pytest.raises(ValueError):
            service.set_relevance_threshold(-0.1)  # < 0.0
    
    @pytest.mark.asyncio
    async def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        service = RetrievalService()
        
        # Mock database session (we won't actually query)
        db = None  # We expect ValueError before DB is used
        
        # Invalid embedding dimension
        with pytest.raises(ValueError, match="Invalid query_embedding"):
            await service.retrieve_top_chunks(
                db=db,
                query_embedding=[0.1] * 100,  # Wrong dimension (not 384)
                user_id=1,
                top_k=50
            )
        
        # Invalid user_id
        with pytest.raises(ValueError, match="Invalid user_id"):
            await service.retrieve_top_chunks(
                db=db,
                query_embedding=[0.1] * 384,
                user_id=-1,  # Negative user_id
                top_k=50
            )
        
        # Invalid top_k
        with pytest.raises(ValueError, match="Invalid top_k"):
            await service.retrieve_top_chunks(
                db=db,
                query_embedding=[0.1] * 384,
                user_id=1,
                top_k=500  # Too large
            )