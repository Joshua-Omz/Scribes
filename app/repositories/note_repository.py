"""
Note repository for database operations.
Data access layer for note-related queries.
"""

from typing import Optional, List
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.models.note_model import Note
from app.schemas.note_schemas import NoteCreate, NoteUpdate



logger = logging.getLogger(__name__)

class NoteRepository:
    """Repository for note database operations."""
    
    def __init__(self, db: AsyncSession, ):
        """Initialize repository with database session."""
        self.db = db

    
    async def create(self, note_data: NoteCreate, user_id: int) -> Note:
        """
        Create a new note in the database.
        
        Args:
            note_data: Note creation data
            user_id: ID of the user creating the note
            
        Returns:
            Note: Created note object
        """  
        note = Note(
            user_id=user_id,
            title=note_data.title,
            content=note_data.content,
            preacher=note_data.preacher,
            tags=note_data.tags,
            scripture_refs=note_data.scripture_refs,
        )
        
        self.db.add(note)
        logger.info(f"Created note object for user {user_id} (not yet flushed)")
        
        return note
    
    async def get_by_id(self, note_id: int) -> Optional[Note]:
        """
        Get note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Optional[Note]: Note object or None
        """
        result = await self.db.execute(
            select(Note).where(Note.id == note_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_and_id(self, note_id: int, user_id: int) -> Optional[Note]:
        """
        Get note by ID and verify ownership.
        
        Args:
            note_id: Note ID
            user_id: User ID for ownership verification
            
        Returns:
            Optional[Note]: Note object or None
        """
        result = await self.db.execute(
            select(Note).where(
                Note.id == note_id,
                Note.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Note]:
        """
        Get all notes for a user with pagination.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Note]: List of note objects
        """
        result = await self.db.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.updated_at.desc(), Note.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_user(self, user_id: int) -> int:
        """
        Count total notes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            int: Total count of notes
        """
        result = await self.db.execute(
            select(func.count(Note.id)).where(Note.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def update(self, note_id: int, note_data: NoteUpdate) -> Optional[Note]:
        """
        Update note information.
        
        Args:
            note_id: Note ID
            note_data: Note update data
            
        Returns:
            Optional[Note]: Updated note object or None
        """
        # Get update data excluding unset fields
        update_data = note_data.model_dump(exclude_unset=True)
        
        if not update_data:
            # No fields to update
            return await self.get_by_id(note_id)
        
        # Perform update
        await self.db.execute(
            update(Note)
            .where(Note.id == note_id)
            .values(**update_data)
        )
        await self.db.flush()
        
        # Return updated note
        return await self.get_by_id(note_id)
    
    async def delete(self, note_id: int) -> bool:
        """
        Delete a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        result = await self.db.execute(
            delete(Note).where(Note.id == note_id)
        )
        await self.db.flush()
        
        return result.rowcount > 0
    
    async def search(
        self,
        user_id: int,
        query: Optional[str] = None,
        tags: Optional[str] = None,
        preacher: Optional[str] = None,
        scripture_ref: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Note]:
        """
        Search notes with filters.
        
        Args:
            user_id: User ID
            query: Search query for title and content
            tags: Filter by tags
            preacher: Filter by preacher name
            scripture_ref: Filter by scripture reference
            date_from: Filter notes from this date
            date_to: Filter notes up to this date
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Note]: List of matching note objects
        """
        # Start with base query
        stmt = select(Note).where(Note.user_id == user_id)
        
        # Apply filters
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Note.title.ilike(search_pattern),
                    Note.content.ilike(search_pattern)
                )
            )
        
        if tags:
            stmt = stmt.where(Note.tags.ilike(f"%{tags}%"))
        
        if preacher:
            stmt = stmt.where(Note.preacher.ilike(f"%{preacher}%"))
        
        if scripture_ref:
            stmt = stmt.where(Note.scripture_refs.ilike(f"%{scripture_ref}%"))
        
        if date_from:
            stmt = stmt.where(Note.created_at >= date_from)
        
        if date_to:
            stmt = stmt.where(Note.created_at <= date_to)
        
        # Order and paginate
        stmt = stmt.order_by(
            Note.updated_at.desc(), 
            Note.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def count_search(
        self,
        user_id: int,
        query: Optional[str] = None,
        tags: Optional[str] = None,
        preacher: Optional[str] = None,
        scripture_ref: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> int:
        """
        Count notes matching search criteria.
        
        Args:
            user_id: User ID
            query: Search query for title and content
            tags: Filter by tags
            preacher: Filter by preacher name
            scripture_ref: Filter by scripture reference
            date_from: Filter notes from this date
            date_to: Filter notes up to this date
            
        Returns:
            int: Count of matching notes
        """
        # Start with base query
        stmt = select(func.count(Note.id)).where(Note.user_id == user_id)
        
        # Apply same filters as search
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Note.title.ilike(search_pattern),
                    Note.content.ilike(search_pattern)
                )
            )
        
        if tags:
            stmt = stmt.where(Note.tags.ilike(f"%{tags}%"))
        
        if preacher:
            stmt = stmt.where(Note.preacher.ilike(f"%{preacher}%"))
        
        if scripture_ref:
            stmt = stmt.where(Note.scripture_refs.ilike(f"%{scripture_ref}%"))
        
        if date_from:
            stmt = stmt.where(Note.created_at >= date_from)
        
        if date_to:
            stmt = stmt.where(Note.created_at <= date_to)
        
        result = await self.db.execute(stmt)
        return result.scalar() or 0
