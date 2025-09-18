"""
SQLite-based user storage implementation.
Clean replacement for in-memory storage with persistent data.
"""

import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import uuid

from .config import settings
from .sqlmodel_models import (
    UserModel, PersonalContextModel, PersonalContextCreate, PersonalContextUpdate,
    ConnectedAccountModel, ConnectedAccountCreate, ConnectedAccountUpdate
)
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

    # PersonalContext operations
    async def get_personal_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get personal context data for user. Returns context dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(PersonalContextModel).where(PersonalContextModel.user_id == user_id)
            result = await session.execute(stmt)
            context = result.first()
            return context[0].to_dict() if context else None
    
    async def create_personal_context(self, user_id: str, context_data: PersonalContextCreate) -> Dict[str, Any]:
        """
        Create personal context for user.
        Returns the created context data.
        Raises ValueError if context already exists.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            try:
                context_model = PersonalContextModel(user_id=user_id, **context_data.model_dump())
                session.add(context_model)
                await session.commit()
                await session.refresh(context_model)
                return context_model.to_dict()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Personal context for user {user_id} already exists")
    
    async def update_personal_context(self, user_id: str, updates: PersonalContextUpdate) -> Optional[Dict[str, Any]]:
        """
        Update personal context data.
        Returns updated context data or None if context not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(PersonalContextModel).where(PersonalContextModel.user_id == user_id)
            result = await session.execute(stmt)
            context = result.first()
            
            if not context:
                return None
            
            context_model = context[0]
            
            # Update fields from PersonalContextUpdate
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(context_model, field, value)
            
            context_model.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            await session.refresh(context_model)
            return context_model.to_dict()
    
    async def create_or_update_personal_context(self, user_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update personal context data.
        Returns the context data (created or updated).
        """
        # Try to get existing context
        existing = await self.get_personal_context(user_id)
        
        if existing:
            # Update existing context
            update_obj = PersonalContextUpdate(**context_data)
            return await self.update_personal_context(user_id, update_obj)
        else:
            # Create new context
            create_obj = PersonalContextCreate(**context_data)
            return await self.create_personal_context(user_id, create_obj)
    
    async def delete_personal_context(self, user_id: str) -> bool:
        """
        Delete personal context by user ID.
        Returns True if context was deleted, False if not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(PersonalContextModel).where(PersonalContextModel.user_id == user_id)
            result = await session.execute(stmt)
            context = result.first()

            if not context:
                return False

            await session.delete(context[0])
            await session.commit()
            return True

    # ConnectedAccount operations
    async def get_connected_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connected accounts for user. Returns list of account dicts."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.is_active == True
            ).order_by(ConnectedAccountModel.created_at)
            result = await session.execute(stmt)
            accounts = result.fetchall()
            return [account[0].to_dict() for account in accounts]

    async def get_connected_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get connected account by ID. Returns account dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(ConnectedAccountModel.id == account_id)
            result = await session.execute(stmt)
            account = result.first()
            return account[0].to_dict() if account else None

    async def get_connected_account_by_plaid_id(self, user_id: str, plaid_account_id: str) -> Optional[Dict[str, Any]]:
        """Get connected account by Plaid account ID. Returns account dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.plaid_account_id == plaid_account_id
            )
            result = await session.execute(stmt)
            account = result.first()
            return account[0].to_dict() if account else None

    async def create_connected_account(self, user_id: str, account_data: ConnectedAccountCreate) -> Dict[str, Any]:
        """
        Create connected account for user.
        Returns the created account data.
        Raises ValueError if account already exists.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            try:
                # Generate unique account ID
                account_id = str(uuid.uuid4())

                account_model = ConnectedAccountModel(
                    id=account_id,
                    user_id=user_id,
                    **account_data.model_dump()
                )
                session.add(account_model)
                await session.commit()
                await session.refresh(account_model)
                return account_model.to_dict()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Connected account with Plaid ID {account_data.plaid_account_id} already exists for user {user_id}")

    async def update_connected_account(self, account_id: str, updates: ConnectedAccountUpdate) -> Optional[Dict[str, Any]]:
        """
        Update connected account data.
        Returns updated account data or None if account not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(ConnectedAccountModel.id == account_id)
            result = await session.execute(stmt)
            account = result.first()

            if not account:
                return None

            account_model = account[0]

            # Update fields from ConnectedAccountUpdate
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(account_model, field, value)

            account_model.updated_at = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(account_model)
            return account_model.to_dict()

    async def deactivate_connected_account(self, account_id: str) -> bool:
        """
        Deactivate connected account (soft delete).
        Returns True if account was deactivated, False if not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(ConnectedAccountModel.id == account_id)
            result = await session.execute(stmt)
            account = result.first()

            if not account:
                return False

            account_model = account[0]
            account_model.is_active = False
            account_model.updated_at = datetime.now(timezone.utc)

            await session.commit()
            return True

    async def delete_connected_account(self, account_id: str) -> bool:
        """
        Permanently delete connected account.
        Returns True if account was deleted, False if not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(ConnectedAccountModel.id == account_id)
            result = await session.execute(stmt)
            account = result.first()

            if not account:
                return False

            await session.delete(account[0])
            await session.commit()
            return True

    async def get_accounts_for_conversation_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get lightweight account data for conversation context."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.is_active == True
            ).order_by(ConnectedAccountModel.created_at)
            result = await session.execute(stmt)
            accounts = result.fetchall()
            return [account[0].to_conversation_context() for account in accounts]

    async def get_connected_accounts_count(self, user_id: str) -> int:
        """Get count of active connected accounts for user."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.is_active == True
            )
            result = await session.execute(stmt)
            return len(result.fetchall())
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
    
    # PersonalContext operations (sync wrappers)
    def get_personal_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get personal context data for user."""
        return self._run_async(self._async_storage.get_personal_context(user_id))
    
    def create_personal_context(self, user_id: str, context_data) -> Dict[str, Any]:
        """Create personal context for user."""
        return self._run_async(self._async_storage.create_personal_context(user_id, context_data))
    
    def update_personal_context(self, user_id: str, updates) -> Optional[Dict[str, Any]]:
        """Update personal context data."""
        return self._run_async(self._async_storage.update_personal_context(user_id, updates))
    
    def create_or_update_personal_context(self, user_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update personal context data."""
        return self._run_async(self._async_storage.create_or_update_personal_context(user_id, context_data))
    
    def delete_personal_context(self, user_id: str) -> bool:
        """Delete personal context by user ID."""
        return self._run_async(self._async_storage.delete_personal_context(user_id))

    # ConnectedAccount operations (sync wrappers)
    def get_connected_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connected accounts for user."""
        return self._run_async(self._async_storage.get_connected_accounts(user_id))

    def get_connected_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get connected account by ID."""
        return self._run_async(self._async_storage.get_connected_account_by_id(account_id))

    def get_connected_account_by_plaid_id(self, user_id: str, plaid_account_id: str) -> Optional[Dict[str, Any]]:
        """Get connected account by Plaid account ID."""
        return self._run_async(self._async_storage.get_connected_account_by_plaid_id(user_id, plaid_account_id))

    def create_connected_account(self, user_id: str, account_data) -> Dict[str, Any]:
        """Create connected account for user."""
        return self._run_async(self._async_storage.create_connected_account(user_id, account_data))

    def update_connected_account(self, account_id: str, updates) -> Optional[Dict[str, Any]]:
        """Update connected account data."""
        return self._run_async(self._async_storage.update_connected_account(account_id, updates))

    def deactivate_connected_account(self, account_id: str) -> bool:
        """Deactivate connected account (soft delete)."""
        return self._run_async(self._async_storage.deactivate_connected_account(account_id))

    def delete_connected_account(self, account_id: str) -> bool:
        """Permanently delete connected account."""
        return self._run_async(self._async_storage.delete_connected_account(account_id))

    def get_accounts_for_conversation_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get lightweight account data for conversation context."""
        return self._run_async(self._async_storage.get_accounts_for_conversation_context(user_id))

    def get_connected_accounts_count(self, user_id: str) -> int:
        """Get count of active connected accounts for user."""
        return self._run_async(self._async_storage.get_connected_accounts_count(user_id))

# Global user storage instance - now SQLite with sync compatibility
user_storage = AsyncUserStorageWrapper()
