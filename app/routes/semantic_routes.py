"""
Semantic search routes for AI-powered note discovery - Version 2.
Refactored for reliability, performance, and maintainability.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from arq import create_pool
from arq.connections import RedisSettings
import logging

from app.core.config import settings

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.models.note_model import Note
from app.models.background_job_model import BackgroundJob
from app.schemas.note_schemas import NoteResponse
from app.schemas.semantic_schemas import (
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchResponse,
    EmbeddingStatusResponse,
    RegenerationStatusResponse
)
from app.services.embedding_service import get_embedding_service, EmbeddingGenerationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/semantic", tags=["Semantic Search"])


# ============================================================================
# Search Endpoints (ORM-Native with pgvector)
# ============================================================================

@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    search_request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform semantic search across user's notes using ORM-native vector search.
    
    This endpoint uses AI embeddings to find notes by meaning, not just keywords.
    For example, searching for "faith" will also find notes about "trust", "belief", etc.
    
    Features:
    - Full pagination support (limit + offset)
    - ORM-native queries (no raw SQL)
    - Automatic type conversion via pgvector
    - Retry logic built into embedding service
    
    Args:
        search_request: Search parameters including query and filters
        db: Database session
        current_user: Authenticated user
        
    Returns:
        SemanticSearchResponse with matching notes and similarity scores
    """
    try:
        # Generate embedding for the search query (with automatic retries)
        embedding_service = get_embedding_service()
        
        try:
            query_embedding = embedding_service.generate(search_request.query)
        except EmbeddingGenerationError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embedding service unavailable: {str(e)}"
            )
        
        # Calculate similarity score using pgvector's cosine_distance
        # 1 - distance = similarity (higher is more similar)
        similarity_score = (1 - Note.embedding.cosine_distance(query_embedding)).label("similarity")
        
        # Build ORM query with pagination
        stmt = (
            select(Note, similarity_score)
            .where(
                Note.user_id == current_user.id,
                Note.embedding.isnot(None),
                similarity_score >= search_request.min_similarity
            )
            .order_by(Note.embedding.cosine_distance(query_embedding))  # Ascending distance = descending similarity
            .offset(search_request.offset)
            .limit(search_request.limit)
        )
        
        # Execute query - pgvector handles all type conversions automatically
        result = await db.execute(stmt)
        rows = result.all()
        
        # Build response using ORM objects directly
        search_results = [
            SemanticSearchResult(
                note=NoteResponse.model_validate(note_obj),
                similarity_score=float(similarity)
            )
            for note_obj, similarity in rows
        ]
        
        return SemanticSearchResponse(
            results=search_results,
            query=search_request.query,
            total_results=len(search_results),
            offset=search_request.offset,
            limit=search_request.limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get("/similar/{note_id}", response_model=SemanticSearchResponse)
async def find_similar_notes(
    note_id: int,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_similarity: float = Query(default=0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find notes similar to a specific note using ORM-native vector search.
    
    This helps discover related sermon notes based on semantic similarity.
    Useful for building a knowledge graph and finding connections.
    
    Args:
        note_id: ID of the source note
        limit: Maximum number of similar notes to return
        offset: Number of results to skip (pagination)
        min_similarity: Minimum similarity threshold
        db: Database session
        current_user: Authenticated user
        
    Returns:
        SemanticSearchResponse with similar notes
    """
    try:
        # Get the source note
        result = await db.execute(
            select(Note).where(
                Note.id == note_id,
                Note.user_id == current_user.id
            )
        )
        source_note = result.scalar_one_or_none()
        
        if not source_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found or you don't have permission to access it"
            )
        
        if source_note.embedding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source note does not have an embedding. Please update the note to generate one."
            )
        
        # Use source note's embedding for similarity search
        source_embedding = source_note.embedding
        similarity_score = (1 - Note.embedding.cosine_distance(source_embedding)).label("similarity")
        
        # Build ORM query
        stmt = (
            select(Note, similarity_score)
            .where(
                Note.user_id == current_user.id,
                Note.id != note_id,  # Exclude the source note itself
                Note.embedding.isnot(None),
                similarity_score >= min_similarity
            )
            .order_by(Note.embedding.cosine_distance(source_embedding))
            .offset(offset)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        # Build response
        search_results = [
            SemanticSearchResult(
                note=NoteResponse.model_validate(note_obj),
                similarity_score=float(similarity)
            )
            for note_obj, similarity in rows
        ]
        
        return SemanticSearchResponse(
            results=search_results,
            query=f"Similar to: {source_note.title}",
            total_results=len(search_results),
            offset=offset,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar notes search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar notes search failed: {str(e)}"
        )


# ============================================================================
# Status & Management Endpoints
# ============================================================================

@router.get("/status", response_model=EmbeddingStatusResponse)
async def get_embedding_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check the status of embeddings for the current user's notes.
    
    Uses efficient SQL aggregation instead of loading all notes into memory.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        EmbeddingStatusResponse with embedding coverage statistics
    """
    try:
        # Use func.count() for efficient aggregation (no memory loading)
        total_notes = await db.scalar(
            select(func.count()).select_from(Note).where(Note.user_id == current_user.id)
        )
        
        notes_with_embeddings = await db.scalar(
            select(func.count()).select_from(Note).where(
                Note.user_id == current_user.id,
                Note.embedding.isnot(None)
            )
        )
        
        # Calculate statistics
        total_notes = total_notes or 0
        notes_with_embeddings = notes_with_embeddings or 0
        notes_without_embeddings = total_notes - notes_with_embeddings
        coverage_percentage = (notes_with_embeddings / total_notes * 100) if total_notes > 0 else 0.0
        
        # Get model info
        embedding_service = get_embedding_service()
        model_info = embedding_service.get_model_info()
        
        return EmbeddingStatusResponse(
            total_notes=total_notes,
            notes_with_embeddings=notes_with_embeddings,
            notes_without_embeddings=notes_without_embeddings,
            coverage_percentage=round(coverage_percentage, 2),
            model_info=model_info
        )
        
    except Exception as e:
        logger.error(f"Embedding status check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding status: {str(e)}"
        )


# ============================================================================
# Background Task for Batch Processing
# ============================================================================

async def regenerate_embeddings_task(user_id: int, job_id: UUID, db: AsyncSession):
    """
    Background task to regenerate embeddings in batches with progress tracking.
    
    This runs asynchronously to avoid blocking the API request.
    Processes notes in chunks to prevent memory issues.
    Updates job progress in database after each batch.
    
    Args:
        user_id: User ID whose notes to regenerate
        job_id: Background job ID for tracking progress
        db: Database session
    """
    batch_size = 100
    offset = 0
    total_processed = 0
    total_failed = 0
    
    embedding_service = get_embedding_service()
    
    try:
        # Get the job record
        result = await db.execute(
            select(BackgroundJob).where(BackgroundJob.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {job_id} not found for user {user_id}")
            return
        
        # Mark job as running
        job.mark_running()
        await db.commit()
        
        # Count total notes to process
        count_result = await db.execute(
            select(func.count(Note.id)).where(Note.user_id == user_id)
        )
        total_notes = count_result.scalar()
        job.total_items = total_notes
        await db.commit()
        
        logger.info(f"Starting embedding regeneration for user {user_id}: {total_notes} notes")
        
        while True:
            # Fetch notes in batches
            result = await db.execute(
                select(Note)
                .where(Note.user_id == user_id)
                .offset(offset)
                .limit(batch_size)
            )
            notes = result.scalars().all()
            
            if not notes:
                break  # No more notes to process
            
            # Process each note in the batch
            for note in notes:
                try:
                    if not note.content or not note.content.strip():
                        continue
                    
                    combined_text = embedding_service.combine_text_for_embedding(
                        content=note.content,
                        scripture_refs=note.scripture_refs,
                        tags=note.tags.split(',') if note.tags else None
                    )
                    
                    embedding = embedding_service.generate(combined_text)
                    note.embedding = embedding
                    total_processed += 1
                    
                except EmbeddingGenerationError as e:
                    logger.error(f"Failed to generate embedding for note {note.id}: {e}")
                    total_failed += 1
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error for note {note.id}: {e}", exc_info=True)
                    total_failed += 1
                    continue
            
            # Commit the batch and update progress
            await db.commit()
            job.update_progress(total_processed, total_failed)
            await db.commit()
            
            logger.info(f"Regeneration batch: processed {len(notes)} notes (offset {offset}), " +
                       f"total: {total_processed} succeeded, {total_failed} failed, " +
                       f"progress: {job.progress_percent}%")
            
            offset += batch_size
        
        # Mark job as completed
        job.mark_completed(result_data={
            "embeddings_generated": total_processed,
            "failed_notes": total_failed,
            "total_notes": total_notes
        })
        await db.commit()
        
        logger.info(f"Regeneration complete for job {job_id}: {total_processed} succeeded, {total_failed} failed")
        
    except Exception as e:
        logger.error(f"Batch regeneration error for job {job_id}: {e}", exc_info=True)
        
        # Mark job as failed
        try:
            if job:
                job.mark_failed(str(e))
                await db.commit()
        except:
            pass
        
        await db.rollback()


@router.post("/regenerate-embeddings", response_model=RegenerationStatusResponse)
async def regenerate_all_embeddings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger background regeneration of embeddings for all user's notes using ARQ worker.
    
    This is useful when:
    - Upgrading to a new embedding model
    - Fixing notes that don't have embeddings
    - After bulk note imports
    
    The operation runs in the ARQ worker (separate process) to avoid blocking the API.
    Returns a job_id that can be used to track progress via GET /jobs/{job_id}
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Status message with job_id for tracking progress
    """
    try:
        # Create a background job record
        job = BackgroundJob(
            user_id=current_user.id,
            job_type="embedding_regeneration",
            status="queued"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"Created regeneration job {job.job_id} for user {current_user.id}")
        
        # Create Redis pool and enqueue ARQ task
        redis_url_parts = settings.redis_url.replace("redis://", "").split(":")
        redis_host = redis_url_parts[0] if redis_url_parts else "localhost"
        redis_port = int(redis_url_parts[1]) if len(redis_url_parts) > 1 else 6379
        
        redis_settings = RedisSettings(host=redis_host, port=redis_port, database=0)
        redis = await create_pool(redis_settings)
        
        try:
            # Enqueue the ARQ task with correct queue name
            arq_job = await redis.enqueue_job(
                'regenerate_embeddings_arq',
                current_user.id,
                str(job.job_id),
                _queue_name="scribes:queue"  # Match the queue name in arq_config.py
            )
            
            logger.info(f"Enqueued ARQ job for regeneration: {arq_job.job_id if arq_job else 'None'}")
            
        finally:
            await redis.close()
        
        return RegenerationStatusResponse(
            message=f"Embedding regeneration has been queued. Track progress at GET /jobs/{job.job_id}",
            status="queued",
            task_id=str(job.job_id)
        )
        
    except Exception as e:
        logger.error(f"Failed to queue regeneration task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue regeneration: {str(e)}"
        )
