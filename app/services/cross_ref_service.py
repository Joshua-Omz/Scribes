"""
Cross Reference service for business logic.
Handles validation and business rules for cross-references between notes.
"""

from typing import List, Optional
from fastapi import HTTPException, status

from app.repositories.cross_ref_repository import CrossRefRepository
from app.repositories.note_repository import NoteRepository
from app.models.cross_ref_model import CrossRef
from app.schemas.cross_ref_schemas import (
    CrossRefCreate,
    CrossRefUpdate,
    CrossRefResponse,
    CrossRefWithNoteDetails,
    BulkCrossRefCreate
)


def _enrich_cross_ref_with_details(cross_ref: CrossRef) -> dict:
    """
    Enrich a CrossRef model with note details for the response.
    Extracts titles and previews from the related notes.
    """
    data = {
        "id": cross_ref.id,
        "note_id": cross_ref.note_id,
        "other_note_id": cross_ref.other_note_id,
        "reference_type": cross_ref.reference_type,
        "description": cross_ref.description,
        "is_auto_generated": cross_ref.is_auto_generated,
        "confidence_score": cross_ref.confidence_score,
        "created_at": cross_ref.created_at,
    }
    
    # Add note details if the relationship is loaded
    if cross_ref.note:
        data["note_title"] = cross_ref.note.title
        # Create a preview (first 100 characters of content)
        content = cross_ref.note.content or ""
        data["note_preview"] = content[:100] + "..." if len(content) > 100 else content
    
    if cross_ref.other_note:
        data["other_note_title"] = cross_ref.other_note.title
        # Create a preview (first 100 characters of content)
        content = cross_ref.other_note.content or ""
        data["other_note_preview"] = content[:100] + "..." if len(content) > 100 else content
    
    return data


