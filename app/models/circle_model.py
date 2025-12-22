from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship 
from app.core.database import Base    

class Circle(Base): 
    __tablename__ = "circles"  # Fixed typo in tablename

    id = Column(Integer, primary_key=True, index=True)  
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)      
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_private = Column(Boolean, default=False)

    # Relationships
    owner = relationship("User", back_populates="owned_circles")
    members = relationship("CircleMember", cascade="all, delete-orphan", back_populates="circle")
    circle_notes = relationship("CircleNote", back_populates="circle", cascade="all, delete-orphan")


class CircleMember(Base):
    __tablename__ = "circle_members"

    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("circles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum("owner", "admin", "member", name="member_role_types"), default="member", nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum("invited", "active", "inactive", name="member_status_types"), default="active", nullable=False)

    # Relationships
    circle = relationship("Circle", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="circle_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # Add unique constraint to prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('circle_id', 'user_id', name='unique_circle_membership'),
    )


class CircleNote(Base):
    __tablename__ = "circle_notes"

    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("circles.id", ondelete="CASCADE"), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    shared_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    circle = relationship("Circle", back_populates="circle_notes")
    note = relationship("Note", back_populates="shared_circles")
    
    # Add unique constraint to prevent duplicate note sharing
    __table_args__ = (
        UniqueConstraint('circle_id', 'note_id', name='unique_circle_note'),
    )
    