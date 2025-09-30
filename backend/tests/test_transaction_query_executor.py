"""
Unit tests for transaction query executor (SQL generation).

Tests parameterized SQL generation from TransactionQueryIntent.
"""

import pytest
from datetime import date

from app.models.transaction_query_models import (
    TransactionQueryIntent,
    QueryIntent,
    SortOrder,
)
from app.utils.transaction_query_executor import (
    intent_to_sql,
    resolve_date_range,
)


class TestResolveDateRange:
    """Test date range resolution from intent."""

    def test_explicit_date_range(self):
        """Test with explicit start and end dates."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_DATE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            original_query="January transactions"
        )

        start, end = resolve_date_range(intent)
        assert start == "2024-01-01"
        assert end == "2024-01-31"

    def test_days_back(self):
        """Test with days_back parameter."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            days_back=7,
            original_query="Last week"
        )

        start, end = resolve_date_range(intent)
        # Should return dates, not testing exact values as they depend on current date
        assert start is not None
        assert end is not None

    def test_no_date_params(self):
        """Test with no date parameters."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            original_query="All time"
        )

        start, end = resolve_date_range(intent)
        assert start is None
        assert end is None


class TestSearchByMerchantSQL:
    """Test SQL generation for search_by_merchant intent."""

    def test_simple_merchant_search(self):
        """Test basic merchant search with date range."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_MERCHANT,
            merchant_names=["Uber"],
            days_back=7,
            original_query="Show my Uber rides last week"
        )

        sql, params = intent_to_sql(intent, "user_123")

        # Check SQL structure
        assert "SELECT * FROM transactions" in sql
        assert "user_id = :uid" in sql
        assert "merchant_name LIKE :merchant_0" in sql
        assert "date BETWEEN :start_date AND :end_date" in sql
        assert "ORDER BY" in sql

        # Check parameters
        assert params["uid"] == "user_123"
        assert params["merchant_0"] == "%Uber%"
        assert "start_date" in params
        assert "end_date" in params

    def test_multiple_merchants(self):
        """Test searching for multiple merchants."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_MERCHANT,
            merchant_names=["Starbucks", "Dunkin"],
            days_back=30,
            original_query="Coffee shops"
        )

        sql, params = intent_to_sql(intent, "user_456")

        # Check OR conditions for multiple merchants
        assert "merchant_name LIKE :merchant_0" in sql
        assert "merchant_name LIKE :merchant_1" in sql
        assert " OR " in sql

        # Check parameters
        assert params["merchant_0"] == "%Starbucks%"
        assert params["merchant_1"] == "%Dunkin%"

    def test_merchant_search_with_limit(self):
        """Test merchant search with result limit."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_MERCHANT,
            merchant_names=["Amazon"],
            limit=10,
            original_query="Last 10 Amazon purchases"
        )

        sql, params = intent_to_sql(intent, "user_789")

        assert "LIMIT :limit" in sql
        assert params["limit"] == 10


