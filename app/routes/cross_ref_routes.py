"""
Cross Reference API routes.
Endpoints for managing cross-references between notes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.repositories.cross_ref_repository import CrossRefRepository
from app.repositories.note_repository import NoteRepository
from app.services.business.cross_ref_service import CrossRefService
from app.schemas.cross_ref_schemas import (
    CrossRefCreate,
    CrossRefUpdate,
    CrossRefResponse,
    CrossRefWithNoteDetails,
    CrossRefListResponse,
    BulkCrossRefCreate,
    CrossRefSuggestion
)
from app.schemas.note_schemas import NoteResponse

router = APIRouter(prefix="/cross-refs", tags=["Cross References"])


def get_cross_ref_service(db: AsyncSession = Depends(get_db)) -> CrossRefService:
    """Dependency to get CrossRefService instance."""
    cross_ref_repo = CrossRefRepository(db)
    note_repo = NoteRepository(db)
    return CrossRefService(cross_ref_repo, note_repo)


@router.post(
    "/",
    response_model=CrossRefResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cross-reference",
    description="Create a cross-reference between two notes. Both notes must belong to the authenticated user."
)
async def create_cross_reference(
    cross_ref_data: CrossRefCreate,
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Create a new cross-reference between two notes."""
    cross_ref = await service.create_cross_ref(cross_ref_data, current_user.id)
    return CrossRefResponse.model_validate(cross_ref)


@router.post(
    "/bulk",
    response_model=List[CrossRefResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple cross-references",
    description="Create multiple cross-references at once. Can optionally skip errors to continue processing valid refs."
)
async def bulk_create_cross_references(
    bulk_data: BulkCrossRefCreate,
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Create multiple cross-references at once."""
    cross_refs = await service.bulk_create_cross_refs(bulk_data, current_user.id)
    return [CrossRefResponse.model_validate(ref) for ref in cross_refs]


@router.get(
    "/{cross_ref_id}",
    response_model=CrossRefWithNoteDetails,
    summary="Get a cross-reference by ID",
    description="Retrieve a specific cross-reference with note details."
)
async def get_cross_reference(
    cross_ref_id: int,
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Get a specific cross-reference by ID."""
    cross_ref_data = await service.get_cross_ref(cross_ref_id, current_user.id)
    return CrossRefWithNoteDetails(**cross_ref_data)


@router.get(
    "/note/{note_id}",
    response_model=CrossRefListResponse,
    summary="Get all cross-references for a note",
    description="Retrieve all cross-references (both incoming and outgoing) for a specific note."
)
async def get_note_cross_references(
    note_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Get all cross-references for a specific note."""
    cross_refs_data = await service.get_note_cross_refs(note_id, current_user.id, skip, limit)
    
    # Get count for pagination
    count_data = await service.get_cross_ref_count(note_id, current_user.id)
    
    return CrossRefListResponse(
        cross_refs=[CrossRefWithNoteDetails(**ref) for ref in cross_refs_data],
        total=count_data["total_cross_refs"],
        skip=skip,
        limit=limit
    )


@router.get(
    "/note/{note_id}/outgoing",
    response_model=List[CrossRefWithNoteDetails],
    summary="Get outgoing cross-references",
    description="Retrieve only outgoing cross-references from a note (references this note makes to other notes)."
)
async def get_outgoing_cross_references(
    note_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Get outgoing cross-references from a note."""
    cross_refs_data = await service.get_outgoing_refs(note_id, current_user.id, skip, limit)
    return [CrossRefWithNoteDetails(**ref) for ref in cross_refs_data]


@router.get(
    "/note/{note_id}/incoming",
    response_model=List[CrossRefWithNoteDetails],
    summary="Get incoming cross-references",
    description="Retrieve only incoming cross-references to a note (references other notes make to this note)."
)
async def get_incoming_cross_references(
    note_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Get incoming cross-references to a note."""
    cross_refs_data = await service.get_incoming_refs(note_id, current_user.id, skip, limit)
    return [CrossRefWithNoteDetails(**ref) for ref in cross_refs_data]


@router.get(
    "/note/{note_id}/related",
    response_model=List[NoteResponse],
    summary="Get related notes",
    description="Get all notes that are cross-referenced with the given note, optionally filtered by reference type."
)
async def get_related_notes(
    note_id: int,
    reference_types: Optional[str] = Query(
        None,
        description="Comma-separated list of reference types to filter by (e.g., 'related,references,supports')"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Get all notes that are cross-referenced with the given note."""
    # Parse reference types if provided
    ref_types_list = None
    if reference_types:
        ref_types_list = [t.strip() for t in reference_types.split(",")]
    
    notes = await service.get_related_notes(
        note_id,
        current_user.id,
        ref_types_list,
        skip,
        limit
    )
    
    return [NoteResponse.model_validate(note) for note in notes]


@router.get(
    "/note/{note_id}/count",
    response_model=dict,
    summary="Get cross-reference count",
    description="Get the count of cross-references for a note (total, outgoing, and incoming)."
)
async def get_cross_reference_count(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Get count of cross-references for a note."""
    return await service.get_cross_ref_count(note_id, current_user.id)


@router.put(
    "/{cross_ref_id}",
    response_model=CrossRefResponse,
    summary="Update a cross-reference",
    description="Update the metadata of an existing cross-reference (type, description, confidence score)."
)
async def update_cross_reference(
    cross_ref_id: int,
    cross_ref_data: CrossRefUpdate,
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Update an existing cross-reference."""
    cross_ref = await service.update_cross_ref(cross_ref_id, cross_ref_data, current_user.id)
    return CrossRefResponse.model_validate(cross_ref)


@router.delete(
    "/{cross_ref_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cross-reference",
    description="Delete a cross-reference. Only the owner of the source note can delete the reference."
)
async def delete_cross_reference(
    cross_ref_id: int,
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """Delete a cross-reference."""
    await service.delete_cross_ref(cross_ref_id, current_user.id)
    return None


# Placeholder endpoint for future AI suggestions feature
@router.get(
    "/suggestions/{note_id}",
    response_model=List[CrossRefSuggestion],
    summary="Get AI-suggested cross-references (Future Feature)",
    description="Get AI-suggested cross-references for a note. This is a placeholder for future implementation."
)
async def get_cross_reference_suggestions(
    note_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    service: CrossRefService = Depends(get_cross_ref_service)
):
    """
    Get AI-suggested cross-references for a note.
    
    This is a placeholder endpoint for future AI integration.
    Currently returns an empty list.
    """
    # TODO: Implement AI-based cross-reference suggestion
    # This would analyze note content and suggest related notes
    # using semantic similarity, topic modeling, or other AI techniques
    
    return []
