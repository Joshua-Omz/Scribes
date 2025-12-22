"""
Data Formatting Utilities

Common data formatting functions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def format_timestamp(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object
        format_str: Format string (default: ISO-like format)
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def format_note_preview(content: str, max_length: int = 150) -> str:
    """
    Format note content for preview display.
    
    Args:
        content: Full note content
        max_length: Maximum preview length
        
    Returns:
        Formatted preview
    """
    # Clean whitespace
    content = " ".join(content.split())
    
    # Truncate if needed
    if len(content) <= max_length:
        return content
    
    # Try to break at word boundary
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If space is reasonably close to end
        truncated = truncated[:last_space]
    
    return truncated + "..."


def format_tags_list(tags: Optional[str]) -> List[str]:
    """
    Format tags string into list.
    
    Args:
        tags: Comma-separated tags string
        
    Returns:
        List of tag strings
    """
    if not tags:
        return []
    
    return [tag.strip() for tag in tags.split(',') if tag.strip()]


def format_response_metadata(sources: List[Dict[str, Any]], include_scores: bool = True) -> List[Dict[str, Any]]:
    """
    Format source metadata for API responses.
    
    Args:
        sources: List of source documents with metadata
        include_scores: Whether to include similarity scores
        
    Returns:
        Formatted metadata list
    """
    formatted = []
    
    for source in sources:
        item = {
            "note_id": source.get("note_id"),
            "title": source.get("title"),
            "chunk_idx": source.get("chunk_idx"),
        }
        
        if include_scores and "similarity_score" in source:
            item["similarity_score"] = round(source["similarity_score"], 4)
        
        formatted.append(item)
    
    return formatted


def format_error_response(error: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format error response for API.
    
    Args:
        error: Error message
        details: Optional error details
        
    Returns:
        Formatted error response
    """
    response = {
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response
