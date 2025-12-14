"""
Context builder for assembling LLM context from retrieved chunks.

Fits chunks into token budget while preserving attribution.
"""

from typing import List, Dict, Any
import logging

from app.services.ai.tokenizer_service import get_tokenizer_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds context text from retrieved chunks within a token budget.
    
    Features:
    - Fits chunks into token budget (greedy best-first)
    - Formats chunks with source attribution
    - Tracks what was used vs. skipped
    - Stores low-relevance chunks in metadata
    """
    
    def __init__(self):
        """Initialize context builder."""
        self.tokenizer = get_tokenizer_service()
        self.default_budget = settings.assistant_max_context_tokens  # 1200
        
        logger.info(
            f"ContextBuilder initialized (default_budget={self.default_budget} tokens)"
        )
    
    def build_context(
        self,
        high_relevance_chunks: List[Dict[str, Any]],
        low_relevance_chunks: List[Dict[str, Any]],
        token_budget: int = None
    ) -> Dict[str, Any]:
        """
        Build context text from chunks within token budget.
        
        Strategy:
        1. Sort high_relevance chunks by score (descending)
        2. Add chunks one-by-one until budget reached
        3. Format each chunk with source attribution
        4. Store low_relevance chunks in metadata (for future use)
        
        Args:
            high_relevance_chunks: Chunks with score >= 0.6
            low_relevance_chunks: Chunks with score < 0.6
            token_budget: Max tokens for context (default: 1200)
            
        Returns:
            {
                "context_text": str,  # Formatted context for LLM
                "chunks_used": List[Dict],  # Chunks that fit in budget
                "chunks_skipped": List[Dict],  # High-rel chunks that didn't fit
                "low_relevance_chunks": List[Dict],  # Stored for metadata
                "total_tokens": int,  # Actual tokens used
                "token_budget": int,  # Budget provided
                "truncated": bool,  # True if some high-rel chunks skipped
                "sources": List[Dict]  # Unique notes cited (for attribution)
            }
        """
        if token_budget is None:
            token_budget = self.default_budget
        
        logger.info(
            f"Building context from {len(high_relevance_chunks)} high-rel chunks, "
            f"{len(low_relevance_chunks)} low-rel chunks (budget={token_budget} tokens)"
        )
        
        # Handle edge case: no high-relevance chunks
        if not high_relevance_chunks:
            logger.warning("No high-relevance chunks provided. Returning empty context.")
            return {
                "context_text": "",
                "chunks_used": [],
                "chunks_skipped": [],
                "low_relevance_chunks": low_relevance_chunks,
                "total_tokens": 0,
                "token_budget": token_budget,
                "truncated": False,
                "sources": []
            }
        
        # Sort chunks by relevance score (descending - best first)
        sorted_chunks = sorted(
            high_relevance_chunks,
            key=lambda c: c["relevance_score"],
            reverse=True
        )
        
        # Build context greedily
        context_parts = []
        chunks_used = []
        current_tokens = 0
        
        for chunk in sorted_chunks:
            # Format this chunk with attribution
            formatted_chunk = self._format_chunk(chunk)
            chunk_tokens = self.tokenizer.count_tokens(formatted_chunk)
            
            # Check if adding this chunk would exceed budget
            if current_tokens + chunk_tokens > token_budget:
                logger.debug(
                    f"Chunk {chunk['chunk_id']} ({chunk_tokens} tokens) would exceed "
                    f"budget ({current_tokens + chunk_tokens} > {token_budget}). Stopping."
                )
                break
            
            # Add chunk to context
            context_parts.append(formatted_chunk)
            chunks_used.append(chunk)
            current_tokens += chunk_tokens
            
            logger.debug(
                f"Added chunk {chunk['chunk_id']} "
                f"(+{chunk_tokens} tokens, total={current_tokens}/{token_budget})"
            )
        
        # Combine all parts into final context
        context_text = "\n\n".join(context_parts)
        
        # Determine which chunks were skipped
        chunks_skipped = [
            c for c in sorted_chunks 
            if c not in chunks_used
        ]
        
        # Extract unique sources (notes) for attribution
        sources = self._extract_sources(chunks_used)
        
        result = {
            "context_text": context_text,
            "chunks_used": chunks_used,
            "chunks_skipped": chunks_skipped,
            "low_relevance_chunks": low_relevance_chunks,
            "total_tokens": current_tokens,
            "token_budget": token_budget,
            "truncated": len(chunks_skipped) > 0,
            "sources": sources
        }
        
        logger.info(
            f"Context built: {len(chunks_used)}/{len(sorted_chunks)} chunks used, "
            f"{current_tokens}/{token_budget} tokens, "
            f"truncated={result['truncated']}"
        )
        
        return result
    
    def _format_chunk(self, chunk: Dict[str, Any]) -> str:
        """
        Format a single chunk with source attribution.
        
        Format:
        ---
        Source: "Note Title" by Preacher Name (Scripture Reference)
        Relevance: 0.89
        Content:
        [chunk text]
        ---
        
        Args:
            chunk: Chunk dict from retrieval
            
        Returns:
            Formatted string
        """
        # Build source line
        source_parts = [f'"{chunk["note_title"]}"']
        
        if chunk.get("preacher"):
            source_parts.append(f"by {chunk['preacher']}")
        
        if chunk.get("scripture_refs"):
            source_parts.append(f"({chunk['scripture_refs']})")
        
        source_line = " ".join(source_parts)
        
        # Format chunk
        formatted = (
            f"---\n"
            f"Source: {source_line}\n"
            f"Relevance: {chunk['relevance_score']:.2f}\n"
            f"Content:\n"
            f"{chunk['chunk_text']}\n"
            f"---"
        )
        
        return formatted
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract unique note sources from chunks.
        
        Used for citation in response metadata.
        
        Args:
            chunks: List of chunks used in context
            
        Returns:
            List of unique sources:
            [
                {
                    "note_id": 123,
                    "note_title": "Sermon Title",
                    "preacher": "Pastor Name",
                    "scripture_refs": "John 3:16",
                    "chunk_count": 3  # How many chunks from this note
                }
            ]
        """
        # Group chunks by note_id
        notes_map = {}
        
        for chunk in chunks:
            note_id = chunk["note_id"]
            
            if note_id not in notes_map:
                notes_map[note_id] = {
                    "note_id": note_id,
                    "note_title": chunk["note_title"],
                    "preacher": chunk.get("preacher"),
                    "scripture_refs": chunk.get("scripture_refs"),
                    "tags": chunk.get("tags"),
                    "chunk_count": 0,
                    "chunk_indices": []
                }
            
            notes_map[note_id]["chunk_count"] += 1
            notes_map[note_id]["chunk_indices"].append(chunk["chunk_idx"])
        
        # Convert to list, sorted by chunk_count (most-cited first)
        sources = sorted(
            notes_map.values(),
            key=lambda s: s["chunk_count"],
            reverse=True
        )
        
        return sources
    
    def preview_context(
        self,
        high_relevance_chunks: List[Dict[str, Any]],
        max_chunks: int = 3
    ) -> str:
        """
        Preview what the context will look like (for debugging).
        
        Args:
            high_relevance_chunks: Chunks to preview
            max_chunks: Number of chunks to show
            
        Returns:
            Formatted preview string
        """
        sorted_chunks = sorted(
            high_relevance_chunks,
            key=lambda c: c["relevance_score"],
            reverse=True
        )
        
        preview_parts = []
        for i, chunk in enumerate(sorted_chunks[:max_chunks], 1):
            formatted = self._format_chunk(chunk)
            tokens = self.tokenizer.count_tokens(formatted)
            preview_parts.append(f"[Chunk {i}] ({tokens} tokens)\n{formatted}")
        
        if len(sorted_chunks) > max_chunks:
            preview_parts.append(f"\n... and {len(sorted_chunks) - max_chunks} more chunks")
        
        return "\n\n".join(preview_parts)


# Singleton
_context_builder = None


def get_context_builder() -> ContextBuilder:
    """Get or create context builder singleton."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder

