"""
Business Services Module

This module contains core business logic services for the Scribes application.

Services:
- AuthService: User authentication and authorization
- NoteService: Note CRUD operations and management
- CrossRefService: Cross-reference management and scripture lookups

Usage:
    from app.services.business import AuthService, NoteService
    
    auth = AuthService()
    user = await auth.authenticate(email, password, db=session)
"""

from app.services.business.auth_service import AuthService
from app.services.business.note_service import NoteService
from app.services.business.cross_ref_service import CrossRefService

__all__ = [
    "AuthService",
    "NoteService",
    "CrossRefService",
]
