"""
Note service - Business logic for note operations.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.note_model import Note
from app.repositories.note_repository import NoteRepository
from app.schemas.note_schemas import (
    NoteCreate, 
    NoteUpdate, 
    NoteResponse,
    NoteListResponse,
    NoteSearchRequest
)
from app.services.ai.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class NoteService:
    """Service for note operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize note service."""
        self.db = db
        self.note_repo = NoteRepository(db)
        self.embedding_service = get_embedding_service()
    
    async def _generate_embedding(self, note: Note) -> None:
        """
        Generate and set embedding for a note.
        
        Args:
            note: Note object to generate embedding for
        """ 
        try:
            # Combine note fields for rich semantic representation
            combined_text = self.embedding_service.combine_text_for_embedding(
                content=note.content,
                scripture_refs=note.scripture_refs,
                tags=note.tags.split(',') if note.tags else None
            )
            
            # Generate embedding
            embedding = self.embedding_service.generate(combined_text)
            note.embedding = embedding
            
            logger.info(f"Generated embedding for note {note.id}")
        except Exception as e:
            logger.error(f"Failed to generate embedding for note {note.id}: {e}")
            # Don't fail the operation if embedding generation fails
            note.embedding = None
    
    async def create_note(self, note_data: NoteCreate, user_id: int) -> Note:
        """
        Create a new note.
        
        Args:
            note_data: Note creation data
            user_id: ID of the user creating the note
            
        Returns:
            Note: Created note object
            
        Raises:
            HTTPException: If validation fails
        """
        # Additional business logic validation
        if not note_data.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty"
            )
        
        if not note_data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty"
            )
        
        # Create note
        note = await self.note_repo.create(note_data, user_id)
        # Generate embedding
        await self._generate_embedding(note)
        await self.db.flush()
        await self.db.refresh(note)
        await self.db.commit()
        logger.info(f"Created note {note.id} with embedding: {note.embedding is not None}")
        return note
    
    async def get_note(self, note_id: int, user_id: int) -> Note:
        """
        Get a single note by ID.
        
        Args:
            note_id: Note ID
            user_id: User ID for ownership verification
            
        Returns:
            Note: Note object
            
        Raises:
            HTTPException: If note not found or unauthorized
        """
        note = await self.note_repo.get_by_user_and_id(note_id, user_id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found or you don't have permission to access it"
            )
        
        return note
    
    async def get_user_notes(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> NoteListResponse:
        """
        Get all notes for a user with pagination.
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            NoteListResponse: Paginated list of notes
            
        Raises:
            HTTPException: If pagination parameters are invalid
        """
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        # Calculate offset
        skip = (page - 1) * page_size
        
        # Get notes and total count
        notes = await self.note_repo.get_all_by_user(user_id, skip=skip, limit=page_size)
        total = await self.note_repo.count_by_user(user_id)
        
        # Convert to response schemas
        note_responses = [NoteResponse.model_validate(note) for note in notes]
        
        return NoteListResponse(
            items=note_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def update_note(
        self, 
        note_id: int, 
        note_data: NoteUpdate, 
        user_id: int
    ) -> Note:
        """
        Update a note.
        
        Args:
            note_id: Note ID
            note_data: Note update data
            user_id: User ID for ownership verification
            
        Returns:
            Note: Updated note object
            
        Raises:
            HTTPException: If note not found or unauthorized
        """
        # Verify ownership first
        existing_note = await self.get_note(note_id, user_id)
        
        # Validate update data
        update_dict = note_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Additional validation for non-empty strings
        if "title" in update_dict and not update_dict["title"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty"
            )
        
        if "content" in update_dict and not update_dict["content"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty"
            )
        
        # Update note
        updated_note = await self.note_repo.update(note_id, note_data)
        
        if not updated_note:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update note"
            )
        
        # Regenerate embedding if content-related fields were updated
        content_fields = {'title', 'content', 'preacher', 'scripture_refs', 'tags'}
        if any(field in update_dict for field in content_fields):
            await self._generate_embedding(updated_note)
        
        await self.db.commit()
        
        return updated_note
    
    async def delete_note(self, note_id: int, user_id: int) -> bool:
        """
        Delete a note.
        
        Args:
            note_id: Note ID
            user_id: User ID for ownership verification
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            HTTPException: If note not found or unauthorized
        """
        # Verify ownership first
        await self.get_note(note_id, user_id)
        
        # Delete note
        deleted = await self.note_repo.delete(note_id)
        await self.db.commit()
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete note"
            )
        
        return True
    
    async def search_notes(
        self,
        user_id: int,
        search_params: NoteSearchRequest,
        page: int = 1,
        page_size: int = 20
    ) -> NoteListResponse:
        """
        Search notes with filters.
        
        Args:
            user_id: User ID
            search_params: Search parameters
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            NoteListResponse: Paginated list of matching notes
            
        Raises:
            HTTPException: If search parameters are invalid
        """
        # Validate pagination
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        # Parse date filters if provided
        date_from = None
        date_to = None
        
        if search_params.date_from:
            try:
                date_from = datetime.fromisoformat(search_params.date_from)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use ISO format (YYYY-MM-DD)"
                )
        
        if search_params.date_to:
            try:
                date_to = datetime.fromisoformat(search_params.date_to)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use ISO format (YYYY-MM-DD)"
                )
        
        # Calculate offset
        skip = (page - 1) * page_size
        
        # Search notes
        notes = await self.note_repo.search(
            user_id=user_id,
            query=search_params.query,
            tags=search_params.tags,
            preacher=search_params.preacher,
            scripture_ref=search_params.scripture_ref,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=page_size
        )
        
        # Get total count
        total = await self.note_repo.count_search(
            user_id=user_id,
            query=search_params.query,
            tags=search_params.tags,
            preacher=search_params.preacher,
            scripture_ref=search_params.scripture_ref,
            date_from=date_from,
            date_to=date_to
        )
        
        # Convert to response schemas
        note_responses = [NoteResponse.model_validate(note) for note in notes]
        
        return NoteListResponse(
            items=note_responses,
            total=total,
            page=page,
            page_size=page_size
        )
