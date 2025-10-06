"""
Transaction query executor that maps intents to safe, parameterized SQL queries.

Strategy:
- Convert TransactionQueryIntent to parameterized SQL templates
- Use bound parameters to prevent SQL injection
- Execute via SQLAlchemy with proper escaping
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import text

from app.models.transaction_query_models import (
    TransactionQueryIntent,
    QueryIntent,
    QueryResult,
)
from app.core.database import SQLiteUserStorage

logger = logging.getLogger(__name__)


def intent_to_sql(
    intent: TransactionQueryIntent,
    user_id: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Convert TransactionQueryIntent to parameterized SQL query.

    Args:
        intent: Parsed query intent
        user_id: User ID for filtering

    Returns:
        Tuple of (SQL query string, parameters dict)

    Example:
        sql, params = intent_to_sql(intent, "user_123")
        # sql = "SELECT * FROM transactions WHERE user_id = :uid AND merchant LIKE :merchant"
        # params = {"uid": "user_123", "merchant": "%Uber%"}
    """
    # Resolve date range
    start_date, end_date = resolve_date_range(intent)

    # Base parameters
    params = {"uid": user_id}

    if intent.intent == QueryIntent.SEARCH_BY_MERCHANT:
        return _sql_search_by_merchant(intent, params, start_date, end_date)

    elif intent.intent == QueryIntent.SPENDING_BY_CATEGORY:
        return _sql_spending_by_category(intent, params, start_date, end_date)

    elif intent.intent == QueryIntent.SPENDING_BY_MERCHANT:
        return _sql_spending_by_merchant(intent, params, start_date, end_date)

    elif intent.intent == QueryIntent.TRANSACTIONS_BY_DATE:
        return _sql_transactions_by_date(intent, params, start_date, end_date)

    elif intent.intent == QueryIntent.TRANSACTIONS_BY_AMOUNT:
        return _sql_transactions_by_amount(intent, params, start_date, end_date)

    elif intent.intent == QueryIntent.SPENDING_SUMMARY:
        return _sql_spending_summary(intent, params, start_date, end_date)

    else:
        # Should not reach here if unknown intents are handled properly
        logger.error(f"Unsupported intent in SQL generation: {intent.intent}")
        return ("", {})


