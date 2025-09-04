"""
SQLite-based user storage implementation.
Clean replacement for in-memory storage with persistent data.
"""

import asyncio
import os
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from .config import settings
from .sqlmodel_models import UserModel
from sqlmodel import SQLModel


class SQLiteUserStorage:
    """
    SQLite-based user storage with persistent data.
    Maintains identical interface to previous in-memory implementation.
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized."""
        if not self._initialized:
            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            self._initialized = True
    
    async def user_exists(self, email: str) -> bool:
        """Check if user with given email exists."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel).where(UserModel.email == email.lower())
            result = await session.execute(stmt)
            return result.first() is not None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID. Returns user dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            user = result.first()
            return user[0].to_dict() if user else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email. Returns user dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel).where(UserModel.email == email.lower())
            result = await session.execute(stmt)
            user = result.first()
            return user[0].to_dict() if user else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in storage.
        Returns the created user data.
        Raises ValueError if user with email already exists.
        """
        # Validate required fields
        if 'id' not in user_data:
            raise ValueError("User data must include 'id' field")
        if 'email' not in user_data:
            raise ValueError("User data must include 'email' field")
        if 'password_hash' not in user_data:
            raise ValueError("User data must include 'password_hash' field")
        
        # Normalize and set defaults
        user_data_copy = user_data.copy()
        user_data_copy['email'] = user_data_copy['email'].lower()
        user_data_copy.setdefault('created_at', datetime.now(timezone.utc))
        user_data_copy.setdefault('profile_complete', False)
        user_data_copy.setdefault('name', '')
        
        await self._ensure_initialized()
        async with self.session_factory() as session:
            try:
                user_model = UserModel.from_dict(user_data_copy)
                session.add(user_model)
                await session.commit()
                await session.refresh(user_model)
                return user_model.to_dict()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"User with email {user_data['email']} already exists")
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user data.
        Returns updated user data or None if user not found.
        Cannot update id, email, or password_hash through this method.
        """
        # Prevent updating immutable fields
        forbidden_fields = {'id', 'email', 'password_hash'}
        if any(field in updates for field in forbidden_fields):
            raise ValueError(f"Cannot update fields: {', '.join(forbidden_fields)}")
        
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            user = result.first()
            
            if not user:
                return None
            
            user_model = user[0]
            user_model.update_from_dict(updates)
            
            await session.commit()
            await session.refresh(user_model)
            return user_model.to_dict()
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user by ID.
        Returns True if user was deleted, False if user not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            user = result.first()
            
            if not user:
                return False
            
            await session.delete(user[0])
            await session.commit()
            return True
    
    async def list_all_users(self) -> List[Dict[str, Any]]:
        """Get all users. Returns list of user dictionaries."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel).order_by(UserModel.created_at)
            result = await session.execute(stmt)
            users = result.fetchall()
            return [user[0].to_dict() for user in users]
    
    async def get_user_count(self) -> int:
        """Get total number of users."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel)
            result = await session.execute(stmt)
            return len(result.fetchall())
    
    async def clear_all_users(self) -> None:
        """Clear all users from storage. Use with caution."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(UserModel)
            result = await session.execute(stmt)
            users = result.fetchall()
            
            for user in users:
                await session.delete(user[0])
            
            await session.commit()
    
    async def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create or update user profile information.
        Marks profile as complete.
        Returns updated user data or None if user not found.
        """
        profile_updates = profile_data.copy()
        profile_updates['profile_complete'] = True
        
        return await self.update_user(user_id, profile_updates)
    
    async def search_users_by_name(self, name_query: str) -> List[Dict[str, Any]]:
        """
        Search users by name (case-insensitive partial match).
        Returns list of matching user dictionaries.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            if not name_query:
                # For empty query, return only users with non-empty names
                stmt = select(UserModel).where(UserModel.name != "")
            else:
                # For non-empty query, search in names (including empty names if they match)
                name_pattern = f"%{name_query.lower()}%"
                stmt = select(UserModel).where(UserModel.name.ilike(name_pattern))
            
            result = await session.execute(stmt)
            users = result.fetchall()
            return [user[0].to_dict() for user in users]


# Async-to-sync wrapper for compatibility with existing sync code
class AsyncUserStorageWrapper:
    """Wrapper to make async SQLite storage work with sync code."""
    
    def __init__(self):
        self._async_storage = SQLiteUserStorage()
        self._loop = None
    
    def _get_or_create_loop(self):
        """Get current event loop or create a new one."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def _run_async(self, coro):
        """Run async function in sync context."""
        loop = self._get_or_create_loop()
        if loop.is_running():
            # If we're in an async context, create a new thread
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    
    def user_exists(self, email: str) -> bool:
        """Check if user with given email exists."""
        return self._run_async(self._async_storage.user_exists(email))
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID. Returns user dict or None if not found."""
        return self._run_async(self._async_storage.get_user_by_id(user_id))
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email. Returns user dict or None if not found."""
        return self._run_async(self._async_storage.get_user_by_email(email))
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in storage."""
        return self._run_async(self._async_storage.create_user(user_data))
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data."""
        return self._run_async(self._async_storage.update_user(user_id, updates))
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID."""
        return self._run_async(self._async_storage.delete_user(user_id))
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        return self._run_async(self._async_storage.list_all_users())
    
    def get_user_count(self) -> int:
        """Get total number of users."""
        return self._run_async(self._async_storage.get_user_count())
    
    def clear_all_users(self) -> None:
        """Clear all users from storage."""
        return self._run_async(self._async_storage.clear_all_users())
    
    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update user profile information."""
        return self._run_async(self._async_storage.create_user_profile(user_id, profile_data))
    
    def search_users_by_name(self, name_query: str) -> List[Dict[str, Any]]:
        """Search users by name."""
        return self._run_async(self._async_storage.search_users_by_name(name_query))


# Global user storage instance - now SQLite with sync compatibility
user_storage = AsyncUserStorageWrapper()