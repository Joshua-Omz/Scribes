"""Models for notes.     preacher = Column(String(100), nullable=True)  # optional field
    tags = Column(String(255), nullable=True)      # comma-separated tags
    scripture_refs = Column(String(255), nullable=True)  # e.g. "John 3:16, Matt 5:9"
    
    # Semantic embedding vector for AI features (384 dimensions from all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())s module defines the database models for notes."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime  
from sqlalchemy.orm import relationship 
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.core.database import Base    


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    preacher = Column(String(100), nullable=True)  # optional field
    tags = Column(String(255), nullable=True)      # comma-separated tags
    scripture_refs = Column(String(255), nullable=True)  # e.g. "John 3:16, Matt 5:9"
    
    # Semantic embedding vector for AI features
    embedding = Column(Vector(384), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship (optional but good for queries later)
    user = relationship("User", back_populates="notes")
    reminders = relationship("Reminder", back_populates="note", cascade="all, delete")
    shared_circles = relationship("CircleNote", back_populates="note", cascade="all, delete")
    # CrossRef relationships
    outgoing_refs = relationship("CrossRef", foreign_keys="CrossRef.note_id", back_populates="note", cascade="all, delete")
    incoming_refs = relationship("CrossRef", foreign_keys="CrossRef.other_note_id", back_populates="other_note", cascade="all, delete")
    # Annotations relationship
    annotations = relationship("Annotation", back_populates="note", cascade="all, delete")
    # Export jobs relationship
    export_jobs = relationship("ExportJob", back_populates="note", cascade="all, delete")