"""User model.

This module defines the User database model for authentication.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user")  # "user" or "admin"
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Email verification status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    notes = relationship("Note", back_populates="user", cascade="all, delete")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete")
    owned_circles = relationship("Circle", back_populates="owner", foreign_keys="Circle.owner_id")
    circle_memberships = relationship("CircleMember", back_populates="user", foreign_keys="CircleMember.user_id", cascade="all, delete")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete")
    annotations = relationship("Annotation", back_populates="user", cascade="all, delete")
    export_jobs = relationship("ExportJob", back_populates="user", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")