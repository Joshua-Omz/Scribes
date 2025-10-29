"""
User repository for database operations.
Data access layer for user-related queries.
"""

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db
    
    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_data: User creation data
            hashed_password: Hashed password
            
        Returns:
            User: Created user object
        """
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role="user",
            is_active=True,
            is_verified=False,
            is_superuser=False,
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User object or None
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            Optional[User]: User object or None
        """
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            Optional[User]: User object or None
        """
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Optional[User]: Updated user object or None
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_dict = user_data.model_dump(exclude_unset=True)
        
        if update_dict:
            # Normalize email and username
            if "email" in update_dict:
                update_dict["email"] = update_dict["email"].lower()
            if "username" in update_dict:
                update_dict["username"] = update_dict["username"].lower()
            
            for key, value in update_dict.items():
                setattr(user, key, value)
            
            await self.db.flush()
            await self.db.refresh(user)
        
        return user
    
    async def update_password(self, user_id: int, hashed_password: str) -> Optional[User]:
        """
        Update user password.
        
        Args:
            user_id: User ID
            hashed_password: New hashed password
            
        Returns:
            Optional[User]: Updated user object or None
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.hashed_password = hashed_password
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def verify_email(self, user_id: int) -> Optional[User]:
        """
        Mark user email as verified.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: Updated user object or None
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_verified = True
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def deactivate(self, user_id: int) -> Optional[User]:
        """
        Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: Updated user object or None
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def activate(self, user_id: int) -> Optional[User]:
        """
        Activate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: Updated user object or None
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_active = True
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def delete(self, user_id: int) -> bool:
        """
        Delete user from database.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.db.delete(user)
        await self.db.flush()
        
        return True
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        List users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status
            
        Returns:
            List[User]: List of user objects
        """
        query = select(User)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_users(self, is_active: Optional[bool] = None) -> int:
        """
        Count total number of users.
        
        Args:
            is_active: Filter by active status
            
        Returns:
            int: Total user count
        """
        from sqlalchemy import func
        
        query = select(func.count(User.id))
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalar_one()
