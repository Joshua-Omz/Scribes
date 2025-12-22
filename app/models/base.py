"""
Base model class with common fields and utilities.
All database models should inherit from this base.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func

from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base model with common fields for all tables.
    Includes id, created_at, and updated_at timestamps.
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when record was last updated"
    )
    
    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation of model."""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"
