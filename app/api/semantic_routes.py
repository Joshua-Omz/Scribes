"""
Semantic search routes for AI-powered note discovery.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.models.note_model import Note
from app.schemas.note_schemas import NoteResponse
from app.services.embedding_service import get_embedding_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/semantic", tags=["Semantic Search"])


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score (0-1)")


class SemanticSearchResult(BaseModel):
    """Single search result with similarity score."""
    note: NoteResponse
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    results: List[SemanticSearchResult]
    query: str
    total_results: int


class EmbeddingStatusResponse(BaseModel):
    """Response for embedding status check."""
    total_notes: int
    notes_with_embeddings: int
    notes_without_embeddings: int
    coverage_percentage: float
    model_info: dict


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    search_request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform semantic search across user's notes.
    
    This endpoint uses AI embeddings to find notes by meaning, not just keywords.
    For example, searching for "faith" will also find notes about "trust", "belief", etc.
    
    Args:
        search_request: Search parameters including query and filters
        db: Database session
        current_user: Authenticated user
        
    Returns:
        SemanticSearchResponse with matching notes and similarity scores
    """
    try:
        # Generate embedding for the search query
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate(search_request.query)
        
        if not query_embedding or all(v == 0.0 for v in query_embedding):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate embedding for query"
            )
        
        # Perform vector similarity search using pgvector
        # Using cosine distance operator: <=>
        # Lower distance = higher similarity
        query_sql = text("""
            SELECT 
                id, user_id, title, content, preacher, tags, scripture_refs,
                created_at, updated_at,
                1 - (embedding <=> :query_vec) AS similarity
            FROM notes
            WHERE user_id = :user_id
                AND embedding IS NOT NULL
                AND 1 - (embedding <=> :query_vec) >= :min_similarity
            ORDER BY embedding <=> :query_vec
            LIMIT :limit
        """)
        
        result = await db.execute(
            query_sql,
            {
                "query_vec": query_embedding,  # Pass the vector directly, not as string
                "user_id": current_user.id,
                "min_similarity": search_request.min_similarity,
                "limit": search_request.limit
            }
        )
        
        rows = result.fetchall()
        
        # Build response
        search_results = []
        for row in rows:
            # Create Note object from row
            note = Note(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                content=row.content,
                preacher=row.preacher,
                tags=row.tags,
                scripture_refs=row.scripture_refs,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            
            search_results.append(
                SemanticSearchResult(
                    note=NoteResponse.model_validate(note),
                    similarity_score=float(row.similarity)
                )
            )
        
        return SemanticSearchResponse(
            results=search_results,
            query=search_request.query,
            total_results=len(search_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get("/similar/{note_id}", response_model=SemanticSearchResponse)
async def find_similar_notes(
    note_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    min_similarity: float = Query(default=0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find notes similar to a specific note.
    
    This helps discover related sermon notes based on semantic similarity.
    Useful for building a knowledge graph and finding connections.
    
    Args:
        note_id: ID of the source note
        limit: Maximum number of similar notes to return
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
        
        if not source_note.embedding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source note does not have an embedding. Please update the note to generate one."
            )
        
        # Find similar notes
        query_sql = text("""
            SELECT 
                id, user_id, title, content, preacher, tags, scripture_refs,
                created_at, updated_at,
                1 - (embedding <=> :source_embedding) AS similarity
            FROM notes
            WHERE user_id = :user_id
                AND id != :source_note_id
                AND embedding IS NOT NULL
                AND 1 - (embedding <=> :source_embedding) >= :min_similarity
            ORDER BY embedding <=> :source_embedding
            LIMIT :limit
        """)
        
        result = await db.execute(
            query_sql,
            {
                "source_embedding": source_note.embedding,  # Pass the vector directly, not as string
                "user_id": current_user.id,
                "source_note_id": note_id,
                "min_similarity": min_similarity,
                "limit": limit
            }
        )
        
        rows = result.fetchall()
        
        # Build response
        search_results = []
        for row in rows:
            note = Note(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                content=row.content,
                preacher=row.preacher,
                tags=row.tags,
                scripture_refs=row.scripture_refs,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            
            search_results.append(
                SemanticSearchResult(
                    note=NoteResponse.model_validate(note),
                    similarity_score=float(row.similarity)
                )
            )
        
        return SemanticSearchResponse(
            results=search_results,
            query=f"Similar to: {source_note.title}",
            total_results=len(search_results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar notes search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar notes search failed: {str(e)}"
        )


@router.get("/status", response_model=EmbeddingStatusResponse)
async def get_embedding_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check the status of embeddings for the current user's notes.
    
    Returns statistics about how many notes have embeddings generated.
    This helps monitor the embedding generation process.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        EmbeddingStatusResponse with embedding coverage statistics
    """
    try:
        # Count total notes
        total_result = await db.execute(
            select(Note).where(Note.user_id == current_user.id)
        )
        total_notes = len(total_result.scalars().all())
        
        # Count notes with embeddings
        with_embeddings_result = await db.execute(
            select(Note).where(
                Note.user_id == current_user.id,
                Note.embedding.isnot(None)
            )
        )
        notes_with_embeddings = len(with_embeddings_result.scalars().all())
        
        # Calculate statistics
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
        logger.error(f"Embedding status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding status: {str(e)}"
        )


@router.post("/regenerate-embeddings")
async def regenerate_all_embeddings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Regenerate embeddings for all user's notes.
    
    This is useful when:
    - Upgrading to a new embedding model
    - Fixing notes that don't have embeddings
    - After bulk note imports
    
    ⚠️ This operation can take time for large note collections.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Status message with number of notes processed
    """
    try:
        # Get all user's notes
        result = await db.execute(
            select(Note).where(Note.user_id == current_user.id)
        )
        notes = result.scalars().all()
        
        if not notes:
            return {
                "message": "No notes found",
                "notes_processed": 0
            }
        
        # Generate embeddings
        embedding_service = get_embedding_service()
        processed_count = 0
        
        for note in notes:
            try:
                combined_text = embedding_service.combine_text_for_embedding(
                    
                    content=note.content,
                    
                    scripture_refs=note.scripture_refs,
                    tags=note.tags.split(',') if note.tags else None
                )
                
                embedding = embedding_service.generate(combined_text)
                note.embedding = embedding
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to generate embedding for note {note.id}: {e}")
                continue
        
        await db.commit()
        
        return {
            "message": f"Successfully regenerated embeddings for {processed_count} notes",
            "notes_processed": processed_count,
            "total_notes": len(notes)
        }
        
    except Exception as e:
        logger.error(f"Batch embedding regeneration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate embeddings: {str(e)}"
        )
