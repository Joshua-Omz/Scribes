"""
NoteChunk model for storing chunked note content with embeddings.

This model enables token-aware RAG by splitting large notes into smaller chunks,
each with its own embedding vector for more accurate semantic search.
"""

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class NoteChunk(Base):
    """
    Represents a chunk of a note with its own embedding vector.
    
    Notes are split into chunks to:
    - Stay within token limits for embeddings and LLM context windows
    - Improve retrieval accuracy (match specific sections, not whole notes)
    - Enable progressive loading and better user experience
    
    Attributes:
        id: Primary key
        note_id: Foreign key to parent note (cascade delete)
        chunk_idx: Index of this chunk within the note (0-based)
        chunk_text: The actual text content of this chunk
        embedding: 384-dimensional vector from all-MiniLM-L6-v2
        created_at: Timestamp when chunk was created
        updated_at: Timestamp when chunk was last updated
    """
    
    __tablename__ = "note_chunks"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_idx = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    
    # 384-dimensional embedding vector (matches all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to parent note
    note = relationship("Note", back_populates="chunks")
    
    def __repr__(self) -> str:
        return f"<NoteChunk(id={self.id}, note_id={self.note_id}, chunk_idx={self.chunk_idx})>"
    
    @property
    def token_count_estimate(self) -> int:
        """
        Rough estimate of token count (actual count requires tokenizer).
        Uses common heuristic: 1 token ≈ 4 characters.
        """
        return len(self.chunk_text) // 4

