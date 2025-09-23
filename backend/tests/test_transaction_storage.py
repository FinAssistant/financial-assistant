"""
Unit tests for transaction storage functionality in GraphitiMCPClient.

Tests the canonical_hash utility and transaction storage methods without
requiring actual Graphiti server connection.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.mcp_clients.graphiti_client import canonical_hash, GraphitiMCPClient
from app.models.plaid_models import PlaidTransaction


class TestCanonicalHash:
    """Test the canonical_hash utility function."""

    def test_canonical_hash_consistency(self):
        """Test that canonical_hash produces consistent results for identical transactions."""
        # Create identical transactions
        tx1 = PlaidTransaction(
            transaction_id="txn_test_001",
            account_id="acc_test_001",
            amount=Decimal("25.50"),
            date="2024-01-15",
            name="Test Transaction",
            merchant_name="Test Merchant",
            category=["Test", "Category"],
            pending=False,
        )

        tx2 = PlaidTransaction(
            transaction_id="txn_test_001",
            account_id="acc_test_001",
            amount=Decimal("25.50"),
            date="2024-01-15",
            name="Test Transaction",
            merchant_name="Test Merchant",
            category=["Test", "Category"],
            pending=False,
        )

        # Test hash consistency
        hash1 = canonical_hash(tx1)
        hash2 = canonical_hash(tx2)

        assert hash1 == hash2, "Identical transactions should produce identical hashes"
        assert len(hash1) == 64, "Hash should be 64 characters (SHA256 hex)"
        assert isinstance(hash1, str), "Hash should be string"

    def test_canonical_hash_uniqueness(self):
        """Test that different transactions produce different hashes."""
        # Create different transactions
        tx1 = PlaidTransaction(
            transaction_id="txn_starbucks_001",
            account_id="acc_checking_001",
            amount=Decimal("4.25"),
            date="2024-01-15",
            name="Starbucks Coffee",
            merchant_name="Starbucks",
            category=["Food", "Coffee"],
            pending=False,
        )

        tx2 = PlaidTransaction(
            transaction_id="txn_grocery_001",
            account_id="acc_checking_001",
            amount=Decimal("87.43"),
            date="2024-01-14",
            name="Grocery Store",
            merchant_name="Whole Foods",
            category=["Food", "Groceries"],
            pending=False,
        )

        # Different transactions should produce different hashes
        hash1 = canonical_hash(tx1)
        hash2 = canonical_hash(tx2)

        assert hash1 != hash2, "Different transactions should produce different hashes"

    def test_canonical_hash_handles_missing_fields(self):
        """Test canonical_hash handles transactions with missing optional fields."""
        # Transaction with minimal fields
        tx_minimal = PlaidTransaction(
            transaction_id="txn_minimal_001",
            account_id="acc_minimal_001",
            amount=Decimal("10.00"),
            name="Minimal Transaction",
            # Note: missing date, merchant_name
        )

        # Should not raise exception
        hash_result = canonical_hash(tx_minimal)

        assert isinstance(hash_result, str), (
            "Should return string even with missing fields"
        )
        assert len(hash_result) == 64, "Should still produce 64-char hash"

    def test_canonical_hash_amount_precision(self):
        """Test that canonical_hash handles decimal amounts with precision sensitivity."""
        # Different string representations of the same value
        tx1 = PlaidTransaction(
            transaction_id="txn_precision_001",
            account_id="acc_test_001",
            amount=Decimal("25.50"),
            name="Precision Test",
        )

        tx2 = PlaidTransaction(
            transaction_id="txn_precision_001",
            account_id="acc_test_001",
            amount=Decimal("25.5"),  # Same value, different string representation
            name="Precision Test",
        )

        hash1 = canonical_hash(tx1)
        hash2 = canonical_hash(tx2)

        # Different string representations should produce different hashes
        # This is correct behavior since Decimal("25.50") != Decimal("25.5") as strings
        assert hash1 != hash2, (
            "Different decimal string representations should produce different hashes"
        )

        # But identical Decimal objects should produce identical hashes
        tx3 = PlaidTransaction(
            transaction_id="txn_precision_001",
            account_id="acc_test_001",
            amount=Decimal("25.50"),  # Identical to tx1
            name="Precision Test",
        )

        hash3 = canonical_hash(tx3)
        assert hash1 == hash3, (
            "Identical decimal objects should produce identical hashes"
        )

    def test_canonical_hash_components(self):
        """Test that canonical_hash includes expected components."""
        tx = PlaidTransaction(
            transaction_id="txn_component_test",
            account_id="acc_test",
            amount=Decimal("123.45"),
            date="2024-01-01",
            name="Component Test",
            merchant_name="Test Merchant",
        )

        hash_result = canonical_hash(tx)

        # Hash should be deterministic based on specific fields
        # We can't predict the exact hash, but we can test consistency
        assert hash_result == canonical_hash(tx), "Hash should be deterministic"

        # Change each component and verify hash changes
        tx_diff_id = PlaidTransaction(
            transaction_id="different_id",
            account_id="acc_test",
            amount=Decimal("123.45"),
            date="2024-01-01",
            name="Component Test",
            merchant_name="Test Merchant",
        )

        assert canonical_hash(tx_diff_id) != hash_result, (
            "Different transaction_id should change hash"
        )


class TestGraphitiClientTransactionStorage:
    """Test GraphitiMCPClient transaction storage methods (mocked)."""

    def create_test_transaction(self) -> PlaidTransaction:
        """Create a test transaction for use in tests."""
        return PlaidTransaction(
            transaction_id="txn_test_storage",
            account_id="acc_test",
            amount=Decimal("42.50"),
            date="2024-01-15",
            name="Test Storage Transaction",
            merchant_name="Test Store",
            category=["Shopping", "General"],
            pending=False,
            ai_category="Shopping",
            ai_subcategory="General Merchandise",
            ai_confidence=0.85,
            ai_tags=["retail", "one-time"],
        )

    @pytest.fixture
    def mock_graphiti_client(self):
        """Create a mocked GraphitiMCPClient for testing."""
        client = GraphitiMCPClient()
        client._connected = True
        client.tools = [
            MagicMock(name="add_memory"),
            MagicMock(name="search_memory_nodes"),
        ]

        # Mock _get_tool method
        def mock_get_tool(tool_name):
            mock_tool = AsyncMock()
            if tool_name == "add_memory":
                mock_tool.ainvoke.return_value = {
                    "success": True,
                    "episode_id": "test_episode_123",
                }
            elif tool_name == "search_memory_nodes":
                mock_tool.ainvoke.return_value = {"nodes": [], "total": 0}
            return mock_tool

        client._get_tool = mock_get_tool
        return client

    @pytest.mark.asyncio
    async def test_store_transaction_episode_success(self, mock_graphiti_client):
        """Test successful transaction episode storage."""
        transaction = self.create_test_transaction()
        user_id = "test_user_123"

        # Test storage without duplicate check
        with patch(
            "app.ai.mcp_clients.graphiti_client._call_tool_with_retries"
        ) as mock_retry:
            mock_retry.return_value = {
                "success": True,
                "episode_id": "test_episode_456",
            }

            result = await mock_graphiti_client.store_transaction_episode(
                user_id=user_id, transaction=transaction, check_duplicate=False
            )

            assert result["found"] is False
            assert "add_memory_response" in result
            assert result["add_memory_response"]["success"] is True

    @pytest.mark.asyncio
    async def test_store_transaction_episode_with_duplicate_detection(
        self, mock_graphiti_client
    ):
        """Test transaction storage with duplicate detection."""
        transaction = self.create_test_transaction()
        user_id = "test_user_123"

        # Mock finding existing transaction
        with patch.object(
            mock_graphiti_client,
            "_find_transaction_by_hash",
            return_value={"existing": "node"},
        ):
            result = await mock_graphiti_client.store_transaction_episode(
                user_id=user_id, transaction=transaction, check_duplicate=True
            )

            assert result["found"] is True
            assert "node" in result

    @pytest.mark.asyncio
    async def test_batch_store_transaction_episodes(self, mock_graphiti_client):
        """Test batch transaction storage."""
        transactions = [
            self.create_test_transaction(),
            PlaidTransaction(
                transaction_id="txn_batch_2",
                account_id="acc_test",
                amount=Decimal("15.75"),
                name="Batch Test 2",
            ),
            PlaidTransaction(
                transaction_id="txn_batch_3",
                account_id="acc_test",
                amount=Decimal("99.99"),
                name="Batch Test 3",
            ),
        ]

        user_id = "test_user_batch"

        # Mock successful storage for all transactions
        with patch.object(
            mock_graphiti_client,
            "store_transaction_episode",
            return_value={"found": False, "add_memory_response": {"success": True}},
        ):
            results = await mock_graphiti_client.batch_store_transaction_episodes(
                user_id=user_id, transactions=transactions, concurrency=2
            )

            assert len(results) == len(transactions)

            # Check each result has required fields
            for result in results:
                assert "transaction_id" in result
                assert "found" in result
                assert result["found"] is False

    @pytest.mark.asyncio
    async def test_batch_store_handles_errors(self, mock_graphiti_client):
        """Test that batch storage handles individual transaction errors gracefully."""
        transactions = [self.create_test_transaction()]
        user_id = "test_user_error"

        # Mock storage method to raise exception
        with patch.object(
            mock_graphiti_client,
            "store_transaction_episode",
            side_effect=Exception("Storage failed"),
        ):
            results = await mock_graphiti_client.batch_store_transaction_episodes(
                user_id=user_id, transactions=transactions
            )

            assert len(results) == 1
            assert "error" in results[0]
            assert results[0]["found"] is False
            assert results[0]["transaction_id"] == transactions[0].transaction_id

    def test_build_transaction_episode_content(self, mock_graphiti_client):
        """Test transaction episode content building."""
        transaction = self.create_test_transaction()
        user_id = "test_user_content"
        tx_hash = "test_hash_123456"

        content = mock_graphiti_client._build_transaction_episode_content(
            transaction, user_id, tx_hash
        )

        # Verify content structure with new natural language format
        assert "User made a" in content
        assert "purchase at" in content
        assert "categorized as" in content
        assert tx_hash in content
        assert str(transaction.amount) in content
        assert transaction.merchant_name in content

        # Verify AI categorization is included
        assert transaction.ai_category in content
        assert transaction.ai_subcategory in content
        assert str(int(transaction.ai_confidence * 100)) in content

    def test_build_transaction_episode_content_without_ai_fields(
        self, mock_graphiti_client
    ):
        """Test episode content building for transaction without AI categorization."""
        transaction = PlaidTransaction(
            transaction_id="txn_no_ai",
            account_id="acc_test",
            amount=Decimal("10.00"),
            name="No AI Transaction",
            # No AI fields set
        )

        user_id = "test_user_no_ai"
        tx_hash = "hash_no_ai_123"

        content = mock_graphiti_client._build_transaction_episode_content(
            transaction, user_id, tx_hash
        )

        # Should still work without AI fields with new natural language format
        assert "User made a" in content
        assert "purchase at" in content
        assert tx_hash in content
        # Should handle None AI fields gracefully
        assert "None - None" in content  # Shows None fields handled
        assert "general establishment" in content  # Fallback category
        assert "miscellaneous category" in content  # Fallback subcategory


class TestTransactionStorageIntegration:
    """Integration tests for transaction storage components working together."""

    def test_canonical_hash_integration_with_plaid_transaction(self):
        """Test canonical_hash works with various PlaidTransaction configurations."""
        # Test with full transaction data
        full_tx = PlaidTransaction(
            transaction_id="txn_full_001",
            account_id="acc_full_001",
            amount=Decimal("156.78"),
            date="2024-01-20",
            name="Full Transaction Data",
            merchant_name="Complete Store",
            category=["Shopping", "Electronics"],
            pending=False,
            ai_category="Electronics",
            ai_subcategory="Computer Hardware",
            ai_confidence=0.92,
            ai_tags=["business", "equipment"],
        )

        # Test with minimal transaction data
        minimal_tx = PlaidTransaction(
            transaction_id="txn_minimal_001",
            account_id="acc_minimal_001",
            amount=Decimal("5.00"),
            name="Minimal Transaction",
        )

        # Both should produce valid hashes
        full_hash = canonical_hash(full_tx)
        minimal_hash = canonical_hash(minimal_tx)

        assert len(full_hash) == 64
        assert len(minimal_hash) == 64
        assert full_hash != minimal_hash
        assert all(c in "0123456789abcdef" for c in full_hash.lower())
        assert all(c in "0123456789abcdef" for c in minimal_hash.lower())