def resolve_date_range(intent: TransactionQueryIntent) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve date range from intent parameters.

    Args:
        intent: TransactionQueryIntent with date parameters

    Returns:
        Tuple of (start_date, end_date) as ISO strings or (None, None)
    """
    if intent.start_date and intent.end_date:
        return (intent.start_date.isoformat(), intent.end_date.isoformat())

    if intent.days_back:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=intent.days_back)
        return (start_date.isoformat(), end_date.isoformat())

    return (None, None)


# SQL template builders for each intent type


def _sql_search_by_merchant(
    intent: TransactionQueryIntent,
    params: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """
    Build SQL for search_by_merchant intent.

    Example: "Show my Uber rides last week"
    """
    sql = "SELECT * FROM transactions WHERE user_id = :uid"

    # Add merchant filter
    if intent.merchant_names:
        # For multiple merchants, use OR conditions
        merchant_conditions = []
        for idx, merchant in enumerate(intent.merchant_names):
            param_name = f"merchant_{idx}"
            merchant_conditions.append(f"merchant_name LIKE :{param_name}")
            params[param_name] = f"%{merchant}%"

        sql += f" AND ({' OR '.join(merchant_conditions)})"

    # Add date range
    if start_date and end_date:
        sql += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    # Add account filter
    if intent.account_id:
        sql += " AND account_id = :account_id"
        params["account_id"] = intent.account_id

    # Add sorting
    sort_column = intent.sort_by or "date"
    sort_order = "DESC" if intent.sort_order.value == "desc" else "ASC"
    sql += f" ORDER BY {sort_column} {sort_order}"

    # Add limit
    if intent.limit:
        sql += " LIMIT :limit"
        params["limit"] = intent.limit

    return (sql, params)


def _sql_spending_by_category(
    intent: TransactionQueryIntent,
    params: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """
    Build SQL for spending_by_category intent.

    Example: "How much did I spend on dining last month?"
    """
    sql = """
        SELECT
            ai_category as category,
            SUM(amount) as total_amount,
            COUNT(*) as transaction_count,
            AVG(amount) as average_amount
        FROM transactions
        WHERE user_id = :uid
    """

    # Add category filter
    if intent.categories:
        category_placeholders = []
        for idx, category in enumerate(intent.categories):
            param_name = f"category_{idx}"
            category_placeholders.append(f":{param_name}")
            params[param_name] = category

        sql += f" AND ai_category IN ({','.join(category_placeholders)})"

    # Add date range
    if start_date and end_date:
        sql += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    # Add account filter
    if intent.account_id:
        sql += " AND account_id = :account_id"
        params["account_id"] = intent.account_id

    # Group by category
    sql += " GROUP BY ai_category"

    # Add sorting
    sort_column = "total_amount" if intent.sort_by == "amount" else "ai_category"
    sort_order = "DESC" if intent.sort_order.value == "desc" else "ASC"
    sql += f" ORDER BY {sort_column} {sort_order}"

    # Add limit
    if intent.limit:
        sql += " LIMIT :limit"
        params["limit"] = intent.limit

    return (sql, params)


def _sql_spending_by_merchant(
    intent: TransactionQueryIntent,
    params: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """Build SQL for spending_by_merchant intent."""
    sql = """
        SELECT
            merchant_name as merchant,
            SUM(amount) as total_amount,
            COUNT(*) as transaction_count,
            AVG(amount) as average_amount
        FROM transactions
        WHERE user_id = :uid
    """

    # Add merchant filter
    if intent.merchant_names:
        merchant_conditions = []
        for idx, merchant in enumerate(intent.merchant_names):
            param_name = f"merchant_{idx}"
            merchant_conditions.append(f"merchant_name LIKE :{param_name}")
            params[param_name] = f"%{merchant}%"

        sql += f" AND ({' OR '.join(merchant_conditions)})"

    # Add date range
    if start_date and end_date:
        sql += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    # Add account filter
    if intent.account_id:
        sql += " AND account_id = :account_id"
        params["account_id"] = intent.account_id

    # Group by merchant
    sql += " GROUP BY merchant_name"

    # Add sorting
    sort_order = "DESC" if intent.sort_order.value == "desc" else "ASC"
    sql += f" ORDER BY total_amount {sort_order}"

    # Add limit
    if intent.limit:
        sql += " LIMIT :limit"
        params["limit"] = intent.limit

    return (sql, params)


def _sql_transactions_by_date(
    intent: TransactionQueryIntent,
    params: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """Build SQL for transactions_by_date intent."""
    sql = "SELECT * FROM transactions WHERE user_id = :uid"

    # Add date range
    if start_date and end_date:
        sql += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    # Add account filter
    if intent.account_id:
        sql += " AND account_id = :account_id"
        params["account_id"] = intent.account_id

    # Add sorting
    sort_column = intent.sort_by or "date"
    sort_order = "DESC" if intent.sort_order.value == "desc" else "ASC"
    sql += f" ORDER BY {sort_column} {sort_order}"

    # Add limit
    if intent.limit:
        sql += " LIMIT :limit"
        params["limit"] = intent.limit

    return (sql, params)


def _sql_transactions_by_amount(
    intent: TransactionQueryIntent,
    params: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """
    Build SQL for transactions_by_amount intent.

    Example: "Show me transactions over $100 this week"
    """
    sql = "SELECT * FROM transactions WHERE user_id = :uid"

    # Add amount filters
    if intent.min_amount is not None:
        sql += " AND amount >= :min_amount"
        params["min_amount"] = intent.min_amount

    if intent.max_amount is not None:
        sql += " AND amount <= :max_amount"
        params["max_amount"] = intent.max_amount

    # Add date range
    if start_date and end_date:
        sql += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    # Add account filter
    if intent.account_id:
        sql += " AND account_id = :account_id"
        params["account_id"] = intent.account_id

    # Add sorting
    sort_column = intent.sort_by or "amount"
    sort_order = "DESC" if intent.sort_order.value == "desc" else "ASC"
    sql += f" ORDER BY {sort_column} {sort_order}"

    # Add limit
    if intent.limit:
        sql += " LIMIT :limit"
        params["limit"] = intent.limit

    return (sql, params)


def _sql_spending_summary(
    intent: TransactionQueryIntent,
    params: Dict[str, Any],
    start_date: Optional[str],
    end_date: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """
    Build SQL for spending_summary intent.

    Example: "What's my spending summary?"
    """
    sql = """
        SELECT
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount,
            AVG(amount) as average_amount,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount
        FROM transactions
        WHERE user_id = :uid
    """

    # Add date range
    if start_date and end_date:
        sql += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    # Add account filter
    if intent.account_id:
        sql += " AND account_id = :account_id"
        params["account_id"] = intent.account_id

    return (sql, params)


async def execute_transaction_query(
    intent: TransactionQueryIntent,
    user_id: str,
    storage: SQLiteUserStorage
) -> QueryResult:
    """
    Execute transaction query using parameterized SQL.

    Args:
        intent: Parsed query intent
        user_id: User ID for filtering
        storage: SQLite storage instance

    Returns:
        QueryResult with query data
    """
    start_time = datetime.now()

    # Handle unknown queries (LLM couldn't map to a supported intent)
    if intent.intent == QueryIntent.UNKNOWN:
        logger.warning(
            f"Unknown query intent (user: {user_id}): "
            f"query='{intent.original_query}', confidence={intent.confidence}"
        )
        return QueryResult(
            success=False,
            intent=QueryIntent.UNKNOWN,
            message=(
                f"I couldn't understand your query: '{intent.original_query}'. "
                "Could you rephrase it? For example, try 'Show my Uber rides last week' "
                "or 'How much did I spend on dining?'"
            )
        )

    try:
        # Convert intent to SQL
        sql, params = intent_to_sql(intent, user_id)

        logger.debug(f"Generated SQL (user: {user_id}): {sql}")
        logger.debug(f"Parameters: {params}")

        # Execute query with bound parameters
        await storage._ensure_initialized()
        async with storage.session_factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()

            # Convert rows to dictionaries
            data = [dict(row._mapping) for row in rows]

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"Query executed successfully (user: {user_id}): "
            f"intent={intent.intent}, results={len(data)}, time={execution_time:.2f}ms"
        )

        return QueryResult(
            success=True,
            intent=intent.intent,
            data=data,
            total_count=len(data),
            execution_time_ms=execution_time
        )

    except Exception as e:
        # Other execution errors
        logger.error(f"Query execution failed (user: {user_id}): {e}", exc_info=True)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return QueryResult(
            success=False,
            intent=intent.intent,
            message=f"Query execution failed: {str(e)}",
            execution_time_ms=execution_time
        )