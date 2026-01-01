"""
AI Assistant service - orchestrates the full RAG pipeline with 3-layer caching.

🟡 COLLABORATIVE: AI can scaffold, YOU review and enhance

This service orchestrates:
1. Query tokenization and validation
2. Query embedding generation (L2 CACHED)
3. Chunk retrieval (vector search) (L3 CACHED)
4. Context building (token-aware)
5. Prompt assembly
6. Text generation
7. Post-processing and formatting (L1 CACHED)

Phase 2 Caching Integration:
- L1 (Query Result Cache): Complete responses (24h TTL, 40% hit rate target)
- L2 (Embedding Cache): Query embeddings (7d TTL, 60% hit rate target)
- L3 (Context Cache): Retrieved chunks (1h TTL, 70% hit rate target)

Key responsibilities:
- Coordinate all sub-services
- Handle errors gracefully
- Log metrics and events
- Ensure proper async flow
- Maintain user isolation throughout
- Cache intelligent layering for cost optimization
"""

from typing import Dict, Any, Optional
import logging
import time
import hashlib
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.tokenizer_service import get_tokenizer_service
from app.services.ai.embedding_service import EmbeddingService
from app.services.ai.retrieval_service import get_retrieval_service
from app.services.ai.context_builder import get_context_builder
from app.core.ai.prompt_engine import get_prompt_engine
from app.services.ai.hf_inference_service import get_inference_service, GenerationError
from app.core.config import settings

# Phase 2: Import caching layers
from app.core.cache import RedisCacheManager
from app.services.ai.caching.query_cache import QueryCache
from app.services.ai.caching.embedding_cache import EmbeddingCache
from app.services.ai.caching.context_cache import ContextCache

