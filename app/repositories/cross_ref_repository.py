"""
Cross Reference repository for database operations.
Handles CRUD operations for cross-references between notes.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload

from app.models.cross_ref_model import CrossRef
from app.models.note_model import Note


class CrossRefRepository:
    """Repository for cross-reference database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def create(
        self,
        note_id: int,
        other_note_id: int,
        reference_type: str = "related",
        description: Optional[str] = None,
        is_auto_generated: str = "manual",
        confidence_score: Optional[int] = None
    ) -> CrossRef:
        """Create a new cross-reference."""
        cross_ref = CrossRef(
            note_id=note_id,
            other_note_id=other_note_id,
            reference_type=reference_type,
            description=description,
            is_auto_generated=is_auto_generated,
            confidence_score=confidence_score
        )
        
        self.db.add(cross_ref)
        await self.db.commit()
        await self.db.refresh(cross_ref)
        
        return cross_ref

    async def get_by_id(self, cross_ref_id: int) -> Optional[CrossRef]:
        """Get cross-reference by ID."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note), selectinload(CrossRef.other_note))
            .where(CrossRef.id == cross_ref_id)
        )
        return result.scalar_one_or_none()

    async def get_by_note_id(
        self,
        note_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get all cross-references for a specific note (both outgoing and incoming)."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note), selectinload(CrossRef.other_note))
            .where(or_(CrossRef.note_id == note_id, CrossRef.other_note_id == note_id))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_outgoing_refs(
        self,
        note_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get outgoing cross-references from a note."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.other_note))
            .where(CrossRef.note_id == note_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_incoming_refs(
        self,
        note_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get incoming cross-references to a note."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note))
            .where(CrossRef.other_note_id == note_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        reference_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get cross-references by type."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note), selectinload(CrossRef.other_note))
            .where(CrossRef.reference_type == reference_type)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ai_generated(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get AI-generated cross-references."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note), selectinload(CrossRef.other_note))
            .where(CrossRef.is_auto_generated.in_(["ai_suggested", "ai_auto"]))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_manual(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get manually created cross-references."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note), selectinload(CrossRef.other_note))
            .where(CrossRef.is_auto_generated == "manual")
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def check_exists(
        self,
        note_id: int,
        other_note_id: int
    ) -> bool:
        """Check if cross-reference already exists between two notes (bidirectional)."""
        result = await self.db.execute(
            select(CrossRef)
            .where(
                or_(
                    and_(CrossRef.note_id == note_id, CrossRef.other_note_id == other_note_id),
                    and_(CrossRef.note_id == other_note_id, CrossRef.other_note_id == note_id)
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def update(
        self,
        cross_ref_id: int,
        reference_type: Optional[str] = None,
        description: Optional[str] = None,
        is_auto_generated: Optional[str] = None,
        confidence_score: Optional[int] = None
    ) -> Optional[CrossRef]:
        """Update an existing cross-reference."""
        cross_ref = await self.get_by_id(cross_ref_id)
        
        if not cross_ref:
            return None
        
        if reference_type is not None:
            cross_ref.reference_type = reference_type
        if description is not None:
            cross_ref.description = description
        if is_auto_generated is not None:
            cross_ref.is_auto_generated = is_auto_generated
        if confidence_score is not None:
            cross_ref.confidence_score = confidence_score
        
        await self.db.commit()
        await self.db.refresh(cross_ref)
        
        return cross_ref

    async def delete(self, cross_ref_id: int) -> bool:
        """Delete a cross-reference."""
        cross_ref = await self.get_by_id(cross_ref_id)
        
        if not cross_ref:
            return False
        
        await self.db.delete(cross_ref)
        await self.db.commit()
        
        return True

    async def delete_by_note(self, note_id: int) -> int:
        """Delete all cross-references associated with a note."""
        result = await self.db.execute(
            delete(CrossRef).where(
                or_(CrossRef.note_id == note_id, CrossRef.other_note_id == note_id)
            )
        )
        await self.db.commit()
        return result.rowcount

    async def count_by_note(self, note_id: int) -> int:
        """Count all cross-references for a note."""
        result = await self.db.execute(
            select(func.count(CrossRef.id))
            .where(or_(CrossRef.note_id == note_id, CrossRef.other_note_id == note_id))
        )
        return result.scalar() or 0

    async def count_outgoing(self, note_id: int) -> int:
        """Count outgoing cross-references from a note."""
        result = await self.db.execute(
            select(func.count(CrossRef.id))
            .where(CrossRef.note_id == note_id)
        )
        return result.scalar() or 0

    async def count_incoming(self, note_id: int) -> int:
        """Count incoming cross-references to a note."""
        result = await self.db.execute(
            select(func.count(CrossRef.id))
            .where(CrossRef.other_note_id == note_id)
        )
        return result.scalar() or 0

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrossRef]:
        """Get all cross-references with pagination."""
        result = await self.db.execute(
            select(CrossRef)
            .options(selectinload(CrossRef.note), selectinload(CrossRef.other_note))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        """Count total number of cross-references."""
        result = await self.db.execute(select(func.count(CrossRef.id)))
        return result.scalar() or 0

    async def bulk_create(self, cross_refs_data: List[dict]) -> List[CrossRef]:
        """Create multiple cross-references at once."""
        cross_refs = [CrossRef(**data) for data in cross_refs_data]
        
        self.db.add_all(cross_refs)
        await self.db.commit()
        
        # Refresh all objects
        for cross_ref in cross_refs:
            await self.db.refresh(cross_ref)
        
        return cross_refs

    async def get_related_notes(
        self,
        note_id: int,
        reference_types: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Note]:
        """Get all notes that are cross-referenced with the given note."""
        query = select(Note).distinct()
        
        # Join with CrossRef to get related notes
        query = query.join(
            CrossRef,
            or_(
                and_(CrossRef.note_id == note_id, Note.id == CrossRef.other_note_id),
                and_(CrossRef.other_note_id == note_id, Note.id == CrossRef.note_id)
            )
        )
        
        # Filter by reference types if specified
        if reference_types:
            query = query.where(CrossRef.reference_type.in_(reference_types))
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
