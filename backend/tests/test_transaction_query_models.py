"""
Unit tests for transaction query models.

Tests the Pydantic models used for LLM-driven transaction query parsing.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.models.transaction_query_models import (
    QueryIntent,
    SortOrder,
    AggregationType,
    TransactionQueryIntent,
    QueryResult,
)


class TestQueryEnums:
    """Test enum definitions for query system."""

    def test_query_intent_enum_values(self):
        """Test that QueryIntent enum has expected values."""
        assert QueryIntent.SPENDING_BY_CATEGORY == "spending_by_category"
        assert QueryIntent.SPENDING_BY_MERCHANT == "spending_by_merchant"
        assert QueryIntent.SPENDING_OVER_TIME == "spending_over_time"
        assert QueryIntent.TRANSACTIONS_BY_AMOUNT == "transactions_by_amount"
        assert QueryIntent.TRANSACTIONS_BY_DATE == "transactions_by_date"
        assert QueryIntent.SEARCH_BY_MERCHANT == "search_by_merchant"
        assert QueryIntent.SEARCH_BY_DESCRIPTION == "search_by_description"
        assert QueryIntent.RECURRING_TRANSACTIONS == "recurring_transactions"
        assert QueryIntent.SPENDING_SUMMARY == "spending_summary"
        assert QueryIntent.UNKNOWN == "unknown"

    def test_sort_order_enum_values(self):
        """Test that SortOrder enum has expected values."""
        assert SortOrder.ASC == "asc"
        assert SortOrder.DESC == "desc"

    def test_aggregation_type_enum_values(self):
        """Test that AggregationType enum has expected values."""
        assert AggregationType.SUM == "sum"
        assert AggregationType.AVERAGE == "average"
        assert AggregationType.COUNT == "count"
        assert AggregationType.MIN == "min"
        assert AggregationType.MAX == "max"


class TestTransactionQueryIntent:
    """Test TransactionQueryIntent model validation and structure."""

    def test_minimal_valid_intent(self):
        """Test creating a minimal valid intent with only required fields."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            original_query="Show me my spending summary"
        )

        assert intent.intent == QueryIntent.SPENDING_SUMMARY
        assert intent.original_query == "Show me my spending summary"
        assert intent.start_date is None
        assert intent.end_date is None
        assert intent.days_back is None
        assert intent.categories is None
        assert intent.merchant_names is None
        assert intent.min_amount is None
        assert intent.max_amount is None
        assert intent.search_term is None
        assert intent.aggregation == AggregationType.SUM  # Default value
        assert intent.group_by is None
        assert intent.sort_by == "date"  # Default value
        assert intent.sort_order == SortOrder.DESC  # Default value
        assert intent.limit is None
        assert intent.account_id is None
        assert intent.confidence is None

    def test_intent_with_date_range(self):
        """Test intent with start and end dates."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_DATE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            original_query="Show transactions in January"
        )

        assert intent.start_date == date(2024, 1, 1)
        assert intent.end_date == date(2024, 1, 31)
        assert intent.days_back is None

    def test_intent_with_days_back(self):
        """Test intent with days_back instead of date range."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            days_back=30,
            original_query="Show spending for last 30 days"
        )

        assert intent.days_back == 30
        assert intent.start_date is None
        assert intent.end_date is None

    def test_intent_with_category_filter(self):
        """Test intent with category filtering."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            categories=["Food & Dining", "Transportation"],
            original_query="How much did I spend on food and transportation?"
        )

        assert intent.categories == ["Food & Dining", "Transportation"]
        assert len(intent.categories) == 2

    def test_intent_with_merchant_filter(self):
        """Test intent with merchant name filtering."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_MERCHANT,
            merchant_names=["Starbucks", "Amazon"],
            original_query="Find transactions from Starbucks or Amazon"
        )

        assert intent.merchant_names == ["Starbucks", "Amazon"]

    def test_intent_with_amount_range(self):
        """Test intent with min and max amount filters."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_AMOUNT,
            min_amount=50.0,
            max_amount=200.0,
            original_query="Show transactions between $50 and $200"
        )

        assert intent.min_amount == 50.0
        assert intent.max_amount == 200.0

    def test_intent_with_aggregation_and_grouping(self):
        """Test intent with aggregation type and grouping."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            aggregation=AggregationType.AVERAGE,
            group_by="category",
            original_query="What's my average spending per category?"
        )

        assert intent.aggregation == AggregationType.AVERAGE
        assert intent.group_by == "category"

    def test_intent_with_sorting_and_limit(self):
        """Test intent with custom sorting and result limit."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_AMOUNT,
            sort_by="amount",
            sort_order=SortOrder.ASC,
            limit=10,
            original_query="Show me 10 smallest transactions"
        )

        assert intent.sort_by == "amount"
        assert intent.sort_order == SortOrder.ASC
        assert intent.limit == 10

    def test_intent_with_confidence_score(self):
        """Test intent with LLM confidence score."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_MERCHANT,
            confidence=0.85,
            original_query="How much at Starbucks?"
        )

        assert intent.confidence == 0.85

    def test_intent_confidence_validation(self):
        """Test that confidence score must be between 0 and 1."""
        # Valid confidence
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_SUMMARY,
            confidence=0.5,
            original_query="Test"
        )
        assert intent.confidence == 0.5

        # Invalid confidence > 1
        with pytest.raises(ValidationError):
            TransactionQueryIntent(
                intent=QueryIntent.SPENDING_SUMMARY,
                confidence=1.5,
                original_query="Test"
            )

        # Invalid confidence < 0
        with pytest.raises(ValidationError):
            TransactionQueryIntent(
                intent=QueryIntent.SPENDING_SUMMARY,
                confidence=-0.5,
                original_query="Test"
            )

    def test_intent_with_search_term(self):
        """Test intent with free-text search term."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SEARCH_BY_DESCRIPTION,
            search_term="coffee",
            original_query="Find all coffee purchases"
        )

        assert intent.search_term == "coffee"

    def test_intent_with_account_filter(self):
        """Test intent with specific account filter."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.TRANSACTIONS_BY_DATE,
            account_id="acc_12345",
            original_query="Show transactions from my checking account"
        )

        assert intent.account_id == "acc_12345"

    def test_complex_intent_with_multiple_filters(self):
        """Test intent with multiple filters combined."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            categories=["Food & Dining"],
            min_amount=10.0,
            max_amount=100.0,
            account_id="acc_checking",
            sort_by="amount",
            sort_order=SortOrder.DESC,
            limit=20,
            confidence=0.92,
            original_query="Show top 20 dining expenses between $10-$100 in January from checking"
        )

        assert intent.intent == QueryIntent.SPENDING_BY_CATEGORY
        assert intent.start_date == date(2024, 1, 1)
        assert intent.end_date == date(2024, 1, 31)
        assert intent.categories == ["Food & Dining"]
        assert intent.min_amount == 10.0
        assert intent.max_amount == 100.0
        assert intent.account_id == "acc_checking"
        assert intent.sort_by == "amount"
        assert intent.sort_order == SortOrder.DESC
        assert intent.limit == 20
        assert intent.confidence == 0.92

    def test_unknown_intent(self):
        """Test creating an unknown intent when query can't be parsed."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.UNKNOWN,
            original_query="This is a completely unrecognizable query",
            confidence=0.1
        )

        assert intent.intent == QueryIntent.UNKNOWN
        assert intent.confidence == 0.1

    def test_missing_required_fields(self):
        """Test that required fields are validated."""
        # Missing intent
        with pytest.raises(ValidationError):
            TransactionQueryIntent(original_query="Test")

        # Missing original_query
        with pytest.raises(ValidationError):
            TransactionQueryIntent(intent=QueryIntent.SPENDING_SUMMARY)


