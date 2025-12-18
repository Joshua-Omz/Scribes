"""
Annotation-related Pydantic schemas for request/response validation.
"""

from typing import Optional
from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class AnnotationBase(BaseSchema):
    """Base annotation schema with common fields."""
    
    content: str = Field(
        ...,
        min_length=1,
        description="Annotation content/comment",
        examples=["This is an important point to remember"]
    )
    annotation_type: Optional[str] = Field(
        "comment",
        max_length=50,
        description="Type of annotation: comment, highlight, note",
        examples=["comment"]
    )
    start_position: Optional[int] = Field(
        None,
        ge=0,
        description="Starting character position in the note",
        examples=[120]
    )
    end_position: Optional[int] = Field(
        None,
        ge=0,
        description="Ending character position in the note",
        examples=[150]
    )
    highlighted_text: Optional[str] = Field(
        None,
        description="The text that was highlighted",
        examples=["This is the highlighted text"]
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="Highlight color (hex or name)",
        examples=["#ffeb3b", "yellow"]
    )


class AnnotationCreate(AnnotationBase):
    """Schema for creating annotation."""
    
    note_id: int = Field(..., description="Note ID to annotate", examples=[1])
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "note_id": 1,
                    "content": "This is an important theological point",
                    "annotation_type": "highlight",
                    "start_position": 120,
                    "end_position": 150,
                    "highlighted_text": "This is the highlighted text",
                    "color": "yellow"
                }
            ]
        }
    }


class AnnotationUpdate(BaseSchema):
    """Schema for updating annotation."""
    
    content: Optional[str] = Field(
        None,
        min_length=1,
        description="Updated annotation content",
        examples=["Updated comment"]
    )
    annotation_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Updated annotation type",
        examples=["note"]
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="Updated color",
        examples=["blue"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Updated annotation content",
                    "color": "blue"
                }
            ]
        }
    }


class AnnotationResponse(AnnotationBase, TimestampSchema):
    """Schema for annotation response."""
    
    id: int
    user_id: int = Field(..., description="User who created the annotation")
    note_id: int = Field(..., description="Note being annotated")
    
    model_config = BaseSchema.model_config
