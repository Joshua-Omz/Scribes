"""
Helper Utilities Module

General-purpose helper functions for common tasks.

Modules:
- text_utils: Text manipulation and processing
- validation: Input validation functions
- formatters: Data formatting utilities

Usage:
    from app.utils.helpers import truncate_text, is_valid_email, format_timestamp
"""

from app.utils.helpers.text_utils import (
    truncate_text,
    clean_whitespace,
    normalize_scripture_ref,
    extract_tags_from_text,
)

from app.utils.helpers.validation import (
    is_valid_email,
    is_valid_scripture_ref,
    sanitize_input,
    validate_query_length,
)

from app.utils.helpers.formatters import (
    format_timestamp,
    format_note_preview,
    format_tags_list,
    format_response_metadata,
    format_error_response,
)

__all__ = [
    # Text utilities
    "truncate_text",
    "clean_whitespace",
    "normalize_scripture_ref",
    "extract_tags_from_text",
    # Validation
    "is_valid_email",
    "is_valid_scripture_ref",
    "sanitize_input",
    "validate_query_length",
    # Formatters
    "format_timestamp",
    "format_note_preview",
    "format_tags_list",
    "format_response_metadata",
    "format_error_response",
]
