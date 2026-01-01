"""Cross reference model.

This module defines the CrossRef database model for note cross-references.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CrossRef(Base):
    """Cross reference database model for linking related notes."""
    
    __tablename__ = "cross_refs"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    other_note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    
    # Reference metadata
    reference_type = Column(String(50), default="related")  # related, references, cited_by, etc.
    description = Column(String(500), nullable=True)  # Optional description of the relationship
    
    # AI-generated or manual
    is_auto_generated = Column(String(20), default="manual")  # manual, ai_suggested, ai_auto
    confidence_score = Column(Integer, nullable=True)  # 0-100 confidence for AI suggestions
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    note = relationship("Note", foreign_keys=[note_id], back_populates="outgoing_refs")
    other_note = relationship("Note", foreign_keys=[other_note_id], back_populates="incoming_refs")
