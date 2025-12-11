"""Annotation model.

This module defines the Annotation database model for note annotations/highlights.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Annotation(Base):
    """Annotation database model for highlights and comments on notes."""
    
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    
    # Annotation content
    content = Column(Text, nullable=False)  # The annotation/comment text
    annotation_type = Column(String(50), default="comment")  # comment, highlight, note
    
    # Position/reference in the note (optional)
    start_position = Column(Integer, nullable=True)  # Character position where highlight starts
    end_position = Column(Integer, nullable=True)    # Character position where highlight ends
    highlighted_text = Column(Text, nullable=True)   # The text that was highlighted
    
    # Color/styling (optional)
    color = Column(String(20), nullable=True)  # For colored highlights
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="annotations")
    note = relationship("Note", back_populates="annotations")
