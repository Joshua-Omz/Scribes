"""
Note API routes.
Handles note CRUD operations and search functionality.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.schemas.note_schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    NoteSearchRequest
)
from app.schemas.auth_schemas import MessageResponse
from app.services.note_service import NoteService


router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post(
    "/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Create a new sermon or study note with optional metadata."
)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> NoteResponse:
    """
    Create a new note.
    
    - **title**: Note title (required, 1-255 chars)
    - **content**: Note content (required, markdown supported)
    - **preacher**: Preacher name (optional)
    - **tags**: Comma-separated tags (optional)
    - **scripture_refs**: Scripture references (optional)
    
    Returns the created note with timestamps.
    """
    note_service = NoteService(db)
    note = await note_service.create_note(note_data, current_user.id)
    
    return NoteResponse.model_validate(note)


@router.get(
    "/",
    response_model=NoteListResponse,
    summary="Get all notes",
    description="Get paginated list of all notes for the current user."
)
async def get_notes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> NoteListResponse:
    """
    Get all notes for the current user with pagination.
    
    - **page**: Page number (default: 1)
    - **page_size**: Number of items per page (default: 20, max: 100)
    
    Returns paginated list of notes ordered by most recently updated.
    """
    note_service = NoteService(db)
    notes_response = await note_service.get_user_notes(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return notes_response


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a single note",
    description="Get detailed information about a specific note."
)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> NoteResponse:
    """
    Get a single note by ID.
    
    - **note_id**: ID of the note to retrieve
    
    Returns the note if it belongs to the current user.
    Raises 404 if not found or unauthorized.
    """
    note_service = NoteService(db)
    note = await note_service.get_note(note_id, current_user.id)
    
    return NoteResponse.model_validate(note)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update an existing note. Only provided fields will be updated."
)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> NoteResponse:
    """
    Update a note.
    
    - **note_id**: ID of the note to update
    - **note_data**: Fields to update (only provided fields will be changed)
    
    Returns the updated note.
    Raises 404 if not found or unauthorized.
    """
    note_service = NoteService(db)
    note = await note_service.update_note(note_id, note_data, current_user.id)
    
    return NoteResponse.model_validate(note)


@router.delete(
    "/{note_id}",
    response_model=MessageResponse,
    summary="Delete a note",
    description="Permanently delete a note and all associated data."
)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """
    Delete a note.
    
    - **note_id**: ID of the note to delete
    
    This will permanently delete the note and all associated:
    - Reminders
    - Cross-references
    - Annotations
    - Shared circle associations
    
    Returns success message.
    Raises 404 if not found or unauthorized.
    """
    note_service = NoteService(db)
    await note_service.delete_note(note_id, current_user.id)
    
    return MessageResponse(
        message="Note deleted successfully",
        detail=f"Note ID {note_id} has been permanently deleted"
    )


@router.post(
    "/search",
    response_model=NoteListResponse,
    summary="Search notes",
    description="Search and filter notes with various criteria."
)
async def search_notes(
    search_params: NoteSearchRequest,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> NoteListResponse:
    """
    Search notes with filters.
    
    - **query**: Search in title and content (optional)
    - **tags**: Filter by tags (optional)
    - **preacher**: Filter by preacher name (optional)
    - **scripture_ref**: Filter by scripture reference (optional)
    - **date_from**: Filter notes from this date (ISO format, optional)
    - **date_to**: Filter notes up to this date (ISO format, optional)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Returns paginated list of matching notes.
    
    Example search:
    ```json
    {
        "query": "grace salvation",
        "tags": "grace, mercy",
        "date_from": "2025-01-01"
    }
    ```
    """
    note_service = NoteService(db)
    notes_response = await note_service.search_notes(
        user_id=current_user.id,
        search_params=search_params,
        page=page,
        page_size=page_size
    )
    
    return notes_response
