"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user_model import User
from app.repositories.user_repository import UserRepository


# HTTP Bearer token scheme for Swagger UI
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (must be active).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user





async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user (must be active and verified).
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current verified user
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user (must be active and admin/superuser).
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin" and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for optional authentication.
    
    Args:
        credentials: HTTP Bearer credentials (optional)
        db: Database session
        
    Returns:
        Optional[User]: Current user or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_all_users_dependency(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> list[User]:
    """
    Get all users from the database (admin only).
    
    Args:
        current_user: Current admin user
        db: Database session
        
    Returns:
        list[User]: List of all users
        
    Raises:
        HTTPException: If user is not admin
    """
    user_repo = UserRepository(db)
    users = await user_repo.get_all()
    return users


async def get_all_deactivated_users_dependency(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> list[User]:
    """
    Get all deactivated users from the database (admin only).
    
    Args:
        current_user: Current admin user
        db: Database session
        
    Returns:
        list[User]: List of all deactivated users
        
    Raises:
        HTTPException: If user is not admin
    """
    user_repo = UserRepository(db)
    users = await user_repo.get_all_deactivated()
    return users


# ============================================================================
# CACHE MANAGER DEPENDENCY (Phase 2: AI Caching)
# ============================================================================

from app.core.cache import get_cache_manager, RedisCacheManager


async def get_cache() -> RedisCacheManager:
    """
    Get Redis cache manager for AI caching.
    
    Provides access to three-layer cache:
    - L1: Query result cache (complete AI responses)
    - L2: Embedding cache (query embeddings)
    - L3: Context cache (retrieved sermon chunks)
    
    Returns:
        RedisCacheManager: Cache manager instance
        
    Usage:
        @router.get("/endpoint")
        async def endpoint(cache: RedisCacheManager = Depends(get_cache)):
            if cache.is_available:
                result = await cache.cache.get("key")
    """
    return await get_cache_manager()