class TestSpendingByCategorySQL:
    """Test SQL generation for spending_by_category intent."""

    def test_basic_category_grouping(self):
        """Test basic spending by category."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            categories=["Food & Dining"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            original_query="Food spending in January"
        )

        sql, params = intent_to_sql(intent, "user_123")

        # Check aggregation
        assert "SUM(amount) as total_amount" in sql
        assert "COUNT(*) as transaction_count" in sql
        assert "AVG(amount) as average_amount" in sql
        assert "GROUP BY ai_category" in sql

        # Check category filter
        assert "ai_category IN (:category_0)" in sql
        assert params["category_0"] == "Food & Dining"

    def test_multiple_categories(self):
        """Test spending across multiple categories."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            categories=["Food & Dining", "Transportation"],
            days_back=30,
            original_query="Food and transport spending"
        )

        sql, params = intent_to_sql(intent, "user_456")

        # Check multiple category parameters
        assert "ai_category IN (:category_0,:category_1)" in sql
        assert params["category_0"] == "Food & Dining"
        assert params["category_1"] == "Transportation"

    def test_category_sorting(self):
        """Test sorting by amount."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            sort_by="amount",
            sort_order=SortOrder.DESC,
            original_query="Top spending categories"
        )

        sql, params = intent_to_sql(intent, "user_789")

        assert "ORDER BY total_amount DESC" in sql


class TestSpendingByMerchantSQL:
    """Test SQL generation for spending_by_merchant intent."""

    def test_merchant_grouping(self):
        """Test grouping spending by merchant."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_MERCHANT,
            days_back=30,
            original_query="Where did I spend the most?"
        )

        sql, params = intent_to_sql(intent, "user_123")

        assert "SUM(amount) as total_amount" in sql
        assert "COUNT(*) as transaction_count" in sql
        assert "GROUP BY merchant_name" in sql
        assert "ORDER BY total_amount DESC" in sql

    def test_merchant_filter_in_grouping(self):
        """Test filtering specific merchants in grouping."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_MERCHANT,
            merchant_names=["Amazon", "Walmart"],
            days_back=30,
            original_query="Amazon vs Walmart spending"
        )

        sql, params = intent_to_sql(intent, "user_456")

        assert "merchant_name LIKE :merchant_0" in sql
        assert "merchant_name LIKE :merchant_1" in sql
        assert params["merchant_0"] == "%Amazon%"
        assert params["merchant_1"] == "%Walmart%"


class TestTransactionsByDateSQL:
    """Test SQL generation for transactions_by_date intent."""

    def test_date_range_query(self):
        """Test querying transactions in date range."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_DATE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            original_query="January transactions"
        )

        sql, params = intent_to_sql(intent, "user_123")

        assert "SELECT * FROM transactions" in sql
        assert "user_id = :uid" in sql
        assert "date BETWEEN :start_date AND :end_date" in sql
        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-01-31"

    def test_date_with_account_filter(self):
        """Test date query with account filter."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_DATE,
            account_id="acc_checking",
            days_back=7,
            original_query="This week's checking transactions"
        )

        sql, params = intent_to_sql(intent, "user_456")

        assert "account_id = :account_id" in sql
        assert params["account_id"] == "acc_checking"


class TestTransactionsByAmountSQL:
    """Test SQL generation for transactions_by_amount intent."""

    def test_min_amount_filter(self):
        """Test filtering by minimum amount."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_AMOUNT,
            min_amount=100.0,
            days_back=30,
            original_query="Transactions over $100"
        )

        sql, params = intent_to_sql(intent, "user_123")

        assert "amount >= :min_amount" in sql
        assert params["min_amount"] == 100.0

    def test_max_amount_filter(self):
        """Test filtering by maximum amount."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_AMOUNT,
            max_amount=50.0,
            days_back=7,
            original_query="Small transactions this week"
        )

        sql, params = intent_to_sql(intent, "user_456")

        assert "amount <= :max_amount" in sql
        assert params["max_amount"] == 50.0

    def test_amount_range(self):
        """Test filtering by amount range."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_AMOUNT,
            min_amount=50.0,
            max_amount=200.0,
            sort_by="amount",
            sort_order=SortOrder.DESC,
            original_query="Mid-range transactions"
        )

        sql, params = intent_to_sql(intent, "user_789")

        assert "amount >= :min_amount" in sql
        assert "amount <= :max_amount" in sql
        assert params["min_amount"] == 50.0
        assert params["max_amount"] == 200.0
        assert "ORDER BY amount DESC" in sql


class TestSpendingSummarySQL:
    """Test SQL generation for spending_summary intent."""

    def test_summary_aggregation(self):
        """Test spending summary with aggregations."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            days_back=30,
            original_query="What's my spending summary?"
        )

        sql, params = intent_to_sql(intent, "user_123")

        # Check all aggregation functions
        assert "COUNT(*) as transaction_count" in sql
        assert "SUM(amount) as total_amount" in sql
        assert "AVG(amount) as average_amount" in sql
        assert "MIN(amount) as min_amount" in sql
        assert "MAX(amount) as max_amount" in sql

    def test_summary_with_date_range(self):
        """Test summary for specific date range."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            original_query="January summary"
        )

        sql, params = intent_to_sql(intent, "user_456")

        assert "date BETWEEN :start_date AND :end_date" in sql
        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-01-31"


class TestSQLInjectionPrevention:
    """Test that parameterized queries prevent SQL injection."""

    def test_merchant_injection_attempt(self):
        """Test that malicious merchant names are parameterized."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_MERCHANT,
            merchant_names=["'; DROP TABLE transactions; --"],
            original_query="Injection attempt"
        )

        sql, params = intent_to_sql(intent, "user_123")

        # SQL structure should be safe
        assert "DROP TABLE" not in sql
        assert "merchant_name LIKE :merchant_0" in sql

        # Malicious input should be in parameters only (safely bound)
        assert params["merchant_0"] == "%'; DROP TABLE transactions; --%"

    def test_category_injection_attempt(self):
        """Test that malicious category names are parameterized."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            categories=["Food' OR '1'='1"],
            original_query="Injection attempt"
        )

        sql, params = intent_to_sql(intent, "user_789")

        # SQL structure should be safe
        assert "OR '1'='1" not in sql
        assert "ai_category IN (:category_0)" in sql

        # Malicious input in parameters
        assert params["category_0"] == "Food' OR '1'='1"


class TestComplexQueries:
    """Test complex queries with multiple filters."""

    def test_complex_merchant_query(self):
        """Test query with multiple filters and conditions."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_MERCHANT,
            merchant_names=["Amazon", "Walmart"],
            min_amount=50.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            account_id="acc_credit",
            sort_by="amount",
            sort_order=SortOrder.DESC,
            limit=20,
            original_query="Complex query"
        )

        sql, params = intent_to_sql(intent, "user_complex")

        # Check all conditions are present
        assert "user_id = :uid" in sql
        assert "merchant_name LIKE" in sql
        assert "date BETWEEN" in sql
        assert "account_id = :account_id" in sql
        assert "ORDER BY amount DESC" in sql
        assert "LIMIT :limit" in sql

        # Check all parameters
        assert params["uid"] == "user_complex"
        assert "merchant_0" in params
        assert "merchant_1" in params
        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-01-31"
        assert params["account_id"] == "acc_credit"
        assert params["limit"] == 20