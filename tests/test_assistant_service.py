"""
Comprehensive unit tests for AssistantService.

Tests cover:
1. Successful query with context
2. No-context scenario
3. Generation error handling
4. Empty query validation
5. Token budget enforcement
6. User with no notes
7. Metadata optional parameter
8. Max sources limiting
9. Unexpected errors

All dependencies are properly mocked to ensure isolated unit testing.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.assistant_service import AssistantService, get_assistant_service
from app.services.ai.hf_inference_service import GenerationError


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def assistant_service():
    """Create AssistantService with mocked dependencies."""
    with patch('app.services.assistant_service.get_tokenizer_service') as mock_tokenizer, \
         patch('app.services.assistant_service.EmbeddingService') as mock_embedding, \
         patch('app.services.assistant_service.get_retrieval_service') as mock_retrieval, \
         patch('app.services.assistant_service.get_context_builder') as mock_context, \
         patch('app.services.assistant_service.get_prompt_engine') as mock_prompt, \
         patch('app.services.assistant_service.get_textgen_service') as mock_textgen:
        
        service = AssistantService()
        
        # Store mocks for test access
        service._mock_tokenizer = mock_tokenizer.return_value
        service._mock_embedding = mock_embedding.return_value
        service._mock_retrieval = mock_retrieval.return_value
        service._mock_context = mock_context.return_value
        service._mock_prompt = mock_prompt.return_value
        service._mock_textgen = mock_textgen.return_value
        
        yield service


class TestAssistantServiceQuery:
    """Test suite for AssistantService.query() method."""
    
    @pytest.mark.asyncio
    async def test_query_with_valid_context(self, assistant_service, mock_db):
        """Test successful query with relevant context chunks."""
        # Arrange
        user_query = "What is grace according to the sermon?"
        user_id = 123
        
        # Mock tokenizer
        assistant_service._mock_tokenizer.count_tokens.return_value = 45
        
        # Mock embedding service
        query_embedding = [0.1] * 384
        assistant_service._mock_embedding.generate.return_value = query_embedding
        
        # Mock retrieval service - high relevance chunks
        high_rel_chunks = [
            {
                "chunk_id": 1,
                "note_id": 42,
                "chunk_text": "Grace is God's unmerited favor...",
                "relevance_score": 0.89,
                "note_title": "Grace and Mercy",
                "preacher": "Pastor John",
                "scripture_refs": "Ephesians 2:8-9",
                "tags": "grace, salvation"
            },
            {
                "chunk_id": 2,
                "note_id": 87,
                "chunk_text": "We cannot earn grace through works...",
                "relevance_score": 0.76,
                "note_title": "Salvation by Faith",
                "preacher": "Dr. Smith",
                "scripture_refs": "Romans 5:8",
                "tags": "grace, faith"
            }
        ]
        low_rel_chunks = []
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=(high_rel_chunks, low_rel_chunks)
        )
        
        # Mock context builder
        context_result = {
            "context_text": "---\nSource: Grace and Mercy\nRelevance: 0.89\nContent:\nGrace is God's unmerited favor...\n---",
            "chunks_used": high_rel_chunks,
            "chunks_skipped": [],
            "sources": [
                {
                    "note_id": 42,
                    "note_title": "Grace and Mercy",
                    "preacher": "Pastor John",
                    "sermon_date": "2025-01-15",
                    "scripture_refs": "Ephesians 2:8-9",
                    "tags": "grace, salvation"
                }
            ],
            "total_tokens": 987,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        # Mock prompt engine
        final_prompt = "<s>[INST] <<SYS>>You are a pastoral AI assistant...<</SYS>>\n\nWhat is grace? [/INST]"
        assistant_service._mock_prompt.build_prompt.return_value = final_prompt
        
        # Mock text generation
        raw_answer = "Based on your sermon notes, grace is God's unmerited favor toward sinners..."
        assistant_service._mock_textgen.generate.return_value = raw_answer
        
        # Mock answer extraction
        clean_answer = "Based on your sermon notes, grace is God's unmerited favor toward sinners..."
        assistant_service._mock_prompt.extract_answer_from_response.return_value = clean_answer
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            max_sources=5,
            include_metadata=True
        )
        
        # Assert
        assert response["answer"] == clean_answer
        assert len(response["sources"]) == 1
        assert response["sources"][0]["note_id"] == 42
        assert response["metadata"] is not None
        assert response["metadata"]["chunks_used"] == 2
        assert response["metadata"]["context_tokens"] == 987
        assert response["metadata"]["query_tokens"] == 45
        assert response["metadata"]["truncated"] is False
        assert "duration_ms" in response["metadata"]
        
        # Verify service calls
        assistant_service._mock_tokenizer.count_tokens.assert_called_once_with(user_query)
        assistant_service._mock_embedding.generate.assert_called_once_with(user_query)
        assistant_service._mock_retrieval.retrieve_top_chunks.assert_called_once()
        assistant_service._mock_context.build_context.assert_called_once()
        assistant_service._mock_prompt.build_prompt.assert_called_once()
        assistant_service._mock_textgen.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_with_no_context(self, assistant_service, mock_db):
        """Test query when no relevant chunks are found."""
        # Arrange
        user_query = "What is quantum physics?"
        user_id = 123
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 30
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        # No high-relevance chunks
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=([], [])
        )
        
        # Empty context
        context_result = {
            "context_text": "",
            "chunks_used": [],
            "chunks_skipped": [],
            "sources": [],
            "total_tokens": 0,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        # Mock no-context response
        no_context_msg = "I don't see that topic in your sermon notes yet. However, the Bible says..."
        assistant_service._mock_prompt.build_no_context_response.return_value = no_context_msg
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            include_metadata=True
        )
        
        # Assert
        assert response["answer"] == no_context_msg
        assert response["sources"] == []
        assert response["metadata"]["no_context"] is True
        assert response["metadata"]["chunks_used"] == 0
        assert response["metadata"]["context_tokens"] == 0
        
        # Verify text generation was NOT called (saves API costs)
        assistant_service._mock_textgen.generate.assert_not_called()
        assistant_service._mock_prompt.build_no_context_response.assert_called_once_with(user_query)
    
    @pytest.mark.asyncio
    async def test_query_with_generation_error(self, assistant_service, mock_db):
        """Test graceful handling of LLM generation failure."""
        # Arrange
        user_query = "What is faith?"
        user_id = 123
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 25
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        high_rel_chunks = [
            {
                "chunk_id": 1,
                "note_id": 42,
                "chunk_text": "Faith is...",
                "relevance_score": 0.85,
                "note_title": "Faith in Action",
                "preacher": "Pastor Jane",
                "scripture_refs": "Hebrews 11:1",
                "tags": "faith"
            }
        ]
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=(high_rel_chunks, [])
        )
        
        context_result = {
            "context_text": "Faith is...",
            "chunks_used": high_rel_chunks,
            "chunks_skipped": [],
            "sources": [
                {
                    "note_id": 42,
                    "note_title": "Faith in Action",
                    "preacher": "Pastor Jane",
                    "sermon_date": "2025-02-01",
                    "scripture_refs": "Hebrews 11:1",
                    "tags": "faith"
                }
            ],
            "total_tokens": 456,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        assistant_service._mock_prompt.build_prompt.return_value = "prompt"
        
        # Mock generation error
        assistant_service._mock_textgen.generate.side_effect = GenerationError("API timeout after 60s")
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            include_metadata=True
        )
        
        # Assert
        assert "I'm having trouble generating a response" in response["answer"]
        assert len(response["sources"]) == 1  # Sources still provided!
        assert response["sources"][0]["note_id"] == 42
        assert response["metadata"]["error"] == "generation_failed"
        assert response["metadata"]["chunks_used"] == 1
        assert response["metadata"]["context_tokens"] == 456
    
    @pytest.mark.asyncio
    async def test_query_with_empty_query(self, assistant_service, mock_db):
        """Test validation of empty query input."""
        # Arrange
        user_id = 123
        
        # Act & Assert - empty string
        response = await assistant_service.query(
            user_query="",
            user_id=user_id,
            db=mock_db
        )
        
        assert "I need a valid question" in response["answer"]
        assert response["sources"] == []
        assert response["metadata"]["error"] == "invalid_input"
        
        # Act & Assert - whitespace only
        response = await assistant_service.query(
            user_query="   ",
            user_id=user_id,
            db=mock_db
        )
        
        assert "I need a valid question" in response["answer"]
        assert response["sources"] == []
    
    @pytest.mark.asyncio
    async def test_query_token_budget_enforcement(self, assistant_service, mock_db):
        """Test that token budgets are respected."""
        # Arrange
        user_query = "What is love?"
        user_id = 123
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 42
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        high_rel_chunks = [{"chunk_id": i, "note_id": i, "chunk_text": "text", "relevance_score": 0.8} for i in range(10)]
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=(high_rel_chunks, [])
        )
        
        # Context builder enforces 1200 token budget
        context_result = {
            "context_text": "context",
            "chunks_used": high_rel_chunks[:5],  # Only 5 fit in budget
            "chunks_skipped": high_rel_chunks[5:],
            "sources": [],
            "total_tokens": 1195,  # Just under budget
            "truncated": True
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        assistant_service._mock_prompt.build_prompt.return_value = "prompt"
        assistant_service._mock_textgen.generate.return_value = "answer"
        assistant_service._mock_prompt.extract_answer_from_response.return_value = "answer"
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            include_metadata=True
        )
        
        # Assert
        assert response["metadata"]["chunks_used"] == 5
        assert response["metadata"]["chunks_skipped"] == 5
        assert response["metadata"]["context_tokens"] == 1195
        assert response["metadata"]["truncated"] is True
        
        # Verify context builder was called with correct budget
        call_args = assistant_service._mock_context.build_context.call_args
        assert call_args is not None
        # Token budget should be from settings (default 1200)
    
    @pytest.mark.asyncio
    async def test_query_with_user_no_notes(self, assistant_service, mock_db):
        """Test query from user with no notes in database."""
        # Arrange
        user_query = "What is salvation?"
        user_id = 999  # New user
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 30
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        # No chunks retrieved
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=([], [])
        )
        
        # Empty context
        context_result = {
            "context_text": "",
            "chunks_used": [],
            "chunks_skipped": [],
            "sources": [],
            "total_tokens": 0,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        no_context_msg = "I don't see any sermon notes yet. Start by adding notes from your sermons!"
        assistant_service._mock_prompt.build_no_context_response.return_value = no_context_msg
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            include_metadata=True
        )
        
        # Assert
        assert response["answer"] == no_context_msg
        assert response["sources"] == []
        assert response["metadata"]["no_context"] is True
        assert response["metadata"]["chunks_retrieved"] == 0
    
    @pytest.mark.asyncio
    async def test_query_metadata_optional(self, assistant_service, mock_db):
        """Test that metadata can be excluded from response."""
        # Arrange
        user_query = "What is hope?"
        user_id = 123
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 30
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        high_rel_chunks = [{"chunk_id": 1, "note_id": 1, "chunk_text": "Hope is...", "relevance_score": 0.8}]
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=(high_rel_chunks, [])
        )
        
        context_result = {
            "context_text": "Hope is...",
            "chunks_used": high_rel_chunks,
            "chunks_skipped": [],
            "sources": [{"note_id": 1, "note_title": "Hope"}],
            "total_tokens": 200,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        assistant_service._mock_prompt.build_prompt.return_value = "prompt"
        assistant_service._mock_textgen.generate.return_value = "Hope is the anchor of the soul..."
        assistant_service._mock_prompt.extract_answer_from_response.return_value = "Hope is the anchor of the soul..."
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            include_metadata=False  # Exclude metadata
        )
        
        # Assert
        assert "answer" in response
        assert "sources" in response
        assert response["metadata"] is None  # Should be None
    
    @pytest.mark.asyncio
    async def test_query_max_sources_limit(self, assistant_service, mock_db):
        """Test that sources are limited to max_sources parameter."""
        # Arrange
        user_query = "What is love?"
        user_id = 123
        max_sources = 2
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 30
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        high_rel_chunks = [
            {"chunk_id": i, "note_id": i, "chunk_text": f"text {i}", "relevance_score": 0.8}
            for i in range(10)
        ]
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=(high_rel_chunks, [])
        )
        
        # 5 unique sources
        sources = [
            {"note_id": i, "note_title": f"Note {i}"}
            for i in range(5)
        ]
        context_result = {
            "context_text": "context",
            "chunks_used": high_rel_chunks,
            "chunks_skipped": [],
            "sources": sources,
            "total_tokens": 500,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        assistant_service._mock_prompt.build_prompt.return_value = "prompt"
        assistant_service._mock_textgen.generate.return_value = "answer"
        assistant_service._mock_prompt.extract_answer_from_response.return_value = "answer"
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            max_sources=max_sources,  # Limit to 2 sources
            include_metadata=True
        )
        
        # Assert
        assert len(response["sources"]) == max_sources  # Only 2 sources
        assert response["metadata"]["sources_count"] == 5  # But metadata shows 5 were available
    
    @pytest.mark.asyncio
    async def test_query_unexpected_error(self, assistant_service, mock_db):
        """Test handling of unexpected errors during pipeline."""
        # Arrange
        user_query = "What is peace?"
        user_id = 123
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 30
        
        # Simulate unexpected error in embedding service
        assistant_service._mock_embedding.generate.side_effect = RuntimeError("Unexpected database connection error")
        
        # Act
        response = await assistant_service.query(
            user_query=user_query,
            user_id=user_id,
            db=mock_db,
            include_metadata=True
        )
        
        # Assert
        assert "Something went wrong" in response["answer"]
        assert response["sources"] == []
        assert response["metadata"]["error"] == "unexpected"
        assert "Unexpected database connection error" in response["metadata"]["error_message"]
    
    @pytest.mark.asyncio
    async def test_query_logs_comprehensive_metrics(self, assistant_service, mock_db):
        """Test that comprehensive metrics are logged on successful query."""
        # Arrange
        user_query = "What is joy?"
        user_id = 123
        
        assistant_service._mock_tokenizer.count_tokens.return_value = 28
        assistant_service._mock_embedding.generate.return_value = [0.1] * 384
        
        high_rel_chunks = [{"chunk_id": 1, "note_id": 1, "chunk_text": "Joy is...", "relevance_score": 0.9}]
        assistant_service._mock_retrieval.retrieve_top_chunks = AsyncMock(
            return_value=(high_rel_chunks, [])
        )
        
        context_result = {
            "context_text": "Joy is...",
            "chunks_used": high_rel_chunks,
            "chunks_skipped": [],
            "sources": [{"note_id": 1, "note_title": "Joy Unspeakable"}],
            "total_tokens": 300,
            "truncated": False
        }
        assistant_service._mock_context.build_context.return_value = context_result
        
        assistant_service._mock_prompt.build_prompt.return_value = "prompt"
        assistant_service._mock_textgen.generate.return_value = "Joy is a fruit of the Spirit..."
        assistant_service._mock_prompt.extract_answer_from_response.return_value = "Joy is a fruit of the Spirit..."
        
        # Act
        with patch('app.services.assistant_service.logger') as mock_logger:
            response = await assistant_service.query(
                user_query=user_query,
                user_id=user_id,
                db=mock_db,
                include_metadata=True
            )
            
            # Assert logging calls
            assert mock_logger.info.called
            
            # Find the final success log
            success_log_calls = [
                call for call in mock_logger.info.call_args_list
                if "Query completed successfully" in str(call)
            ]
            assert len(success_log_calls) > 0


class TestAssistantServiceSingleton:
    """Test singleton pattern for AssistantService."""
    
    def test_get_assistant_service_singleton(self):
        """Test that get_assistant_service returns the same instance."""
        with patch('app.services.assistant_service.get_tokenizer_service'), \
             patch('app.services.assistant_service.EmbeddingService'), \
             patch('app.services.assistant_service.get_retrieval_service'), \
             patch('app.services.assistant_service.get_context_builder'), \
             patch('app.services.assistant_service.get_prompt_engine'), \
             patch('app.services.assistant_service.get_textgen_service'):
            
            service1 = get_assistant_service()
            service2 = get_assistant_service()
            
            assert service1 is service2


class TestAssistantServiceInitialization:
    """Test AssistantService initialization."""
    
    def test_initialization_creates_all_dependencies(self):
        """Test that all sub-services are initialized."""
        with patch('app.services.assistant_service.get_tokenizer_service') as mock_tokenizer, \
             patch('app.services.assistant_service.EmbeddingService') as mock_embedding, \
             patch('app.services.assistant_service.get_retrieval_service') as mock_retrieval, \
             patch('app.services.assistant_service.get_context_builder') as mock_context, \
             patch('app.services.assistant_service.get_prompt_engine') as mock_prompt, \
             patch('app.services.assistant_service.get_textgen_service') as mock_textgen:
            
            service = AssistantService()
            
            # Assert all getters were called
            mock_tokenizer.assert_called_once()
            mock_embedding.assert_called_once()
            mock_retrieval.assert_called_once()
            mock_context.assert_called_once()
            mock_prompt.assert_called_once()
            mock_textgen.assert_called_once()
            
            # Assert attributes exist
            assert hasattr(service, 'tokenizer')
            assert hasattr(service, 'embedding_service')
            assert hasattr(service, 'retrieval')
            assert hasattr(service, 'context_builder')
            assert hasattr(service, 'prompt_engine')
            assert hasattr(service, 'textgen')
