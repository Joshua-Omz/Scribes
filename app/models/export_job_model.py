"""Export job model.

This module defines the ExportJob database model for tracking export tasks.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ExportJob(Base):
    """Export job database model for async export task management."""
    
    __tablename__ = "export_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=True)  # Null if exporting multiple notes
    
    # Export configuration
    export_format = Column(String(20), nullable=False)  # pdf, markdown, docx, etc.
    export_type = Column(String(50), nullable=False)    # single_note, multiple_notes, all_notes, circle_notes
    
    # Job status
    status = Column(
        Enum("pending", "processing", "completed", "failed", name="export_status_types"),
        default="pending",
        nullable=False
    )
    
    # File information
    file_path = Column(String(500), nullable=True)  # Path to generated file
    file_url = Column(String(500), nullable=True)   # URL to download file
    file_size = Column(Integer, nullable=True)      # File size in bytes
    
    # Error tracking
    error_message = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="export_jobs")
    note = relationship("Note", back_populates="export_jobs")
