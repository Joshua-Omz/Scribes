"""
Assistant API routes.

🟡 COLLABORATIVE: AI can scaffold, YOU add security and validation

Endpoints:
- POST /assistant/query - Main query endpoint
- GET /assistant/health - Health check for assistant services

AI can create basic handler structure, but YOU should:
- Add rate limiting
- Add input sanitization
- Add security headers
- Add comprehensive error responses
- Add OpenAPI documentation
- Add request logging
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.schemas.assistant_schemas import (
    AssistantQueryRequest,
    AssistantResponse,
    AssistantError
)
from app.services.assistant_service import get_assistant_service

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
    
    🔴 TODO (YOU): Add rate limiting, input sanitization, caching
    """
)
async def query_assistant(
    request: AssistantQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process assistant query.
    
    🟡 SCAFFOLD - Basic structure provided, YOU enhance
    
    TODO (YOU):
    - Add rate limiting check (Redis)
    - Check cache for recent identical queries
    - Sanitize input for prompt injection
    - Add request correlation ID
    - Log query metrics
    - Handle errors gracefully
    - Return user-friendly error messages
    """
    logger.info(f"Assistant query from user {current_user.id}: {request.query[:50]}...")
    
    # TODO: Rate limiting check
    # TODO: Cache check
    # TODO: Input sanitization
    
    raise NotImplementedError(
        "Assistant query endpoint needs implementation. "
        "AI provided scaffold, YOU add security and business logic."
    )


@router.get(
    "/health",
    summary="Health check for assistant services",
    description="Check if all assistant dependencies are ready (embedding model, generation model, etc.)"
)
async def assistant_health():
    """
    Health check endpoint.
    
    🟡 SCAFFOLD - YOU should implement checks for:
    - Embedding service ready
    - Generation model loaded
    - Database connectivity
    - Redis connectivity (for caching)
    """
    raise NotImplementedError("Health check not implemented")

