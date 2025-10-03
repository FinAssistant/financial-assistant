"""
Unit tests for InsightsGenerator service.

Tests SQL query logic for generating spending insights from transaction data.
"""

import pytest
import os
import tempfile
from app.services.insights_generator import InsightsGenerator
from app.core.database import SQLiteUserStorage
from app.core.sqlmodel_models import TransactionCreate


@pytest.fixture
async def storage():
    """Create clean SQLite storage for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as temp_db:
        try:
            database_url = f"sqlite+aiosqlite:///{temp_db.name}"
            storage = SQLiteUserStorage(database_url)
            await storage._ensure_initialized()
            yield storage
        finally:
            await storage.engine.dispose()
            os.unlink(temp_db.name)


@pytest.fixture
async def insights_generator(storage):
    """Create InsightsGenerator instance for testing."""
    return InsightsGenerator(storage=storage, graphiti_client=None)


@pytest.fixture
async def sample_transactions(storage):
    """Create sample transactions for testing."""
    user_id = "test_user_123"

    # Create transactions for current month (January 2025)
    current_month_txns = [
        TransactionCreate(
            canonical_hash="hash_txn_1" + "0" * 54,
            user_id=user_id,
            transaction_id="txn_1",
            account_id="acc_1",
            amount=50.00,
            date="2025-01-05",
            name="Starbucks",
            merchant_name="Starbucks",
            ai_category="Food & Dining",
            ai_subcategory="Coffee Shops",
            ai_confidence=0.95
        ),
        TransactionCreate(
            canonical_hash="hash_txn_2" + "0" * 54,
            user_id=user_id,
            transaction_id="txn_2",
            account_id="acc_1",
            amount=120.00,
            date="2025-01-10",
            name="Whole Foods",
            merchant_name="Whole Foods",
            ai_category="Food & Dining",
            ai_subcategory="Groceries",
            ai_confidence=0.98
        ),
        TransactionCreate(
            canonical_hash="hash_txn_3" + "0" * 54,
            user_id=user_id,
            transaction_id="txn_3",
            account_id="acc_1",
            amount=45.00,
            date="2025-01-15",
            name="Shell Gas",
            merchant_name="Shell",
            ai_category="Transportation",
            ai_subcategory="Gas Stations",
            ai_confidence=0.92
        ),
        TransactionCreate(
            canonical_hash="hash_txn_4" + "0" * 54,
            user_id=user_id,
            transaction_id="txn_4",
            account_id="acc_1",
            amount=200.00,
            date="2025-01-20",
            name="Amazon",
            merchant_name="Amazon",
            ai_category="Shopping",
            ai_subcategory="Online Shopping",
            ai_confidence=0.88
        ),
        TransactionCreate(
            canonical_hash="hash_txn_5" + "0" * 54,
            user_id=user_id,
            transaction_id="txn_5",
            account_id="acc_1",
            amount=80.00,
            date="2025-01-25",
            name="Restaurant",
            merchant_name="Local Restaurant",
            ai_category="Food & Dining",
            ai_subcategory="Restaurants",
            ai_confidence=0.94
        ),
    ]

    # Create transactions for previous month (December 2024)
    previous_month_txns = [
        TransactionCreate(
            canonical_hash="hash_txn_prev_1" + "0" * 49,
            user_id=user_id,
            transaction_id="txn_prev_1",
            account_id="acc_1",
            amount=60.00,
            date="2024-12-05",
            name="Starbucks",
            merchant_name="Starbucks",
            ai_category="Food & Dining",
            ai_subcategory="Coffee Shops",
            ai_confidence=0.95
        ),
        TransactionCreate(
            canonical_hash="hash_txn_prev_2" + "0" * 49,
            user_id=user_id,
            transaction_id="txn_prev_2",
            account_id="acc_1",
            amount=100.00,
            date="2024-12-15",
            name="Whole Foods",
            merchant_name="Whole Foods",
            ai_category="Food & Dining",
            ai_subcategory="Groceries",
            ai_confidence=0.98
        ),
        TransactionCreate(
            canonical_hash="hash_txn_prev_3" + "0" * 49,
            user_id=user_id,
            transaction_id="txn_prev_3",
            account_id="acc_1",
            amount=300.00,
            date="2024-12-20",
            name="Amazon",
            merchant_name="Amazon",
            ai_category="Shopping",
            ai_subcategory="Online Shopping",
            ai_confidence=0.88
        ),
    ]

    # Store all transactions
    all_transactions = current_month_txns + previous_month_txns
    await storage.batch_create_transactions(all_transactions)

    return {
        "user_id": user_id,
        "current_month": current_month_txns,
        "previous_month": previous_month_txns,
        "total_current": sum(t.amount for t in current_month_txns),
        "total_previous": sum(t.amount for t in previous_month_txns)
    }


class TestInsightsGeneratorQueries:
    """Test SQL query methods in InsightsGenerator."""

    @pytest.mark.asyncio
    async def test_get_total_spending_with_data(self, insights_generator, sample_transactions):
        """Test total spending calculation with transaction data."""
        user_id = sample_transactions["user_id"]

        # Query January 2025
        total = await insights_generator.get_total_spending(
            user_id, "2025-01-01", "2025-01-31"
        )

        assert total == sample_transactions["total_current"]
        assert total == 495.00  # 50 + 120 + 45 + 200 + 80

    @pytest.mark.asyncio
    async def test_get_total_spending_no_data(self, insights_generator):
        """Test total spending with no transactions."""
        total = await insights_generator.get_total_spending(
            "nonexistent_user", "2025-01-01", "2025-01-31"
        )

        assert total == 0.0

    @pytest.mark.asyncio
    async def test_get_total_spending_date_range(self, insights_generator, sample_transactions):
        """Test total spending respects date range."""
        user_id = sample_transactions["user_id"]

        # Query only first half of January
        total = await insights_generator.get_total_spending(
            user_id, "2025-01-01", "2025-01-15"
        )

        # Should include: 50 + 120 + 45 = 215
        assert total == 215.00

    @pytest.mark.asyncio
    async def test_get_category_breakdown(self, insights_generator, sample_transactions):
        """Test category breakdown calculation."""
        user_id = sample_transactions["user_id"]

        categories = await insights_generator.get_category_breakdown(
            user_id, "2025-01-01", "2025-01-31", limit=10
        )

        assert len(categories) == 3  # Food & Dining, Transportation, Shopping

        # Check Food & Dining (largest category)
        food_cat = next(c for c in categories if c["name"] == "Food & Dining")
        assert food_cat["amount"] == 250.00  # 50 + 120 + 80
        assert food_cat["percentage"] == pytest.approx(50.5, rel=0.1)  # 250/495 * 100
        assert food_cat["transaction_count"] == 3

        # Check Shopping
        shopping_cat = next(c for c in categories if c["name"] == "Shopping")
        assert shopping_cat["amount"] == 200.00
        assert shopping_cat["percentage"] == pytest.approx(40.4, rel=0.1)

        # Check Transportation
        transport_cat = next(c for c in categories if c["name"] == "Transportation")
        assert transport_cat["amount"] == 45.00
        assert transport_cat["percentage"] == pytest.approx(9.1, rel=0.1)

    @pytest.mark.asyncio
    async def test_get_category_breakdown_empty(self, insights_generator):
        """Test category breakdown with no data."""
        categories = await insights_generator.get_category_breakdown(
            "nonexistent_user", "2025-01-01", "2025-01-31"
        )

        assert categories == []

    @pytest.mark.asyncio
    async def test_get_month_over_month_trend(self, insights_generator, sample_transactions):
        """Test month-over-month trend calculation."""
        user_id = sample_transactions["user_id"]

        # Compare January 2025 to December 2024
        trend = await insights_generator.get_month_over_month_trend(user_id, "2025-01")

        # Current: 495, Previous: 460 (60 + 100 + 300)
        # Change: (495 - 460) / 460 * 100 = 7.6%
        assert trend == pytest.approx(7.6, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_month_over_month_trend_no_previous_data(self, insights_generator, sample_transactions):
        """Test month-over-month trend with no previous month data."""
        user_id = sample_transactions["user_id"]

        # Query a month with no previous data (e.g., November 2024)
        trend = await insights_generator.get_month_over_month_trend(user_id, "2024-11")

        assert trend is None  # Can't calculate without previous data

    @pytest.mark.asyncio
    async def test_get_month_over_month_trend_decrease(self, insights_generator, storage):
        """Test month-over-month trend showing decrease."""
        user_id = "test_user_decrease"

        # Create transactions with decreasing trend
        transactions = [
            TransactionCreate(
                canonical_hash="hash_dec_1" + "0" * 53,
                user_id=user_id,
                transaction_id="txn_dec_1",
                account_id="acc_1",
                amount=500.00,
                date="2025-01-15",
                name="Big Purchase",
                ai_category="Shopping"
            ),
            TransactionCreate(
                canonical_hash="hash_dec_2" + "0" * 53,
                user_id=user_id,
                transaction_id="txn_dec_2",
                account_id="acc_1",
                amount=1000.00,
                date="2024-12-15",
                name="Huge Purchase",
                ai_category="Shopping"
            ),
        ]
        await storage.batch_create_transactions(transactions)

        trend = await insights_generator.get_month_over_month_trend(user_id, "2025-01")

        # (500 - 1000) / 1000 * 100 = -50%
        assert trend == pytest.approx(-50.0, abs=0.1)


class TestInsightsGeneratorOrchestration:
    """Test full insights generation orchestration."""

    @pytest.mark.asyncio
    async def test_generate_spending_insights_full(self, insights_generator, sample_transactions):
        """Test complete insights generation."""
        user_id = sample_transactions["user_id"]

        insights = await insights_generator.generate_spending_insights(user_id, month="2025-01")

        # Verify structure
        assert "total_spending" in insights
        assert "monthly_average" in insights
        assert "period_months" in insights
        assert "top_categories" in insights
        assert "trends" in insights

        # Verify data
        assert insights["total_spending"] == 495.00
        assert insights["monthly_average"] == 495.00  # Same as total for 1 month
        assert insights["period_months"] == 1
        assert len(insights["top_categories"]) > 0
        assert insights["top_categories"][0]["name"] == "Food & Dining"  # Highest spending

        # Verify trends
        trends = insights["trends"]
        assert "month_over_month_change" in trends
        assert trends["month_over_month_change"] == pytest.approx(7.6, abs=0.1)

    @pytest.mark.asyncio
    async def test_generate_spending_insights_defaults_to_current_month(self, insights_generator, sample_transactions):
        """Test that insights default to current month when not specified."""
        user_id = sample_transactions["user_id"]

        # Don't specify month - should default to current
        insights = await insights_generator.generate_spending_insights(user_id)

        # Should return data structure even if no data for current month
        assert "total_spending" in insights
        assert "monthly_average" in insights
        assert "period_months" in insights
        assert "top_categories" in insights
        assert "trends" in insights

    @pytest.mark.asyncio
    async def test_generate_spending_insights_no_data(self, insights_generator):
        """Test insights generation with no transaction data."""
        insights = await insights_generator.generate_spending_insights("no_data_user", month="2025-01")

        assert insights["total_spending"] == 0.0
        assert insights["monthly_average"] == 0.0
        assert insights["period_months"] == 1
        assert insights["top_categories"] == []
        assert insights["trends"]["month_over_month_change"] is None

    @pytest.mark.asyncio
    async def test_generate_spending_insights_invalid_month_format(self, insights_generator):
        """Test error handling for invalid month format."""
        with pytest.raises(ValueError, match="Month must be in YYYY-MM format"):
            await insights_generator.generate_spending_insights("user", month="invalid")

    @pytest.mark.asyncio
    async def test_generate_spending_insights_custom_date_range(self, storage, sample_transactions):
        """Test insights generation with custom date range (no month)."""
        insights_generator = InsightsGenerator(storage)
        user_id = "test_user_123"

        # Create transactions with sample data (combine current and previous month)
        all_transactions = sample_transactions['current_month'] + sample_transactions['previous_month']
        await storage.batch_create_transactions(all_transactions)

        # Use custom date range instead of month
        insights = await insights_generator.generate_spending_insights(
            user_id=user_id,
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        # Should have basic insights
        assert insights["total_spending"] > 0
        assert insights["monthly_average"] > 0
        assert insights["period_months"] == 1  # January = 1 month
        assert len(insights["top_categories"]) > 0

        # Trends should be None for custom date ranges (no month-over-month)
        assert insights["trends"]["month_over_month_change"] is None
        assert insights["trends"]["unusual_spending"] is None
