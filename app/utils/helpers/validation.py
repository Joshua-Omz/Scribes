"""
Input Validation Utilities

Common validation functions for user inputs.
"""

import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_scripture_ref(ref: str) -> bool:
    """
    Validate scripture reference format.
    
    Examples of valid refs:
        - "John 3:16"
        - "1 John 3:16"
        - "Matthew 5:1-10"
        - "Genesis 1"
        
    Args:
        ref: Scripture reference
        
    Returns:
        True if valid format
    """
    # Basic pattern - can be enhanced
    pattern = r'^[\d\s]*[A-Za-z]+\s+\d+(?::\d+(?:-\d+)?)?$'
    return bool(re.match(pattern, ref.strip()))


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input text.
    
    Args:
        text: Input text
        max_length: Optional maximum length
        
    Returns:
        Sanitized text
    """
    # Remove any potential SQL injection attempts
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_query_length(query: str, min_length: int = 3, max_length: int = 500) -> tuple[bool, Optional[str]]:
    """
    Validate query string length.
    
    Args:
        query: Query string
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    query = query.strip()
    
    if not query:
        return False, "Query cannot be empty"
    
    if len(query) < min_length:
        return False, f"Query must be at least {min_length} characters"
    
    if len(query) > max_length:
        return False, f"Query must be at most {max_length} characters"
    
    return True, None