class CrossRefService:
    """Service for cross-reference business logic."""
    
    def __init__(self, cross_ref_repo: CrossRefRepository, note_repo: NoteRepository):
        """Initialize service with repositories."""
        self.cross_ref_repo = cross_ref_repo
        self.note_repo = note_repo

    async def create_cross_ref(
        self,
        cross_ref_data: CrossRefCreate,
        user_id: int
    ) -> CrossRef:
        """
        Create a new cross-reference.
        Validates:
        - Both notes exist
        - User owns the source note
        - Cross-reference doesn't already exist
        - Source and target notes are different
        """
        # Check if source and target are the same
        if cross_ref_data.note_id == cross_ref_data.other_note_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a cross-reference to the same note"
            )
        
        # Verify source note exists and user owns it
        source_note = await self.note_repo.get_by_id(cross_ref_data.note_id)
        if not source_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source note with id {cross_ref_data.note_id} not found"
            )
        
        if source_note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create cross-references for this note"
            )
        
        # Verify target note exists and user owns it
        target_note = await self.note_repo.get_by_id(cross_ref_data.other_note_id)
        if not target_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target note with id {cross_ref_data.other_note_id} not found"
            )
        
        if target_note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create cross-references between your own notes"
            )
        
        # Check if cross-reference already exists (bidirectional)
        exists = await self.cross_ref_repo.check_exists(
            cross_ref_data.note_id,
            cross_ref_data.other_note_id
        )
        
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A cross-reference between these notes already exists"
            )
        
        # Create the cross-reference
        return await self.cross_ref_repo.create(
            note_id=cross_ref_data.note_id,
            other_note_id=cross_ref_data.other_note_id,
            reference_type=cross_ref_data.reference_type,
            description=cross_ref_data.description,
            is_auto_generated=cross_ref_data.is_auto_generated,
            confidence_score=cross_ref_data.confidence_score
        )

    async def get_cross_ref(self, cross_ref_id: int, user_id: int) -> dict:
        """
        Get a cross-reference by ID with note details.
        Validates user owns the source note.
        """
        cross_ref = await self.cross_ref_repo.get_by_id(cross_ref_id)
        
        if not cross_ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cross-reference with id {cross_ref_id} not found"
            )
        
        # Verify user owns either the source or target note
        source_note = await self.note_repo.get_by_id(cross_ref.note_id)
        target_note = await self.note_repo.get_by_id(cross_ref.other_note_id)
        
        if source_note.user_id != user_id and target_note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this cross-reference"
            )
        
        return _enrich_cross_ref_with_details(cross_ref)

    async def get_note_cross_refs(
        self,
        note_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        Get all cross-references for a note with details.
        Validates user owns the note.
        """
        # Verify note exists and user owns it
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        if note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view cross-references for this note"
            )
        
        cross_refs = await self.cross_ref_repo.get_by_note_id(note_id, skip, limit)
        return [_enrich_cross_ref_with_details(cr) for cr in cross_refs]

    async def get_outgoing_refs(
        self,
        note_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """Get outgoing cross-references from a note with details."""
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        if note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view cross-references for this note"
            )
        
        cross_refs = await self.cross_ref_repo.get_outgoing_refs(note_id, skip, limit)
        return [_enrich_cross_ref_with_details(cr) for cr in cross_refs]

    async def get_incoming_refs(
        self,
        note_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """Get incoming cross-references to a note with details."""
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        if note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view cross-references for this note"
            )
        
        cross_refs = await self.cross_ref_repo.get_incoming_refs(note_id, skip, limit)
        return [_enrich_cross_ref_with_details(cr) for cr in cross_refs]

    async def update_cross_ref(
        self,
        cross_ref_id: int,
        cross_ref_data: CrossRefUpdate,
        user_id: int
    ) -> CrossRef:
        """
        Update a cross-reference.
        Validates user owns the source note.
        """
        # Get existing cross-reference
        cross_ref = await self.cross_ref_repo.get_by_id(cross_ref_id)
        
        if not cross_ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cross-reference with id {cross_ref_id} not found"
            )
        
        # Verify user owns the source note
        source_note = await self.note_repo.get_by_id(cross_ref.note_id)
        if source_note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this cross-reference"
            )
        
        # Update the cross-reference
        updated_cross_ref = await self.cross_ref_repo.update(
            cross_ref_id=cross_ref_id,
            reference_type=cross_ref_data.reference_type,
            description=cross_ref_data.description,
            is_auto_generated=cross_ref_data.is_auto_generated,
            confidence_score=cross_ref_data.confidence_score
        )
        
        return updated_cross_ref

    async def delete_cross_ref(self, cross_ref_id: int, user_id: int) -> bool:
        """
        Delete a cross-reference.
        Validates user owns the source note.
        """
        # Get existing cross-reference
        cross_ref = await self.cross_ref_repo.get_by_id(cross_ref_id)
        
        if not cross_ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cross-reference with id {cross_ref_id} not found"
            )
        
        # Verify user owns the source note
        source_note = await self.note_repo.get_by_id(cross_ref.note_id)
        if source_note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this cross-reference"
            )
        
        return await self.cross_ref_repo.delete(cross_ref_id)

    async def bulk_create_cross_refs(
        self,
        bulk_data: BulkCrossRefCreate,
        user_id: int
    ) -> List[CrossRef]:
        """
        Create multiple cross-references at once.
        Validates all notes and checks for duplicates.
        """
        created_refs = []
        
        for cross_ref_data in bulk_data.cross_refs:
            try:
                cross_ref = await self.create_cross_ref(cross_ref_data, user_id)
                created_refs.append(cross_ref)
            except HTTPException as e:
                # Skip duplicates or invalid refs in bulk operations
                if bulk_data.skip_errors:
                    continue
                else:
                    raise e
        
        return created_refs

    async def get_cross_ref_count(self, note_id: int, user_id: int) -> dict:
        """Get count of cross-references for a note."""
        # Verify note exists and user owns it
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        if note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this note's statistics"
            )
        
        total = await self.cross_ref_repo.count_by_note(note_id)
        outgoing = await self.cross_ref_repo.count_outgoing(note_id)
        incoming = await self.cross_ref_repo.count_incoming(note_id)
        
        return {
            "note_id": note_id,
            "total_cross_refs": total,
            "outgoing_refs": outgoing,
            "incoming_refs": incoming
        }

    async def get_related_notes(
        self,
        note_id: int,
        user_id: int,
        reference_types: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all notes that are cross-referenced with the given note."""
        # Verify note exists and user owns it
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        if note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view related notes"
            )
        
        return await self.cross_ref_repo.get_related_notes(
            note_id,
            reference_types,
            skip,
            limit
        )
