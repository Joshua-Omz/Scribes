"""
AI Assistant service - orchestrates the full RAG pipeline.

🟡 COLLABORATIVE: AI can scaffold, YOU review and enhance

This service orchestrates:
1. Query tokenization and validation
2. Query embedding generation
3. Chunk retrieval (vector search)
4. Context building (token-aware)
5. Prompt assembly
6. Text generation
7. Post-processing and formatting

Key responsibilities:
- Coordinate all sub-services
- Handle errors gracefully
- Log metrics and events
- Ensure proper async flow
- Maintain user isolation throughout

AI can create basic flow, but YOU should:
- Add comprehensive error handling
- Add metrics/observability
- Add business logic (e.g., query classification)
- Optimize performance
- Add caching integration
"""

from typing import Dict, Any
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.tokenizer_service import get_tokenizer_service
from app.services.ai.embedding_service import EmbeddingService
from app.services.ai.retrieval_service import get_retrieval_service
from app.services.ai.context_builder import get_context_builder
from app.core.ai.prompt_engine import get_prompt_engine
from app.services.ai.hf_inference_service import get_inference_service, GenerationError
from app.core.config import settings

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Main service for AI assistant queries.
    
    🟡 SCAFFOLD - AI provides structure, YOU enhance with business logic
    """
    
    def __init__(self):
        """Initialize assistant service with dependencies."""
        self.tokenizer = get_tokenizer_service()
        self.embedding_service = EmbeddingService()
        self.retrieval = get_retrieval_service()
        self.context_builder = get_context_builder()
        self.prompt_engine = get_prompt_engine()
        self.inference = get_inference_service()  # Updated to new service
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
            
            query_tokens = self.tokenizer.count_tokens(user_query)
            logger.info(f"Query tokens: {query_tokens}")
            
            # ============================================================
            # STEP 2: Embedding Generation
            # ============================================================
            logger.debug("Generating query embedding...")
            query_embedding = self.embedding_service.generate(user_query)
            logger.debug(f"Query embedding generated: {len(query_embedding)} dimensions")
            
            # ============================================================
            # STEP 3: Chunk Retrieval (Vector Search with User Isolation)
            # ============================================================
            logger.debug(f"Retrieving chunks with top_k={settings.assistant_top_k}...")
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
                        "truncated": False,
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
            # ============================================================
            logger.info("Calling inference service (chat completion)...")
            try:
                raw_answer = self.inference.generate_from_messages(
                    messages=messages,
                    max_tokens=settings.assistant_max_output_tokens,
                    temperature=settings.hf_generation_temperature,
                    top_p=settings.assistant_model_top_p
                )
                logger.info(f"Answer generated: {len(raw_answer)} characters")
                
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
                        "truncated": context_result["truncated"],
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
                    "truncated": context_result["truncated"],
                    "duration_ms": duration_ms,
                    "sources_count": len(sources)
                } if include_metadata else None
            }
            
            # Comprehensive logging
            logger.info(
                f"Query completed successfully in {duration_ms:.0f}ms",
                extra={
                    "user_id": user_id,
                    "query_length": len(user_query),
                    "query_tokens": query_tokens,
                    "chunks_retrieved": len(high_rel) + len(low_rel),
                    "chunks_used": len(context_result["chunks_used"]),
                    "context_tokens": context_result["total_tokens"],
                    "answer_length": len(answer),
                    "duration_ms": duration_ms,
                    "sources_count": len(sources),
                    "truncated": context_result["truncated"]
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


def get_assistant_service() -> AssistantService:
    """Get or create assistant service singleton."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = AssistantService()
    return _assistant_service

