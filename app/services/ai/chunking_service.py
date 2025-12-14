"""
Chunking service for splitting notes into token-aware chunks.

This service splits long notes into smaller chunks suitable for:
- Embedding generation (stays within model limits)
- Semantic search (more precise retrieval)
- LLM context windows (prevents truncation)

Uses TokenizerService for accurate token counting.
"""

from typing import List, Dict, Any
import logging

from app.services.ai.tokenizer_service import get_tokenizer_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Service for chunking notes with token awareness.
    
    Splits note content into overlapping chunks where each chunk:
    - Fits within the embedding model's token limit
    - Overlaps with neighbors to preserve context
    - Maintains semantic coherence
    """
    
    def __init__(self):
        """Initialize chunking service with tokenizer."""
        self.tokenizer_service = get_tokenizer_service()
        self.default_chunk_size = settings.assistant_chunk_size  # 384 tokens
        self.default_overlap = settings.assistant_chunk_overlap  # 64 tokens
        logger.info(
            f"ChunkingService initialized "
            f"(chunk_size={self.default_chunk_size}, overlap={self.default_overlap})"
        )
    
    def chunk_note(
        self,
        note_content: str,
        chunk_size: int = None,
        overlap: int = None,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split note content into overlapping chunks with metadata.
        
        Args:
            note_content: The full note text to chunk
            chunk_size: Target tokens per chunk (default from config)
            overlap: Token overlap between chunks (default from config)
            metadata: Optional metadata to attach to each chunk (e.g., note_id, title)
            
        Returns:
            List of chunk dictionaries with structure:
            {
                "chunk_idx": 0,
                "chunk_text": "...",
                "token_count": 384,
                "metadata": {...}  # If provided
            }
            
        Example:
            >>> chunking_service = ChunkingService()
            >>> chunks = chunking_service.chunk_note(
            ...     "Long sermon note...",
            ...     metadata={"note_id": 123, "title": "Faith"}
            ... )
            >>> len(chunks)
            5
            >>> chunks[0]["chunk_idx"]
            0
            >>> chunks[0]["token_count"] <= 384
            True
        """
        # Use defaults if not specified
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap
        metadata = metadata or {}
        
        # Validate inputs
        if not note_content or not note_content.strip():
            logger.warning("Empty note content provided for chunking")
            return []
        
        if chunk_size <= overlap:
            raise ValueError(f"chunk_size ({chunk_size}) must be greater than overlap ({overlap})")
        
        # Use tokenizer to split text
        chunk_texts = self.tokenizer_service.chunk_text(
            text=note_content,
            chunk_size=chunk_size,
            overlap=overlap
        )
        
        # Build result with metadata
        chunks = []
        for idx, chunk_text in enumerate(chunk_texts):
            chunk_token_count = self.tokenizer_service.count_tokens(chunk_text)
            
            chunk_data = {
                "chunk_idx": idx,
                "chunk_text": chunk_text,
                "token_count": chunk_token_count,
            }
            
            # Add metadata if provided
            if metadata:
                chunk_data["metadata"] = metadata
            
            chunks.append(chunk_data)
        
        logger.info(
            f"Chunked note into {len(chunks)} chunks "
            f"(original: {len(note_content)} chars, "
            f"{self.tokenizer_service.count_tokens(note_content)} tokens)"
        )
        
        return chunks
    
    def chunk_notes_batch(
        self,
        notes: List[Dict[str, Any]],
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple notes in batch.
        
        Args:
            notes: List of note dictionaries with at minimum:
                   {"id": int, "content": str, "title": str (optional)}
            chunk_size: Target tokens per chunk
            overlap: Token overlap between chunks
            
        Returns:
            Flat list of all chunks from all notes, each with note metadata
            
        Example:
            >>> notes = [
            ...     {"id": 1, "content": "Note 1...", "title": "Faith"},
            ...     {"id": 2, "content": "Note 2...", "title": "Hope"}
            ... ]
            >>> all_chunks = chunking_service.chunk_notes_batch(notes)
            >>> # Returns chunks from both notes with note_id metadata
        """
        all_chunks = []
        
        for note in notes:
            note_id = note.get("id")
            note_content = note.get("content", "")
            
            if not note_content:
                logger.warning(f"Skipping note {note_id}: empty content")
                continue
            
            # Build metadata from note
            metadata = {
                "note_id": note_id,
                "title": note.get("title"),
                "preacher": note.get("preacher"),
                "tags": note.get("tags"),
                "scripture_refs": note.get("scripture_refs"),
            }
            
            # Chunk the note
            note_chunks = self.chunk_note(
                note_content=note_content,
                chunk_size=chunk_size,
                overlap=overlap,
                metadata=metadata
            )
            
            all_chunks.extend(note_chunks)
        
        logger.info(f"Batch chunked {len(notes)} notes into {len(all_chunks)} total chunks")
        return all_chunks
    
    def should_chunk(self, note_content: str, threshold_tokens: int = None) -> bool:
        """
        Check if a note needs chunking based on token count.
        
        Args:
            note_content: Note text
            threshold_tokens: Token threshold (default: chunk_size from config)
            
        Returns:
            True if note should be chunked, False if it fits in one chunk
            
        Example:
            >>> short_note = "Brief note"
            >>> chunking_service.should_chunk(short_note)
            False
            >>> long_note = "Very long sermon..." * 1000
            >>> chunking_service.should_chunk(long_note)
            True
        """
        threshold = threshold_tokens or self.default_chunk_size
        token_count = self.tokenizer_service.count_tokens(note_content)
        return token_count > threshold
    
    def estimate_chunk_count(self, note_content: str, chunk_size: int = None) -> int:
        """
        Estimate how many chunks a note will produce.
        
        Args:
            note_content: Note text
            chunk_size: Target chunk size in tokens
            
        Returns:
            Estimated number of chunks
        """
        chunk_size = chunk_size or self.default_chunk_size
        overlap = self.default_overlap
        
        total_tokens = self.tokenizer_service.count_tokens(note_content)
        
        if total_tokens <= chunk_size:
            return 1
        
        # Calculate chunks with overlap
        stride = chunk_size - overlap
        return (total_tokens - chunk_size) // stride + 1


# Global singleton
_chunking_service = None


def get_chunking_service() -> ChunkingService:
    """
    Get or create global ChunkingService instance.
    
    Returns:
        ChunkingService singleton
    """
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service

