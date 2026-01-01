"""Background job model for tracking async task execution.

This module defines the BackgroundJob database model for tracking 
long-running background tasks like embedding regeneration, exports, etc.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class BackgroundJob(Base):
    """Background job database model for async task tracking."""
    
    __tablename__ = "background_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    job_type = Column(String(100), nullable=False)  # 'embedding_regeneration', 'export', 'reminder_batch', etc.
    
    # Status tracking
    # Possible values: 'queued', 'running', 'completed', 'failed', 'cancelled'
    status = Column(String(20), nullable=False, default="queued")
    
    # Progress tracking
    progress_percent = Column(Integer, default=0)
    total_items = Column(Integer, nullable=True)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # Results and errors
    result_data = Column(JSONB, nullable=True)  # Flexible JSON storage for job results
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="background_jobs")
    
    def __repr__(self):
        return f"<BackgroundJob(id={self.id}, job_id={self.job_id}, type={self.job_type}, status={self.status})>"
    
    def update_progress(self, processed: int, failed: int = 0):
        """Update progress counters and calculate percentage.
        
        Args:
            processed: Number of items successfully processed
            failed: Number of items that failed
        """
        self.processed_items = processed
        self.failed_items = failed
        
        if self.total_items and self.total_items > 0:
            total_done = processed + failed
            self.progress_percent = int((total_done / self.total_items) * 100)
        else:
            self.progress_percent = 0
    
    def mark_running(self):
        """Mark job as running and set started_at timestamp."""
        self.status = "running"
        self.started_at = func.now()
    
    def mark_completed(self, result_data: dict = None):
        """Mark job as completed successfully.
        
        Args:
            result_data: Optional dictionary of result data to store
        """
        self.status = "completed"
        self.completed_at = func.now()
        self.progress_percent = 100
        if result_data:
            self.result_data = result_data
    
    def mark_failed(self, error_message: str):
        """Mark job as failed with error message.
        
        Args:
            error_message: Description of the error
        """
        self.status = "failed"
        self.completed_at = func.now()
        self.error_message = error_message
