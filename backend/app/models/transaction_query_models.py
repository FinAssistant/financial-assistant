"""
Transaction query intent models for LLM-driven query system.

This module defines Pydantic models for structured transaction queries,
allowing LLMs to extract user intent and convert to safe, parameterized SQL.
"""

from typing import Optional, List, Literal
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum


class QueryIntent(str, Enum):
    """Supported transaction query intents."""
    SPENDING_BY_CATEGORY = "spending_by_category"
    SPENDING_BY_MERCHANT = "spending_by_merchant"
    SPENDING_OVER_TIME = "spending_over_time"
    TRANSACTIONS_BY_AMOUNT = "transactions_by_amount"
    TRANSACTIONS_BY_DATE = "transactions_by_date"
    SEARCH_BY_MERCHANT = "search_by_merchant"
    SEARCH_BY_DESCRIPTION = "search_by_description"
    RECURRING_TRANSACTIONS = "recurring_transactions"
    SPENDING_SUMMARY = "spending_summary"
    UNKNOWN = "unknown"


class SortOrder(str, Enum):
    """Sort order for results."""
    ASC = "asc"
    DESC = "desc"


class AggregationType(str, Enum):
    """Types of aggregation for spending queries."""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"


class TransactionQueryIntent(BaseModel):
    """
    Structured representation of a transaction query intent.

    LLMs parse natural language queries and fill this model,
    which is then safely converted to parameterized SQL.
    """

    intent: QueryIntent = Field(
        description="The type of query the user wants to perform"
    )

    # Time filters
    start_date: Optional[date] = Field(
        None,
        description="Start date for filtering transactions (inclusive)"
    )
    end_date: Optional[date] = Field(
        None,
        description="End date for filtering transactions (inclusive)"
    )
    days_back: Optional[int] = Field(
        None,
        description="Number of days to look back from today (alternative to date range)"
    )

    # Category filters
    categories: Optional[List[str]] = Field(
        None,
        description="List of spending categories to filter by"
    )

    # Merchant filters
    merchant_names: Optional[List[str]] = Field(
        None,
        description="List of merchant names to filter by (exact or partial match)"
    )

    # Amount filters
    min_amount: Optional[float] = Field(
        None,
        description="Minimum transaction amount (inclusive)"
    )
    max_amount: Optional[float] = Field(
        None,
        description="Maximum transaction amount (inclusive)"
    )

    # Search terms
    search_term: Optional[str] = Field(
        None,
        description="Free text search term for merchant or description"
    )

    # Aggregation and grouping
    aggregation: Optional[AggregationType] = Field(
        AggregationType.SUM,
        description="Type of aggregation to perform on amounts"
    )
    group_by: Optional[Literal["category", "merchant", "day", "week", "month"]] = Field(
        None,
        description="Field to group results by"
    )

    # Sorting and pagination
    sort_by: Optional[Literal["date", "amount", "merchant", "category"]] = Field(
        "date",
        description="Field to sort results by. IMPORTANT: Use 'date' (not 'start_date'), 'amount', 'merchant', or 'category'"
    )
    sort_order: SortOrder = Field(
        SortOrder.DESC,
        description="Sort order (ascending or descending)"
    )
    limit: Optional[int] = Field(
        None,
        description="Maximum number of results to return"
    )

    # Account filter
    account_id: Optional[str] = Field(
        None,
        description="Specific account ID to filter transactions"
    )

    # Original query for logging
    original_query: str = Field(
        description="The original natural language query from the user"
    )

    # Confidence score
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="LLM confidence in the intent extraction (0.0 to 1.0)"
    )


class QueryResult(BaseModel):
    """Result of a transaction query execution."""

    success: bool = Field(description="Whether the query executed successfully")
    intent: QueryIntent = Field(description="The executed query intent")
    data: List[dict] = Field(default_factory=list, description="Query result data")
    total_count: int = Field(default=0, description="Total number of results")
    message: Optional[str] = Field(None, description="Success or error message")

    # Metadata
    execution_time_ms: Optional[float] = Field(
        None,
        description="Query execution time in milliseconds"
    )


class UnknownQueryLog(BaseModel):
    """Log entry for queries that couldn't be mapped to known intents."""

    original_query: str = Field(description="The user's original query")
    attempted_intent: Optional[QueryIntent] = Field(
        None,
        description="Intent the LLM attempted to extract"
    )
    confidence: Optional[float] = Field(
        None,
        description="Confidence score if available"
    )
    user_id: str = Field(description="User who made the query")
    timestamp: str = Field(description="ISO timestamp of the query")
    error_reason: Optional[str] = Field(
        None,
        description="Reason for failure to map intent"
    )