# Phase 4: Import circuit breaker components
from app.services.ai.circuit_breaker import ServiceUnavailableError
from pybreaker import CircuitBreakerError

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Main service for AI assistant queries with 3-layer caching.
    
    🟡 SCAFFOLD - AI provides structure, YOU enhance with business logic
    """
    
    def __init__(self, cache_manager: Optional[RedisCacheManager] = None):
        """
        Initialize assistant service with dependencies.
        
        Args:
            cache_manager: Optional Redis cache manager for caching layers
        """
        self.tokenizer = get_tokenizer_service()
        self.embedding_service = EmbeddingService()
        self.retrieval = get_retrieval_service()
        self.context_builder = get_context_builder()
        self.prompt_engine = get_prompt_engine()
        self.inference = get_inference_service()
        
        # Initialize cache layers (Phase 2)
        if cache_manager and cache_manager.is_available:
            self.query_cache = QueryCache(cache_manager)
            self.embedding_cache = EmbeddingCache(cache_manager)
            self.context_cache = ContextCache(cache_manager)
            self.caching_enabled = True
            logger.info("AssistantService initialized with 3-layer caching ✅")
        else:
            self.query_cache = None
            self.embedding_cache = None
            self.context_cache = None
            self.caching_enabled = False
            logger.warning("AssistantService initialized WITHOUT caching ⚠️")
        
        logger.info("AssistantService initialized")
    
    async def query(
        self,
        user_query: str,
        user_id: int,
        db: AsyncSession,
        max_sources: int = 5,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Process user query through full RAG pipeline.
        
        ✅ IMPLEMENTED - Complete 7-step RAG pipeline
        
        Flow:
        1. Validate and tokenize query
        2. Embed query → vector
        3. Retrieve relevant chunks (user-scoped)
        4. Build context within token budget
        5. Assemble prompt
        6. Generate answer
        7. Post-process and format response
        
        Args:
            user_query: User's question
            user_id: Current user ID (for isolation)
            db: Database session
            max_sources: Max sources to cite
            include_metadata: Include context metadata
            
        Returns:
            AssistantResponse dict with keys:
            - answer: Generated answer text
            - sources: List of source note dicts (limited by max_sources)
            - metadata: Optional dict with performance metrics
            
        Raises:
            ValueError: If query is empty or invalid
        """
        start_time = time.time()
        
        logger.info(f"Processing assistant query for user {user_id}: {user_query[:50]}...")
        
        try:
            # ============================================================
            # STEP 1: Query Validation & Tokenization
            # ============================================================
            if not user_query or not user_query.strip():
                logger.warning(f"Empty query received from user {user_id}")
                raise ValueError("Query cannot be empty")
            
            # Count original query tokens
            original_query_tokens = self.tokenizer.count_tokens(user_query)
            query_truncated = False
            
            # Truncate query if it exceeds budget
            if original_query_tokens > settings.assistant_user_query_tokens:
                logger.warning(
                    f"Query exceeds token limit: {original_query_tokens} > "
                    f"{settings.assistant_user_query_tokens}. Truncating..."
                )
                user_query = self.tokenizer.truncate_to_tokens(
                    user_query, 
                    settings.assistant_user_query_tokens
                )
                query_truncated = True
                query_tokens = self.tokenizer.count_tokens(user_query)
                logger.info(
                    f"Query truncated: {original_query_tokens} → {query_tokens} tokens"
                )
            else:
                query_tokens = original_query_tokens
            
            logger.info(f"Query tokens: {query_tokens}")
            
            # ============================================================
            # STEP 2: Embedding Generation (L2 CACHED)
            # ============================================================
            logger.debug("Generating query embedding...")
            
            # Try L2 cache first
            query_embedding = None
            if self.caching_enabled and self.embedding_cache:
                query_embedding = await self.embedding_cache.get(user_query)
            
            # L2 miss - compute embedding
            if query_embedding is None:
                query_embedding = self.embedding_service.generate(user_query)
                
                # Store in L2 cache
                if self.caching_enabled and self.embedding_cache:
                    await self.embedding_cache.set(user_query, query_embedding)
            
            # Convert to numpy array if it's a list (for cache key generation)
            if isinstance(query_embedding, list):
                query_embedding_array = np.array(query_embedding, dtype=np.float32)
            else:
                query_embedding_array = query_embedding
            
            # Generate embedding hash for L3 cache key
            embedding_hash = hashlib.sha256(query_embedding_array.tobytes()).hexdigest()
            
            logger.debug(f"Query embedding generated: {len(query_embedding)} dimensions")
            
            # ============================================================
            # STEP 3: Chunk Retrieval (Vector Search with User Isolation) (L3 CACHED)
            # ============================================================
            logger.debug(f"Retrieving chunks with top_k={settings.assistant_top_k}...")
            
            # Try L3 cache first
            cached_chunks = None
            if self.caching_enabled and self.context_cache:
                cached_chunks = await self.context_cache.get(user_id, embedding_hash)
            
            if cached_chunks:
                # L3 hit - use cached chunks
                # Separate into high/low relevance based on stored similarity scores
                high_rel = [c for c in cached_chunks if c.get("similarity", 0) >= 0.7]
                low_rel = [c for c in cached_chunks if c.get("similarity", 0) < 0.7]
                logger.info(f"Retrieved from L3 cache: {len(high_rel)} high, {len(low_rel)} low")
            else:
                # L3 miss - do vector search
                high_rel, low_rel = await self.retrieval.retrieve_top_chunks(
                    db=db,
                    query_embedding=query_embedding,
                    user_id=user_id,
                    top_k=settings.assistant_top_k
                )
                logger.info(
                    f"Retrieved {len(high_rel)} high-relevance, "
                    f"{len(low_rel)} low-relevance chunks"
                )
                
                # Store in L3 cache
                if self.caching_enabled and self.context_cache:
                    # Combine for caching
                    all_chunks = high_rel + low_rel
                    await self.context_cache.set(user_id, embedding_hash, all_chunks)
            
            # ============================================================
            # L1 CACHE CHECK: Complete Response Cache
            # ============================================================
            # Extract context IDs for L1 cache key
            context_ids = []
            for chunk in (high_rel + low_rel):
                if hasattr(chunk, 'id'):
                    context_ids.append(chunk.id)
                elif isinstance(chunk, dict) and 'chunk_id' in chunk:
                    context_ids.append(chunk['chunk_id'])
            
            # Check L1 cache for complete response
            if self.caching_enabled and self.query_cache and context_ids:
                cached_response = await self.query_cache.get(
                    user_id=user_id,
                    query=user_query,
                    context_ids=context_ids
                )
                if cached_response:
                    # L1 HIT - Return cached complete response immediately
                    logger.info("✅ L1 CACHE HIT - Returning cached response")
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Update duration in metadata
                    if cached_response.get("metadata"):
                        cached_response["metadata"]["duration_ms"] = duration_ms
                        cached_response["metadata"]["from_cache"] = True
                    
                    return cached_response
            
            # L1 miss - continue with generation...
            
            # ============================================================
            # STEP 4: Context Building (Token-Aware Assembly)
            # ============================================================
            logger.debug(
                f"Building context with budget={settings.assistant_max_context_tokens} tokens..."
            )
            context_result = self.context_builder.build_context(
                high_relevance_chunks=high_rel,
                low_relevance_chunks=low_rel,
                token_budget=settings.assistant_max_context_tokens
            )
            
            context_text = context_result["context_text"]
            sources = context_result["sources"]
            logger.info(
                f"Context built: {context_result['total_tokens']} tokens, "
                f"{len(context_result['chunks_used'])} chunks used, "
                f"{len(sources)} unique sources"
            )
            
            # Edge Case: No relevant context found
            if not context_text:
                logger.info("No relevant context found - returning no-context response")
                duration_ms = (time.time() - start_time) * 1000
                
                return {
                    "answer": self.prompt_engine.build_no_context_response(user_query),
                    "sources": [],
                    "metadata": {
                        "no_context": True,
                        "chunks_retrieved": len(low_rel),
                        "chunks_used": 0,
                        "chunks_skipped": len(low_rel),
                        "context_tokens": 0,
                        "query_tokens": query_tokens,
                        "query_truncated": query_truncated,
                        "context_truncated": False,
                        "duration_ms": duration_ms
                    } if include_metadata else None
                }
            
            # ============================================================
            # STEP 5: Prompt Assembly (Chat Messages Format)
            # ============================================================
            logger.debug("Assembling chat messages...")
            messages = self.prompt_engine.build_messages(
                user_query=user_query,
                context_text=context_text,
                sources=sources
            )
            logger.debug(f"Chat messages assembled: {len(messages)} messages")
            
            # ============================================================
            # STEP 6: Text Generation (LLM Inference via Chat Completion)
            # WITH CIRCUIT BREAKER FALLBACK
            # ============================================================
            logger.info("Calling inference service (chat completion)...")
            try:
                # Try primary path: Full LLM generation
                raw_answer = self.inference.generate_from_messages(
                    messages=messages,
                    max_tokens=settings.assistant_max_output_tokens,
                    temperature=settings.hf_generation_temperature,
                    top_p=settings.assistant_model_top_p
                )
                logger.info(f"Answer generated: {len(raw_answer)} characters")
            
            except (ServiceUnavailableError, CircuitBreakerError) as e:
                # Circuit breaker is OPEN - attempt fallback to L1 cache
                logger.warning(
                    f"Circuit breaker OPEN, attempting L1 cache fallback",
                    extra={
                        "user_id": user_id,
                        "query_length": len(user_query),
                        "circuit_state": "open"
                    }
                )
                
                # Try L1 cache fallback (fresh check after circuit opens)
                if self.caching_enabled and self.query_cache and context_ids:
                    cached_response = await self.query_cache.get(
                        user_id=user_id,
                        query=user_query,
                        context_ids=context_ids
                    )
                    
                    if cached_response:
                        # L1 HIT - Return cached response
                        logger.info("✅ Circuit open, L1 cache fallback successful")
                        duration_ms = (time.time() - start_time) * 1000
                        
                        # Add fallback metadata
                        cached_response["metadata"] = {
                            **cached_response.get("metadata", {}),
                            "from_fallback": True,
                            "fallback_reason": "circuit_breaker_open",
                            "fallback_source": "l1_cache",
                            "duration_ms": duration_ms
                        }
                        
                        return cached_response
                
                # No cache available - return graceful degradation response
                logger.warning(
                    "Circuit open, no cache available, returning excerpts",
                    extra={"user_id": user_id}
                )
                
                # Extract top 3 relevant excerpts from context
                excerpts = []
                for chunk in (high_rel + low_rel)[:3]:  # Top 3 chunks
                    chunk_text = chunk.get("text", "") if isinstance(chunk, dict) else chunk.text
                    if chunk_text:
                        excerpts.append(f"• {chunk_text[:200]}...")  # First 200 chars
                
                duration_ms = (time.time() - start_time) * 1000
                
                return {
                    "answer": (
                        "⚠️ The AI assistant is temporarily unavailable. "
                        "Here are the most relevant excerpts from your sermons:\n\n" +
                        "\n\n".join(excerpts) if excerpts else
                        "⚠️ The AI assistant is temporarily unavailable and "
                        "no relevant sermon content was found for your query. "
                        "Please try again in a few moments."
                    ),
                    "sources": sources[:max_sources] if sources else [],
                    "metadata": {
                        "from_fallback": True,
                        "fallback_reason": "circuit_breaker_open_no_cache",
                        "fallback_source": "excerpts",
                        "chunks_retrieved": len(high_rel) + len(low_rel),
                        "chunks_used": 0,
                        "excerpts_returned": len(excerpts),
                        "duration_ms": duration_ms,
                        "no_context": len(excerpts) == 0
                    } if include_metadata else None
                }
                
            except GenerationError as e:
                logger.error(f"Text generation failed: {e}")
                duration_ms = (time.time() - start_time) * 1000
                
                return {
                    "answer": (
                        "I'm having trouble generating a response right now. "
                        "Please try rephrasing your question or try again in a moment."
                    ),
                    "sources": sources[:max_sources] if sources else [],
                    "metadata": {
                        "error": "generation_failed",
                        "chunks_used": len(context_result["chunks_used"]),
                        "chunks_skipped": len(context_result["chunks_skipped"]),
                        "context_tokens": context_result["total_tokens"],
                        "query_tokens": query_tokens,
                        "query_truncated": query_truncated,
                        "context_truncated": context_result["truncated"],
                        "duration_ms": duration_ms
                    } if include_metadata else None
                }
            
            # ============================================================
            # STEP 7: Response Formatting & Post-Processing
            # ============================================================
            logger.debug("Extracting and formatting final answer...")
            answer = self.prompt_engine.extract_answer_from_response(raw_answer)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Limit sources to max_sources
            limited_sources = sources[:max_sources] if sources else []
            
            # Build final response
            response = {
                "answer": answer,
                "sources": limited_sources,
                "metadata": {
                    "chunks_used": len(context_result["chunks_used"]),
                    "chunks_skipped": len(context_result["chunks_skipped"]),
                    "context_tokens": context_result["total_tokens"],
                    "query_tokens": query_tokens,
                    "query_truncated": query_truncated,
                    "context_truncated": context_result["truncated"],
                    "duration_ms": duration_ms,
                    "sources_count": len(sources),
                    "from_cache": False  # New generation
                } if include_metadata else None
            }
            
            # ============================================================
            # L1 CACHE STORE: Cache complete response
            # ============================================================
            if self.caching_enabled and self.query_cache and context_ids:
                await self.query_cache.set(
                    user_id=user_id,
                    query=user_query,
                    context_ids=context_ids,
                    response=response
                )
            
            # Comprehensive logging
            logger.info(
                f"Query completed successfully in {duration_ms:.0f}ms",
                extra={
                    "user_id": user_id,
                    "query_length": len(user_query),
                    "query_tokens": query_tokens,
                    "query_truncated": query_truncated,
                    "chunks_retrieved": len(high_rel) + len(low_rel),
                    "chunks_used": len(context_result["chunks_used"]),
                    "context_tokens": context_result["total_tokens"],
                    "context_truncated": context_result["truncated"],
                    "answer_length": len(answer),
                    "duration_ms": duration_ms,
                    "sources_count": len(sources)
                }
            )
            
            return response
            
        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Invalid input from user {user_id}: {e}")
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "answer": "I need a valid question to help you explore your sermon notes.",
                "sources": [],
                "metadata": {
                    "error": "invalid_input",
                    "error_message": str(e),
                    "duration_ms": duration_ms
                } if include_metadata else None
            }
            
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                f"Unexpected error processing query for user {user_id}: {e}",
                exc_info=True
            )
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "answer": "Something went wrong while processing your question. Please try again.",
                "sources": [],
                "metadata": {
                    "error": "unexpected",
                    "error_message": str(e),
                    "duration_ms": duration_ms
                } if include_metadata else None
            }


# Singleton
_assistant_service = None


def get_assistant_service(cache_manager: Optional[RedisCacheManager] = None) -> AssistantService:
    """
    Get or create assistant service singleton.
    
    Args:
        cache_manager: Optional cache manager for caching layers
        
    Returns:
        AssistantService: Singleton instance
    """
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = AssistantService(cache_manager=cache_manager)
    return _assistant_service


async def invalidate_user_cache(user_id: int, cache_manager: Optional[RedisCacheManager] = None):
    """
    Invalidate cached data when user modifies notes.
    
    Called by note CRUD endpoints to ensure fresh search results.
    
    Args:
        user_id: User ID to invalidate cache for
        cache_manager: Cache manager instance
    """
    if cache_manager and cache_manager.is_available:
        context_cache = ContextCache(cache_manager)
        await context_cache.invalidate_user(user_id)
        logger.info(f"Invalidated L3 cache for user {user_id}")
