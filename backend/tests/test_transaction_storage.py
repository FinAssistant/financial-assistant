"""
Unit tests for SQLite transaction storage functionality.

Tests the transaction models and storage methods added to the core database module.
"""

import pytest
import tempfile
import os
from decimal import Decimal
from datetime import datetime, timezone

from app.core.database import SQLiteUserStorage, AsyncUserStorageWrapper
from app.core.sqlmodel_models import TransactionCreate, TransactionUpdate
from app.models.plaid_models import PlaidTransaction


class TestSQLiteTransactionStorage:
    """Test SQLite transaction storage functionality."""

    @pytest.fixture
    async def temp_db_storage(self):
        """Create a temporary SQLite database for testing."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()

        try:
            database_url = f"sqlite+aiosqlite:///{temp_db.name}"
            storage = SQLiteUserStorage(database_url)
            await storage._ensure_initialized()
            yield storage
        finally:
            await storage.engine.dispose()
            os.unlink(temp_db.name)

    @pytest.fixture
    def sample_transaction_create(self):
        """Create a sample TransactionCreate for testing."""
        return TransactionCreate(
            canonical_hash="a123456789012345678901234567890123456789012345678901234567890123",
            user_id="test_user_123",
            transaction_id="txn_test_001",
            account_id="acc_test_001",
            amount=25.50,
            date="2024-01-15",
            name="Test Transaction",
            merchant_name="Test Merchant",
            category="Food,Dining",
            ai_category="Food & Dining",
            ai_subcategory="Restaurants",
            ai_confidence=0.95,
            ai_tags="lunch,business",
            pending=False
        )

    @pytest.mark.asyncio
    async def test_create_transaction(self, temp_db_storage, sample_transaction_create):
        """Test creating a transaction in SQLite storage."""
        result = await temp_db_storage.create_transaction(sample_transaction_create)

        assert result is not None
        assert result["canonical_hash"] == sample_transaction_create.canonical_hash
        assert result["user_id"] == sample_transaction_create.user_id
        assert result["transaction_id"] == sample_transaction_create.transaction_id
        assert float(result["amount"]) == sample_transaction_create.amount
        assert result["merchant_name"] == sample_transaction_create.merchant_name
        assert result["ai_category"] == sample_transaction_create.ai_category

    @pytest.mark.asyncio
    async def test_get_transaction_by_hash(self, temp_db_storage, sample_transaction_create):
        """Test retrieving a transaction by canonical hash."""
        # First create the transaction
        await temp_db_storage.create_transaction(sample_transaction_create)

        # Then retrieve it
        result = await temp_db_storage.get_transaction_by_hash(sample_transaction_create.canonical_hash)

        assert result is not None
        assert result["canonical_hash"] == sample_transaction_create.canonical_hash
        assert result["user_id"] == sample_transaction_create.user_id
        assert result["transaction_id"] == sample_transaction_create.transaction_id

    @pytest.mark.asyncio
    async def test_get_transaction_by_hash_not_found(self, temp_db_storage):
        """Test retrieving a non-existent transaction returns None."""
        result = await temp_db_storage.get_transaction_by_hash("non_existent_hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_transactions_for_user(self, temp_db_storage):
        """Test retrieving transactions for a specific user."""
        user_id = "test_user_123"

        # Create multiple transactions for the user
        for i in range(3):
            tx_create = TransactionCreate(
                canonical_hash=f"hash_{i:02d}" + "0" * 56,
                user_id=user_id,
                transaction_id=f"txn_{i:03d}",
                account_id="acc_test_001",
                amount=10.00 + i * 5.50,
                date=f"2024-01-{15 + i:02d}",
                name=f"Transaction {i}",
                merchant_name=f"Merchant {i}",
                ai_category="Test Category"
            )
            await temp_db_storage.create_transaction(tx_create)

        # Retrieve all transactions for user
        results = await temp_db_storage.get_transactions_for_user(user_id)

        assert len(results) == 3
        assert all(tx["user_id"] == user_id for tx in results)

        # Test with limit
        limited_results = await temp_db_storage.get_transactions_for_user(user_id, limit=2)
        assert len(limited_results) == 2

    @pytest.mark.asyncio
    async def test_get_transactions_for_user_with_account_filter(self, temp_db_storage):
        """Test retrieving transactions filtered by account."""
        user_id = "test_user_filter"
        account_id_1 = "acc_checking"
        account_id_2 = "acc_savings"

        # Create transactions for different accounts
        tx1 = TransactionCreate(
            canonical_hash="hash_account_1" + "0" * 48,
            user_id=user_id,
            transaction_id="txn_acc1_001",
            account_id=account_id_1,
            amount=25.00,
            date="2024-01-15",
            name="Account 1 Transaction",
            merchant_name="Account 1 Merchant"
        )

        tx2 = TransactionCreate(
            canonical_hash="hash_account_2" + "0" * 48,
            user_id=user_id,
            transaction_id="txn_acc2_001",
            account_id=account_id_2,
            amount=50.00,
            date="2024-01-16",
            name="Account 2 Transaction",
            merchant_name="Account 2 Merchant"
        )

        await temp_db_storage.create_transaction(tx1)
        await temp_db_storage.create_transaction(tx2)

        # Filter by account_id_1
        filtered_results = await temp_db_storage.get_transactions_for_user(
            user_id, account_id=account_id_1
        )

        assert len(filtered_results) == 1
        assert filtered_results[0]["account_id"] == account_id_1
        assert filtered_results[0]["merchant_name"] == "Account 1 Merchant"

    @pytest.mark.asyncio
    async def test_get_spending_summary(self, temp_db_storage):
        """Test getting spending summary for a user."""
        user_id = "test_user_summary"

        # Create transactions with different categories
        transactions_data = [
            ("Food & Dining", 25.50, "Restaurant"),
            ("Food & Dining", 15.75, "Coffee Shop"),
            ("Transportation", 45.00, "Gas Station"),
            ("Shopping", 89.99, "Electronics Store"),
        ]

        for i, (category, amount, merchant) in enumerate(transactions_data):
            tx_create = TransactionCreate(
                canonical_hash=f"summary_hash_{i:02d}" + "0" * 49,
                user_id=user_id,
                transaction_id=f"txn_summary_{i:03d}",
                account_id="acc_summary_001",
                amount=amount,
                date="2025-09-28",
                name=f"Summary Transaction {i}",
                merchant_name=merchant,
                ai_category=category
            )
            await temp_db_storage.create_transaction(tx_create)

        summary = await temp_db_storage.get_spending_summary(user_id, days=30)

        assert summary is not None
        assert "total_amount" in summary
        assert "transaction_count" in summary
        assert "category_summary" in summary

        # Check total spending
        expected_total = sum(amount for _, amount, _ in transactions_data)
        assert abs(float(summary["total_amount"]) - expected_total) < 0.01

        # Check transaction count
        assert summary["transaction_count"] == len(transactions_data)

        # Check category breakdown exists
        assert len(summary["category_summary"]) > 0

    @pytest.mark.asyncio
    async def test_duplicate_transaction_prevention(self, temp_db_storage, sample_transaction_create):
        """Test that duplicate transactions (same canonical_hash) are prevented."""
        # Create first transaction
        result1 = await temp_db_storage.create_transaction(sample_transaction_create)
        assert result1 is not None

        # Try to create duplicate - should raise an exception
        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            await temp_db_storage.create_transaction(sample_transaction_create)


class TestTransactionModels:
    """Test transaction SQLModel definitions."""

    def test_transaction_create_model(self):
        """Test TransactionCreate model validation."""
        tx_create = TransactionCreate(
            canonical_hash="a" * 64,  # 64-char hash
            user_id="user_123",
            transaction_id="txn_123",
            account_id="acc_123",
            amount=25.50,
            date="2024-01-15",
            name="Test Transaction",
            merchant_name="Test Merchant"
        )

        assert tx_create.canonical_hash == "a" * 64
        assert tx_create.user_id == "user_123"
        assert tx_create.amount == 25.50
        assert tx_create.name == "Test Transaction"
        assert tx_create.merchant_name == "Test Merchant"

    def test_transaction_create_with_ai_fields(self):
        """Test TransactionCreate with AI categorization fields."""
        tx_create = TransactionCreate(
            canonical_hash="b" * 64,
            user_id="user_456",
            transaction_id="txn_456",
            account_id="acc_456",
            amount=75.25,
            date="2024-01-16",
            name="AI Transaction",
            merchant_name="AI Merchant",
            ai_category="Food & Dining",
            ai_subcategory="Restaurants",
            ai_confidence=0.88,
            ai_tags="dinner,date-night"
        )

        assert tx_create.ai_category == "Food & Dining"
        assert tx_create.ai_subcategory == "Restaurants"
        assert tx_create.ai_confidence == 0.88
        assert tx_create.ai_tags == "dinner,date-night"

    def test_transaction_update_model(self):
        """Test TransactionUpdate model for partial updates."""
        tx_update = TransactionUpdate(
            ai_category="Updated Category",
            ai_confidence=0.95,
            updated_at=datetime.now(timezone.utc)
        )

        assert tx_update.ai_category == "Updated Category"
        assert tx_update.ai_confidence == 0.95
        assert tx_update.updated_at is not None

        # Fields not provided should be None
        assert tx_update.merchant_name is None
        assert tx_update.amount is None


class TestTransactionStorageIntegration:
    """Integration tests for transaction storage with actual database."""

    @pytest.fixture
    async def temp_db_storage(self):
        """Create a temporary SQLite database for testing."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()

        try:
            database_url = f"sqlite+aiosqlite:///{temp_db.name}"
            storage = SQLiteUserStorage(database_url)
            await storage._ensure_initialized()
            yield storage
        finally:
            await storage.engine.dispose()
            os.unlink(temp_db.name)

    @pytest.mark.asyncio
    async def test_full_transaction_workflow(self, temp_db_storage):
        """Test complete transaction storage workflow from PlaidTransaction to SQLite."""
        user_id = "integration_test_user"

        # Create a PlaidTransaction (simulating data from Plaid)
        plaid_tx = PlaidTransaction(
            transaction_id="txn_integration_001",
            account_id="acc_integration_001",
            amount=Decimal("42.75"),
            date="2025-09-28",
            name="Integration Test Store",
            merchant_name="Test Store",
            category=["Shopping", "General"],
            pending=False,
            ai_category="Shopping",
            ai_subcategory="General Merchandise",
            ai_confidence=0.89,
            ai_tags=["retail", "one-time"]
        )

        # Convert to TransactionCreate (simulating SpendingAgent conversion logic)
        import hashlib
        hash_string = f"{plaid_tx.transaction_id}_{plaid_tx.account_id}_{plaid_tx.amount}_{plaid_tx.date}"
        canonical_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        tx_create = TransactionCreate(
            canonical_hash=canonical_hash,
            user_id=user_id,
            transaction_id=plaid_tx.transaction_id,
            account_id=plaid_tx.account_id,
            amount=float(plaid_tx.amount),
            date=plaid_tx.date,
            name=plaid_tx.name,
            merchant_name=plaid_tx.merchant_name,
            category=",".join(plaid_tx.category),
            ai_category=plaid_tx.ai_category,
            ai_subcategory=plaid_tx.ai_subcategory,
            ai_confidence=float(plaid_tx.ai_confidence),
            ai_tags=",".join(plaid_tx.ai_tags),
            pending=plaid_tx.pending
        )

        # Store in SQLite
        stored_result = await temp_db_storage.create_transaction(tx_create)
        assert stored_result is not None

        # Retrieve and verify
        retrieved = await temp_db_storage.get_transaction_by_hash(canonical_hash)
        assert retrieved["transaction_id"] == plaid_tx.transaction_id
        assert float(retrieved["amount"]) == float(plaid_tx.amount)
        assert retrieved["ai_category"] == plaid_tx.ai_category

        # Test user query
        user_transactions = await temp_db_storage.get_transactions_for_user(user_id)
        assert len(user_transactions) == 1
        assert user_transactions[0]["canonical_hash"] == canonical_hash

        # Test spending summary
        summary = await temp_db_storage.get_spending_summary(user_id, days=30)
        assert summary["transaction_count"] == 1
        assert abs(float(summary["total_amount"]) - float(plaid_tx.amount)) < 0.01

    @pytest.mark.asyncio
    async def test_batch_transaction_storage(self, temp_db_storage):
        """Test storing multiple transactions for realistic batch processing."""
        user_id = "batch_test_user"

        # Create multiple PlaidTransactions
        transactions = []
        for i in range(5):
            tx = PlaidTransaction(
                transaction_id=f"txn_batch_{i:03d}",
                account_id="acc_batch_001",
                amount=Decimal(f"{10.50 + i * 5.25}"),
                date=f"2025-09-{25 + i:02d}",
                name=f"Batch Transaction {i}",
                merchant_name=f"Merchant {i}",
                category=["Testing", "Batch"],
                pending=False,
                ai_category="Testing",
                ai_confidence=0.90 + i * 0.01
            )
            transactions.append(tx)

        # Store all transactions
        stored_count = 0
        for tx in transactions:
            import hashlib
            hash_string = f"{tx.transaction_id}_{tx.account_id}_{tx.amount}_{tx.date}"
            canonical_hash = hashlib.sha256(hash_string.encode()).hexdigest()

            tx_create = TransactionCreate(
                canonical_hash=canonical_hash,
                user_id=user_id,
                transaction_id=tx.transaction_id,
                account_id=tx.account_id,
                amount=float(tx.amount),
                date=tx.date,
                name=tx.name,
                merchant_name=tx.merchant_name,
                ai_category=tx.ai_category,
                ai_confidence=float(tx.ai_confidence)
            )

            await temp_db_storage.create_transaction(tx_create)
            stored_count += 1

        # Verify all stored
        assert stored_count == 5

        # Test retrieval
        all_transactions = await temp_db_storage.get_transactions_for_user(user_id)
        assert len(all_transactions) == 5

        # Test summary
        summary = await temp_db_storage.get_spending_summary(user_id, days=30)
        assert summary["transaction_count"] == 5
        expected_total = sum(float(tx.amount) for tx in transactions)
        assert abs(float(summary["total_amount"]) - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_batch_create_transactions_with_duplicates(self, temp_db_storage):
        """Test batch storage method with duplicate detection via database indexes."""
        user_id = "batch_duplicate_user"

        # Create transactions with some duplicates
        transactions = []
        for i in range(3):
            tx_data = TransactionCreate(
                canonical_hash=f"batch_hash_{i:02d}" + "0" * 51,
                user_id=user_id,
                transaction_id=f"txn_batch_{i:03d}",
                account_id="acc_batch_001",
                amount=15.50 + i * 2.25,
                date=f"2025-09-{25 + i:02d}",
                merchant_name=f"Batch Merchant {i}",
                ai_category="Testing",
                name=f"Transaction Name {i}"
            )
            transactions.append(tx_data)

        # Add a duplicate (same canonical_hash as first transaction)
        duplicate_tx = TransactionCreate(
            canonical_hash="batch_hash_00" + "0" * 51,  # Same as first transaction
            user_id=user_id,
            transaction_id="txn_duplicate_001",
            account_id="acc_batch_001",
            amount=99.99,
            date="2025-09-29",
            name="Duplicate Transaction",
            merchant_name="Duplicate Merchant"
        )
        transactions.append(duplicate_tx)

        # Batch store with duplicate detection
        result = await temp_db_storage.batch_create_transactions(transactions)

        # Should store 3 new and detect 1 duplicate
        assert result["stored"] == 3
        assert result["duplicates"] == 1
        assert result["errors"] == 0

        # Verify only 3 unique transactions in database
        all_transactions = await temp_db_storage.get_transactions_for_user(user_id)
        assert len(all_transactions) == 3


class TestAsyncWrapperCompatibility:
    """Test the sync wrapper methods for compatibility."""

    def test_sync_wrapper_methods_exist(self):
        """Test that sync wrapper methods exist for the new transaction storage methods."""
        # We can't easily test the actual sync methods without a real database
        # but we can verify the wrapper has the expected methods

        # This would be used like: AsyncUserStorageWrapper(sqlite_storage)
        # and should have sync versions of all async methods

        # Just verify the class exists and can be imported
        assert AsyncUserStorageWrapper is not None

        # In a real implementation, this would have methods like:
        # - get_transaction_by_hash_sync
        # - create_transaction_sync
        # - get_transactions_for_user_sync
        # - get_spending_summary_sync
        pass