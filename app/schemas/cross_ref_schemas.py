"""
Cross reference-related Pydantic schemas for request/response validation.
"""

from typing import Optional, List
from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class CrossRefBase(BaseSchema):
    """Base cross reference schema with common fields."""
    
    other_note_id: int = Field(
        ...,
        description="ID of the note being referenced",
        examples=[2]
    )
    reference_type: Optional[str] = Field(
        "related",
        max_length=50,
        description="Type of reference: related, references, cited_by, contradicts, supports",
        examples=["related"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of the relationship",
        examples=["Both notes discuss the same theological concept"]
    )
    is_auto_generated: Optional[str] = Field(
        "manual",
        max_length=20,
        description="Source: manual, ai_suggested, ai_auto",
        examples=["manual"]
    )
    confidence_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Confidence score for AI-generated references (0-100)",
        examples=[85]
    )


class CrossRefCreate(CrossRefBase):
    """Schema for creating cross reference."""
    
    note_id: int = Field(..., description="Source note ID", examples=[1])
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "note_id": 1,
                    "other_note_id": 2,
                    "reference_type": "related",
                    "description": "Both notes discuss grace and salvation",
                    "is_auto_generated": "manual"
                },
                {
                    "note_id": 1,
                    "other_note_id": 3,
                    "reference_type": "references",
                    "is_auto_generated": "ai_suggested",
                    "confidence_score": 92
                }
            ]
        }
    }


class CrossRefUpdate(BaseSchema):
    """Schema for updating cross reference."""
    
    reference_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Updated reference type",
        examples=["supports"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated description",
        examples=["Updated relationship description"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reference_type": "supports",
                    "description": "This note supports the argument in the other note"
                }
            ]
        }
    }


class CrossRefResponse(CrossRefBase, TimestampSchema):
    """Schema for cross reference response."""
    
    id: int
    note_id: int = Field(..., description="Source note ID")
    
    model_config = BaseSchema.model_config


class CrossRefWithNoteDetails(CrossRefResponse):
    """Schema for cross reference with note details."""
    
    note_title: Optional[str] = Field(None, description="Title of the source note")
    note_preview: Optional[str] = Field(
        None,
        description="Preview of the source note content",
        examples=["This note discusses the theological concept of..."]
    )
    other_note_title: Optional[str] = Field(None, description="Title of the referenced note")
    other_note_preview: Optional[str] = Field(
        None,
        description="Preview of the referenced note content",
        examples=["This note discusses the theological concept of..."]
    )
    
    model_config = BaseSchema.model_config


class CrossRefListResponse(BaseSchema):
    """Schema for list of cross references."""
    
    cross_refs: List[CrossRefWithNoteDetails]
    total: int
    skip: int = 0
    limit: int = 100
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cross_refs": [],
                    "total": 5,
                    "skip": 0,
                    "limit": 100
                }
            ]
        }
    }


class CrossRefSuggestion(BaseSchema):
    """Schema for AI-suggested cross reference."""
    
    note_id: int = Field(..., description="Source note ID")
    suggested_note_id: int = Field(..., description="Suggested related note ID")
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score (0-100)"
    )
    reason: str = Field(
        ...,
        description="Explanation of why this reference is suggested",
        examples=["Both notes discuss similar theological themes"]
    )
    suggested_reference_type: str = Field(
        ...,
        description="Suggested reference type",
        examples=["related"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "note_id": 1,
                    "suggested_note_id": 5,
                    "confidence_score": 87,
                    "reason": "Both notes discuss the doctrine of grace",
                    "suggested_reference_type": "related"
                }
            ]
        }
    }


class BulkCrossRefCreate(BaseSchema):
    """Schema for bulk creating multiple cross references."""
    
    cross_refs: List[CrossRefCreate] = Field(
        ...,
        description="List of cross references to create",
        min_length=1,
        max_length=100
    )
    skip_errors: bool = Field(
        True,
        description="Whether to skip errors and continue with valid references"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cross_refs": [
                        {
                            "note_id": 1,
                            "other_note_id": 2,
                            "reference_type": "related",
                            "description": "Both discuss grace"
                        },
                        {
                            "note_id": 1,
                            "other_note_id": 3,
                            "reference_type": "expands_on"
                        }
                    ],
                    "skip_errors": True
                }
            ]
        }
    }