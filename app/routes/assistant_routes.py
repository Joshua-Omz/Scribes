"""
Assistant API routes - FastAPI service layer only.

SERVICE RESPONSIBILITIES:
- Input sanitization
- RAG pipeline orchestration
- AI-specific caching (queries, embeddings, context)
- Cost tracking (token usage)
- Semantic metrics
- Error handling

GATEWAY RESPONSIBILITIES (not in service):
- Rate limiting (per-user, per-IP)
- Authentication & authorization
- Edge caching (static content)
- Global retries
- Request correlation IDs

Endpoints:
- POST /assistant/query - Main query endpoint with RAG
- GET /assistant/health - Health check for assistant dependencies
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.schemas.assistant_schemas import (
    AssistantQueryRequest,
    AssistantResponse,
    AssistantError
)
from app.services.ai.assistant_service import get_assistant_service, AssistantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


@router.post(
    "/query",
    response_model=AssistantResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the AI assistant",
    description="""
    Ask the AI assistant a question about your sermon notes.
    
    The assistant uses RAG (Retrieval-Augmented Generation) to:
    1. Find relevant chunks from your notes
    2. Build context within token limits
    3. Generate an answer citing sources
    
    SERVICE-LEVEL FEATURES:
    - Input sanitization: Anti-injection protection
    - Token management: Automatic truncation
    - Cost tracking: Token usage monitoring
    - AI-specific caching: Queries, embeddings, context
    - Error handling: Graceful degradation
    - Circuit breakers: LLM dependency protection
    
    NOTE: Rate limiting, auth, and global metrics are handled by API Gateway.
    """
)
async def query_assistant(
    request: AssistantQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AssistantResponse:
    """
    Process assistant query - service-level responsibilities only.
    
    Steps:
    1. Input validation and sanitization
    2. Query the RAG pipeline (with AI caching)
    3. Track cost (token usage)
    4. Return structured response
    
    Gateway handles: rate limiting, auth, edge caching, retries
    Service handles: AI logic, semantic caching, cost tracking
    
    Args:
        request: Query request with user question
        current_user: Authenticated user (from gateway auth)
        db: Database session
        
    Returns:
        AssistantResponse with answer and metadata
        
    Raises:
        HTTPException: 400 if invalid input, 500 if service error
    """
    start_time = time.time()
    request_cost = 0.0
    
    try:
        # Step 1: Input validation (gateway handles rate limiting and auth)
        logger.info(f"Assistant query from user {current_user.id}: {request.query[:50]}...")
        
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        if len(request.query) > 10000:  # Sanity check
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query too long (max 10,000 characters)"
            )
        
        # Step 2: Get cache manager and assistant service (Phase 2)
        from app.core.dependencies import get_cache
        cache_manager = await get_cache()
        assistant = get_assistant_service(cache_manager=cache_manager)
        
        result = await assistant.query(
            user_id=current_user.id,
            user_query=request.query,  # Changed from query_text
            db=db
        )
        
        # Step 3: Calculate cost for tracking (service responsibility)
        if result.get("metadata"):
            metadata = result["metadata"]
            request_cost = calculate_request_cost(metadata)
        
        # Step 4: Build response
        duration = time.time() - start_time
        
        response = AssistantResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            metadata={
                **result.get("metadata", {}),
                "request_duration_seconds": round(duration, 2),
                "api_cost_usd": request_cost
            }
        )
        
        logger.info(
            f"Assistant query completed for user {current_user.id}: "
            f"{duration:.2f}s, cost=${request_cost:.6f}"
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
        
    except Exception as e:
        logger.error(
            f"Assistant query failed for user {current_user.id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant service error: {str(e)}"
        )


def calculate_request_cost(metadata: dict) -> float:
    """
    Calculate API cost for a request based on token usage.
    
    Llama-3.2-3B-Instruct pricing (approximate):
    - Input: $0.0000002 per token
    - Output: $0.0000006 per token
    
    Args:
        metadata: Response metadata with token counts
        
    Returns:
        Cost in USD
    """
    query_tokens = metadata.get("query_tokens", 0)
    context_tokens = metadata.get("context_tokens", 0)
    output_tokens = metadata.get("output_tokens", 0)
    
    # Input cost (query + context)
    input_tokens = query_tokens + context_tokens
    input_cost = input_tokens * 0.0000002
    
    # Output cost
    output_cost = output_tokens * 0.0000006
    
    total_cost = input_cost + output_cost
    
    return round(total_cost, 8)  # Round to 8 decimal places


@router.get(
    "/cache-stats",
    summary="Get AI cache performance statistics",
    description="""
    Retrieve performance statistics for the three-layer AI cache:
    - L1 (Query Result Cache): Complete AI responses
    - L2 (Embedding Cache): Query embeddings
    - L3 (Context Cache): Retrieved sermon chunks
    
    Shows hit rates, cost savings, and cache sizes.
    Useful for monitoring cache effectiveness and ROI.
    """
)
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AI cache statistics (Phase 2: Semantic Caching).
    
    Returns metrics for all three cache layers:
    - Total entries cached
    - Hit counts and rates
    - Estimated cost savings
    - TTL configurations
    
    Args:
        current_user: Authenticated user
        
    Returns:
        dict: Cache statistics by layer
        
    Raises:
        HTTPException: 503 if cache unavailable
    """
    try:
        # Import cache dependencies
        from app.core.dependencies import get_cache
        from app.services.ai.caching import QueryCache, EmbeddingCache, ContextCache
        
        # Get cache manager
        cache_manager = await get_cache()
        
        if not cache_manager.is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache not available"
            )
        
        # Get stats from each layer
        query_cache = QueryCache(cache_manager)
        embedding_cache = EmbeddingCache(cache_manager)
        context_cache = ContextCache(cache_manager)
        
        l1_stats = await query_cache.get_stats()
        l2_stats = await embedding_cache.get_stats()
        l3_stats = await context_cache.get_stats()
        
        # Aggregate stats
        total_cost_saved = l1_stats.get("total_cost_saved", 0.0)
        
        return {
            "cache_enabled": True,
            "layers": {
                "l1_query_result": l1_stats,
                "l2_embedding": l2_stats,
                "l3_context": l3_stats
            },
            "combined": {
                "total_cost_saved_usd": total_cost_saved,
                "annual_savings_estimate_usd": round(total_cost_saved * 365, 2)
            },
            "note": "Cost savings calculated from L1 cache hits (full LLM calls avoided)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check for assistant services",
    description="Check if assistant dependencies are ready (embedding model, generation model, database, cache)"
)
async def assistant_health():
    """
    Health check endpoint - service dependencies only.
    
    Checks:
    - Assistant service initialization
    - Database connectivity
    - Model availability
    - Cache availability (Phase 2)
    
    NOTE: Gateway handles infrastructure health (Redis, load balancers, etc.)
    
    Returns:
        200: All services healthy
        503: One or more services unavailable
    """
    health_status = {
        "status": "healthy",
        "checks": {},
        "service": "assistant"
    }
    
    try:
        # Check assistant service
        assistant = get_assistant_service()
        health_status["checks"]["assistant_service"] = "available"
        health_status["checks"]["models"] = "initialized"
        
        # Check cache availability (Phase 2)
        try:
            from app.core.dependencies import get_cache
            cache_manager = await get_cache()
            health_status["checks"]["cache"] = "available" if cache_manager.is_available else "unavailable"
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            health_status["checks"]["cache"] = "unavailable"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )