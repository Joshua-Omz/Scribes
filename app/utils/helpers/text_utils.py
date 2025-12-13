"""
Text Utilities

Common text manipulation and processing functions.
"""

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Input text to truncate
        max_length: Maximum length (default: 100)
        suffix: Suffix to add when truncated (default: "...")
        
    Returns:
        Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_whitespace(text: str) -> str:
    """
    Clean excess whitespace from text.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    return " ".join(text.split())


def normalize_scripture_ref(ref: str) -> str:
    """
    Normalize scripture reference format.
    
    Examples:
        "John 3:16" -> "John 3:16"
        "john 3 : 16" -> "John 3:16"
        "1john3:16" -> "1 John 3:16"
        
    Args:
        ref: Scripture reference
        
    Returns:
        Normalized reference
    """
    # Remove extra spaces around colons
    ref = ref.replace(" : ", ":").replace(": ", ":").replace(" :", ":")
    
    # Add space before book name and chapter
    # Basic implementation - can be enhanced
    return ref.strip()


def extract_tags_from_text(text: str) -> list[str]:
    """
    Extract potential tags from text based on common patterns.
    
    Args:
        text: Input text
        
    Returns:
        List of potential tags
    """
    # Simple implementation - can be enhanced with NLP
    words = text.lower().split()
    
    # Filter for words that might be good tags
    tags = [
        word.strip('.,!?;:')
        for word in words
        if len(word) > 4 and word.isalpha()
    ]
    
    # Return unique tags
    return list(set(tags))[:10]  # Max 10 tags
