"""Notification model.

This module defines the Notification database model for user notifications.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Notification(Base):
    """Notification database model for user notification system."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Notification content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Notification type and priority
    notification_type = Column(
        Enum("info", "warning", "error", "success", "reminder", name="notification_types"),
        default="info",
        nullable=False
    )
    priority = Column(
        Enum("low", "medium", "high", name="priority_types"),
        default="medium",
        nullable=False
    )
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Optional link/action
    action_url = Column(String(500), nullable=True)  # URL to navigate when clicked
    
    # Extra data (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="notifications")
