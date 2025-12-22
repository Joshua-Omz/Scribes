
"""
Retrieval service for semantic search over note chunks.

Performs vector similarity search with user isolation.
Separates high and low relevance chunks for different uses.
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant note chunks via vector similarity.
    
    Features:
    - User-scoped vector search (security)
    - Separates high/low relevance chunks
    - Returns note metadata for citations
    """
    
    def __init__(self):
        """Initialize retrieval service."""
        self.relevance_threshold = 0.15  # Adjusted for sentence-transformer Q&A matching (lower than statement-to-statement)
        logger.info(
            f"RetrievalService initialized "
            f"(relevance_threshold={self.relevance_threshold})"
        )
    
    async def retrieve_top_chunks(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        user_id: int,
        top_k: int = settings.assistant_top_k   
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieve top-k most relevant chunks for a query.
        
        SECURITY: Only retrieves chunks from notes owned by user_id.
        
        Args:
            db: Database session
            query_embedding: Query vector (384-dim)
            user_id: Current user's ID (for isolation)
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (high_relevance_chunks, low_relevance_chunks)
            Each chunk dict contains:
            {
                "chunk_id": int,
                "note_id": int,
                "chunk_idx": int,
                "chunk_text": str,
                "relevance_score": float (0-1, higher is better),
                "note_title": str,
                "note_created_at": datetime,
                "preacher": str,
                "scripture_refs": str,
                "tags": str
            }
            
        Raises:
            ValueError: If inputs invalid
            Exception: If DB error occurs
        """
        # Input validation
        if not query_embedding or len(query_embedding) != settings.assistant_embedding_dim:
            raise ValueError(
                f"Invalid query_embedding: expected {settings.assistant_embedding_dim} dimensions, "
                f"got {len(query_embedding) if query_embedding else 0}"
            )
        
        if user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")
        
        if top_k <= 0 or top_k > 200:
            raise ValueError(f"Invalid top_k: {top_k} (must be 1-200)")
        
        logger.info(f"Retrieving top-{top_k} chunks for user {user_id}")
        
        # SQL query with user isolation
        query_sql = text("""
            SELECT 
                nc.id as chunk_id,
                nc.note_id,
                nc.chunk_idx,
                nc.chunk_text,
                1 - (nc.embedding <-> :query_vec) as relevance_score,
                n.title as note_title,
                n.created_at as note_created_at,
                n.preacher,
                n.scripture_refs,
                n.tags
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE 
                n.user_id = :user_id
                AND nc.embedding IS NOT NULL
            ORDER BY nc.embedding <-> :query_vec
            LIMIT :top_k
        """)
        
        try:
            # Execute query
            # Note: pgvector with asyncpg requires string format for vector parameters
            result = await db.execute(
                query_sql,
                {
                    "query_vec": str(query_embedding),
                    "user_id": user_id,
                    "top_k": top_k
                }
            )
            
            rows = result.fetchall()
            
            if not rows:
                logger.warning(
                    f"No chunks found for user {user_id}. "
                    f"User may have no notes with embeddings."
                )
                return [], []
            
            # Convert rows to dicts
            all_chunks = []
            for row in rows:
                chunk_dict = {
                    "chunk_id": row.chunk_id,
                    "note_id": row.note_id,
                    "chunk_idx": row.chunk_idx,
                    "chunk_text": row.chunk_text,
                    "relevance_score": float(row.relevance_score),
                    "note_title": row.note_title,
                    "note_created_at": row.note_created_at,
                    "preacher": row.preacher,
                    "scripture_refs": row.scripture_refs,
                    "tags": row.tags
                }
                all_chunks.append(chunk_dict)
            
            # Separate high and low relevance chunks
            high_relevance = [
                c for c in all_chunks 
                if c["relevance_score"] >= self.relevance_threshold
            ]
            low_relevance = [
                c for c in all_chunks 
                if c["relevance_score"] < self.relevance_threshold
            ]
            
            logger.info(
                f"Retrieved {len(all_chunks)} chunks for user {user_id}: "
                f"{len(high_relevance)} high relevance, {len(low_relevance)} low relevance"
            )
            
            return high_relevance, low_relevance
            
        except Exception as e:
            logger.error(f"Error retrieving chunks for user {user_id}: {e}", exc_info=True)
            raise Exception(f"Database error during chunk retrieval: {str(e)}")
    
    def set_relevance_threshold(self, threshold: float):
        """
        Update the relevance threshold for separating high/low relevance.
        
        Args:
            threshold: Score threshold (0-1). Scores >= threshold are "high relevance"
        """
        if not 0 <= threshold <= 1:
            raise ValueError(f"Threshold must be 0-1, got {threshold}")
        
        self.relevance_threshold = threshold
        logger.info(f"Relevance threshold updated to {threshold}")


# Singleton
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """Get or create retrieval service singleton."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service