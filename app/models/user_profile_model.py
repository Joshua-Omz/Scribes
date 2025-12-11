"""User profile model.

This module defines the UserProfile database model for extended user information.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserProfile(Base):
    """User profile database model for extended user information."""
    
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Extended profile fields
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    phone_number = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Preferences (can be expanded)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to User
    user = relationship("User", back_populates="profile")