class TestQueryResult:
    """Test QueryResult model for query execution results."""

    def test_successful_query_result(self):
        """Test creating a successful query result."""
        result = QueryResult(
            success=True,
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            data=[
                {"category": "Food & Dining", "amount": 250.50},
                {"category": "Transportation", "amount": 180.00}
            ],
            total_count=2,
            execution_time_ms=15.5
        )

        assert result.success is True
        assert result.intent == QueryIntent.SPENDING_BY_CATEGORY
        assert len(result.data) == 2
        assert result.total_count == 2
        assert result.execution_time_ms == 15.5
        assert result.message is None

    def test_failed_query_result(self):
        """Test creating a failed query result with error message."""
        result = QueryResult(
            success=False,
            intent=QueryIntent.UNKNOWN,
            message="Unable to parse query intent",
            execution_time_ms=5.0
        )

        assert result.success is False
        assert result.intent == QueryIntent.UNKNOWN
        assert result.data == []
        assert result.total_count == 0
        assert result.message == "Unable to parse query intent"
        assert result.execution_time_ms == 5.0

    def test_empty_query_result(self):
        """Test query result with no data found."""
        result = QueryResult(
            success=True,
            intent=QueryIntent.TRANSACTIONS_BY_DATE,
            data=[],
            total_count=0,
            message="No transactions found in specified date range"
        )

        assert result.success is True
        assert result.data == []
        assert result.total_count == 0
        assert result.message is not None

    def test_query_result_defaults(self):
        """Test that QueryResult has proper defaults."""
        result = QueryResult(
            success=True,
            intent=QueryIntent.SPENDING_SUMMARY
        )

        assert result.data == []
        assert result.total_count == 0
        assert result.message is None
        assert result.execution_time_ms is None


class TestModelSerialization:
    """Test JSON serialization and deserialization of models."""

    def test_transaction_query_intent_serialization(self):
        """Test serializing TransactionQueryIntent to JSON."""
        intent = TransactionQueryIntent(
            intent=QueryIntent.SPENDING_BY_CATEGORY,
            categories=["Food & Dining"],
            days_back=30,
            original_query="Food spending last month",
            confidence=0.9
        )

        json_data = intent.model_dump_json()
        assert "spending_by_category" in json_data
        assert "Food & Dining" in json_data
        assert "0.9" in json_data

    def test_transaction_query_intent_deserialization(self):
        """Test deserializing JSON to TransactionQueryIntent."""
        json_str = '''
        {
            "intent": "spending_by_merchant",
            "merchant_names": ["Starbucks"],
            "days_back": 7,
            "original_query": "Starbucks spending this week",
            "confidence": 0.85
        }
        '''

        intent = TransactionQueryIntent.model_validate_json(json_str)
        assert intent.intent == QueryIntent.SPENDING_BY_MERCHANT
        assert intent.merchant_names == ["Starbucks"]
        assert intent.days_back == 7
        assert intent.confidence == 0.85

    def test_query_result_serialization(self):
        """Test serializing QueryResult to JSON."""
        result = QueryResult(
            success=True,
            intent=QueryIntent.SPENDING_SUMMARY,
            data=[{"total": 1500.00}],
            total_count=1
        )

        json_data = result.model_dump_json()
        assert "true" in json_data.lower()
        assert "spending_summary" in json_data
        assert "1500" in json_data