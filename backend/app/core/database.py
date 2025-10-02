"""
SQLite-based user storage implementation.
Clean replacement for in-memory storage with persistent data.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlmodel import SQLModel

from .config import settings
from .sqlmodel_models import (
    ConnectedAccountCreate,
    ConnectedAccountModel,
    ConnectedAccountUpdate,
    PersonalContextCreate,
    PersonalContextModel,
    PersonalContextUpdate,
    TransactionCreate,
    TransactionModel,
    TransactionUpdate,
    UserModel,
)

logger = logging.getLogger(__name__)

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
        """Clear all users from storage and all related data. Use with caution."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            # Import all related models
            from .sqlmodel_models import (
                ConnectedAccountModel,
                DependentModel,
                PersonalContextModel,
                SpouseBasicInfoModel,
            )

            # Clear all user-related tables in dependency order (children first)
            # 1. Connected accounts
            connected_accounts_stmt = select(ConnectedAccountModel)
            connected_accounts_result = await session.execute(connected_accounts_stmt)
            connected_accounts = connected_accounts_result.fetchall()
            for account in connected_accounts:
                await session.delete(account[0])

            # 2. Dependents
            dependents_stmt = select(DependentModel)
            dependents_result = await session.execute(dependents_stmt)
            dependents = dependents_result.fetchall()
            for dependent in dependents:
                await session.delete(dependent[0])

            # 3. Spouse basic info
            spouse_stmt = select(SpouseBasicInfoModel)
            spouse_result = await session.execute(spouse_stmt)
            spouses = spouse_result.fetchall()
            for spouse in spouses:
                await session.delete(spouse[0])

            # 4. Personal context
            personal_context_stmt = select(PersonalContextModel)
            personal_context_result = await session.execute(personal_context_stmt)
            personal_contexts = personal_context_result.fetchall()
            for context in personal_contexts:
                await session.delete(context[0])

            # 5. Finally, clear users
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

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context including basic info and personal demographics.
        Uses a single JOIN query for efficiency.
        Returns agent-ready context dict.
        """
        await self._ensure_initialized()

        async with self.session_factory() as session:
            # Single query with LEFT JOIN to get user + personal context
            stmt = (
                select(UserModel, PersonalContextModel)
                .outerjoin(PersonalContextModel, UserModel.id == PersonalContextModel.user_id)
                .where(UserModel.id == user_id)
            )

            result = await session.execute(stmt)
            row = result.first()

            if not row:
                return {}  # User not found

            user_model, personal_context_model = row

            # Build agent-ready context structure
            context = {
                "user_id": user_id,
                "name": user_model.name or "User",
                "email": user_model.email,
                "profile_complete": user_model.profile_complete,
                "demographics": {},
                "financial_context": {}
            }

            # Add personal context demographics if available
            if personal_context_model:
                pc_dict = personal_context_model.to_dict()

                # Map demographics (updated for new PersonalContextModel schema)
                demographics = {}
                if pc_dict.get("age_range"):
                    demographics["age_range"] = pc_dict["age_range"]
                if pc_dict.get("life_stage"):
                    demographics["life_stage"] = pc_dict["life_stage"]
                if pc_dict.get("marital_status"):
                    demographics["marital_status"] = pc_dict["marital_status"]
                if pc_dict.get("occupation_type"):
                    demographics["occupation_type"] = pc_dict["occupation_type"]
                if pc_dict.get("location_context"):
                    demographics["location"] = pc_dict["location_context"]

                context["demographics"] = demographics

                # Map financial context (updated for new PersonalContextModel schema)
                financial_context = {}
                if pc_dict.get("family_structure"):
                    financial_context["family_structure"] = pc_dict["family_structure"]
                if pc_dict.get("total_dependents_count") is not None:
                    financial_context["has_dependents"] = pc_dict["total_dependents_count"] > 0
                    financial_context["dependent_count"] = pc_dict["total_dependents_count"]
                if pc_dict.get("children_count") is not None:
                    financial_context["children_count"] = pc_dict["children_count"]
                if pc_dict.get("caregiving_responsibilities"):
                    financial_context["caregiving_responsibilities"] = pc_dict["caregiving_responsibilities"]

                context["financial_context"] = financial_context

            return context

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
    async def get_connected_accounts(
        self, user_id: str, include_tokens: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all connected accounts for user. Returns list of account dicts.

        Args:
            user_id: User identifier
            include_tokens: If True, includes encrypted_access_token field
                (for internal use only)

        Returns:
            List of account dictionaries
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(ConnectedAccountModel).where(
                ConnectedAccountModel.user_id == user_id,
                ConnectedAccountModel.is_active
            ).order_by(ConnectedAccountModel.created_at)
            result = await session.execute(stmt)
            accounts = result.fetchall()

            if include_tokens:
                # For internal use: include access tokens by adding them to the dict
                return [
                    {**account[0].to_dict(), 'encrypted_access_token': account[0].encrypted_access_token}
                    for account in accounts
                ]
            else:
                # For external use: exclude sensitive fields via to_dict()
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
                # Let SQLModel auto-generate the integer primary key
                account_model = ConnectedAccountModel(
                    user_id=user_id,
                    **account_data.model_dump()
                )
                session.add(account_model)
                await session.commit()
                await session.refresh(account_model)
                return account_model.to_dict()
            except IntegrityError as e:
                await session.rollback()
                raise ValueError(f"Failed to create connected account with Plaid ID {account_data.plaid_account_id} for user {user_id}: {str(e)}")

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
                ConnectedAccountModel.is_active
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
                ConnectedAccountModel.is_active
            )
            result = await session.execute(stmt)
            return len(result.fetchall())

    # =============================================================================
    # Transaction Storage Operations
    # =============================================================================

    async def get_transaction_by_hash(self, canonical_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by canonical hash. Returns transaction dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(TransactionModel).where(TransactionModel.canonical_hash == canonical_hash)
            result = await session.execute(stmt)
            transaction = result.first()
            return transaction[0].to_dict() if transaction else None

    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by Plaid transaction ID. Returns transaction dict or None if not found."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(TransactionModel).where(TransactionModel.transaction_id == transaction_id)
            result = await session.execute(stmt)
            transaction = result.first()
            return transaction[0].to_dict() if transaction else None

    async def get_transactions_for_user(
        self,
        user_id: str,
        limit: Optional[int] = None,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for user with optional filters.
        Returns list of transaction dictionaries.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(TransactionModel).where(TransactionModel.user_id == user_id)

            # Add optional filters
            if account_id:
                stmt = stmt.where(TransactionModel.account_id == account_id)
            if start_date:
                stmt = stmt.where(TransactionModel.date >= start_date)
            if end_date:
                stmt = stmt.where(TransactionModel.date <= end_date)

            # Order by date descending (most recent first)
            stmt = stmt.order_by(TransactionModel.date.desc(), TransactionModel.created_at.desc())

            # Apply limit if specified
            if limit:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            transactions = result.fetchall()
            return [transaction[0].to_dict() for transaction in transactions]

    async def create_transaction(self, transaction_data: TransactionCreate) -> Dict[str, Any]:
        """
        Create transaction in storage.
        Returns the created transaction data.
        Raises ValueError if transaction with canonical_hash already exists.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            try:
                transaction_model = TransactionModel(**transaction_data.model_dump())
                session.add(transaction_model)
                await session.commit()
                await session.refresh(transaction_model)
                return transaction_model.to_dict()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Transaction with canonical hash {transaction_data.canonical_hash} already exists")

    async def update_transaction(self, canonical_hash: str, updates: TransactionUpdate) -> Optional[Dict[str, Any]]:
        """
        Update transaction data.
        Returns updated transaction data or None if transaction not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(TransactionModel).where(TransactionModel.canonical_hash == canonical_hash)
            result = await session.execute(stmt)
            transaction = result.first()

            if not transaction:
                return None

            transaction_model = transaction[0]

            # Update fields from TransactionUpdate
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(transaction_model, field, value)

            transaction_model.updated_at = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(transaction_model)
            return transaction_model.to_dict()

    async def create_or_update_transaction(self, transaction_data: TransactionCreate) -> Dict[str, Any]:
        """
        Create or update transaction data using database upsert (INSERT OR REPLACE).
        Returns the transaction data (created or updated).
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            try:
                # Use SQLite's INSERT OR REPLACE for efficient upsert

                # Build INSERT OR REPLACE statement
                tx_data = transaction_data.model_dump()

                # Execute upsert
                transaction_model = TransactionModel(**tx_data)
                await session.merge(transaction_model)  # SQLAlchemy's upsert method
                await session.commit()
                await session.refresh(transaction_model)
                return transaction_model.to_dict()

            except Exception as e:
                await session.rollback()
                logger.error(f"Error in transaction upsert: {e}")
                raise

    async def delete_transaction(self, canonical_hash: str) -> bool:
        """
        Delete transaction by canonical hash.
        Returns True if transaction was deleted, False if not found.
        """
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(TransactionModel).where(TransactionModel.canonical_hash == canonical_hash)
            result = await session.execute(stmt)
            transaction = result.first()

            if not transaction:
                return False

            await session.delete(transaction[0])
            await session.commit()
            return True

    async def get_transactions_count(self, user_id: str) -> int:
        """Get count of transactions for user."""
        await self._ensure_initialized()
        async with self.session_factory() as session:
            stmt = select(TransactionModel).where(TransactionModel.user_id == user_id)
            result = await session.execute(stmt)
            return len(result.fetchall())

    async def get_spending_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get spending summary for user for the last N days.
        Returns summary with total amounts, category breakdowns, etc.
        """
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        transactions = await self.get_transactions_for_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        # Calculate summary statistics
        total_amount = sum(t['amount'] for t in transactions)
        transaction_count = len(transactions)

        # Group by AI category
        category_summary = {}
        for transaction in transactions:
            category = transaction.get('ai_category', 'Uncategorized')
            if category not in category_summary:
                category_summary[category] = {
                    'count': 0,
                    'total_amount': 0.0,
                    'transactions': []
                }
            category_summary[category]['count'] += 1
            category_summary[category]['total_amount'] += transaction['amount']
            category_summary[category]['transactions'].append(transaction['canonical_hash'])

        return {
            'user_id': user_id,
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
            'total_amount': total_amount,
            'transaction_count': transaction_count,
            'category_summary': category_summary,
            'most_recent_transaction': transactions[0] if transactions else None
        }

    async def batch_create_transactions(self, transactions: List[TransactionCreate]) -> Dict[str, Any]:
        """
        Efficiently store multiple transactions using database indexes for duplicate prevention.

        Args:
            transactions: List of TransactionCreate objects to store

        Returns:
            Dict with storage statistics: stored, duplicates, errors
        """
        if not transactions:
            return {"stored": 0, "duplicates": 0, "errors": 0}

        await self._ensure_initialized()

        stored_count = 0
        duplicate_count = 0
        error_count = 0

        # Process each transaction individually to handle duplicates properly
        for tx_data in transactions:
            try:
                async with self.session_factory() as session:
                    # Create transaction model and let database indexes handle duplicates
                    transaction_model = TransactionModel(**tx_data.model_dump())
                    session.add(transaction_model)
                    await session.commit()
                    stored_count += 1
                    logger.debug(f"Stored transaction: {tx_data.canonical_hash}")

            except Exception as e:
                # Check if it's a duplicate (integrity error)
                if "UNIQUE constraint failed" in str(e) or "PRIMARY KEY constraint failed" in str(e):
                    duplicate_count += 1
                    logger.debug(f"Duplicate transaction detected by database: {tx_data.canonical_hash}")
                else:
                    error_count += 1
                    logger.error(f"Error storing transaction {tx_data.canonical_hash}: {e}")

        logger.info(f"Batch storage: {stored_count} stored, {duplicate_count} duplicates, {error_count} errors")

        return {
            "stored": stored_count,
            "duplicates": duplicate_count,
            "errors": error_count
        }
# Async-to-sync wrapper for compatibility with existing sync code
class AsyncUserStorageWrapper:
    """Wrapper to make async SQLite storage work with sync code."""

    def __init__(self):
        self._async_storage = SQLiteUserStorage()
        self._loop = None

    def _get_or_create_loop(self):
        """Get current event loop or create a new one."""
        try:
            # Use asyncio.get_running_loop() to avoid deprecation warning
            return asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new one instead of using deprecated get_event_loop()
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

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get complete user context including basic info and personal demographics."""
        return self._run_async(self._async_storage.get_user_context(user_id))

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
    def get_connected_accounts(self, user_id: str, include_tokens: bool = False) -> List[Dict[str, Any]]:
        """Get all connected accounts for user."""
        return self._run_async(self._async_storage.get_connected_accounts(user_id, include_tokens))

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

    # Transaction operations (sync wrappers)
    def get_transaction_by_hash(self, canonical_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction by canonical hash."""
        return self._run_async(self._async_storage.get_transaction_by_hash(canonical_hash))

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by Plaid transaction ID."""
        return self._run_async(self._async_storage.get_transaction_by_id(transaction_id))

    def get_transactions_for_user(
        self,
        user_id: str,
        limit: Optional[int] = None,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for user with optional filters."""
        return self._run_async(self._async_storage.get_transactions_for_user(
            user_id, limit, account_id, start_date, end_date
        ))

    def create_transaction(self, transaction_data) -> Dict[str, Any]:
        """Create transaction in storage."""
        return self._run_async(self._async_storage.create_transaction(transaction_data))

    def update_transaction(self, canonical_hash: str, updates) -> Optional[Dict[str, Any]]:
        """Update transaction data."""
        return self._run_async(self._async_storage.update_transaction(canonical_hash, updates))

    def create_or_update_transaction(self, transaction_data) -> Dict[str, Any]:
        """Create or update transaction data based on canonical hash."""
        return self._run_async(self._async_storage.create_or_update_transaction(transaction_data))

    def delete_transaction(self, canonical_hash: str) -> bool:
        """Delete transaction by canonical hash."""
        return self._run_async(self._async_storage.delete_transaction(canonical_hash))

    def get_transactions_count(self, user_id: str) -> int:
        """Get count of transactions for user."""
        return self._run_async(self._async_storage.get_transactions_count(user_id))

    def get_spending_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get spending summary for user for the last N days."""
        return self._run_async(self._async_storage.get_spending_summary(user_id, days))

    def batch_create_transactions(self, transactions: List[TransactionCreate]) -> Dict[str, Any]:
        """Efficiently store multiple transactions using database indexes for duplicate prevention."""
        return self._run_async(self._async_storage.batch_create_transactions(transactions))

# Global user storage instance - now SQLite with sync compatibility
user_storage = AsyncUserStorageWrapper()
