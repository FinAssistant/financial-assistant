"""
Transaction query parser using LLM to convert natural language to structured queries.

Strategy:
1. Prompt LLM to fill TransactionQueryIntent model using structured output
2. Map intent to parameterized SQL queries (no SQL injection risk)
3. Log unknown queries for analysis
"""

import logging
from datetime import timedelta, date
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.transaction_query_models import TransactionQueryIntent, QueryIntent

logger = logging.getLogger(__name__)


def build_intent_extraction_prompt() -> str:
    """
    Build the system prompt for LLM intent extraction.

    Returns instructions with examples for the LLM to follow.
    """
    # Get current date for relative time calculations
    today = date.today()
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_month_end = today.replace(day=1) - timedelta(days=1)

    return f"""You convert user transaction queries into structured intent.

**Intent Types:**
- spending_by_category: Group spending by category
- spending_by_merchant: Group spending by merchant
- transactions_by_date: List transactions in date range
- transactions_by_amount: Filter by amount range
- spending_summary: Overall spending summary
- search_by_merchant: Search by merchant name
- unknown: Can't determine intent

**Time Reference Rules (Today is {today}):**
- "last week": days_back = 7
- "this month": start_date = first day of current month, end_date = today
- "last month": start_date = {last_month_start}, end_date = {last_month_end}
- "last 30 days": days_back = 30

**Examples:**

User: "Show my Uber rides last week"
→ intent: search_by_merchant, merchant_names: ["Uber"], days_back: 7, confidence: 0.95

User: "How much did I spend on dining last month?"
→ intent: spending_by_category, categories: ["Food & Dining"], start_date: {last_month_start}, end_date: {last_month_end}, confidence: 0.9

User: "Show me transactions over $100 this week"
→ intent: transactions_by_amount, min_amount: 100, days_back: 7, confidence: 0.95

User: "What's my spending summary?"
→ intent: spending_summary, days_back: 30, confidence: 0.85

Extract all relevant fields and provide a confidence score (0.0-1.0)."""


def parse_user_query_to_intent(
    user_query: str,
    llm,
    user_id: str
) -> TransactionQueryIntent:
    """
    Parse natural language query into structured TransactionQueryIntent using LLM.

    Uses LLM structured output for reliable extraction.

    Args:
        user_query: User's natural language query
        llm: LangChain LLM instance
        user_id: User ID for logging

    Returns:
        TransactionQueryIntent with extracted parameters
    """
    if llm is None:
        logger.error(f"LLM not available for query parsing (user: {user_id})")
        return TransactionQueryIntent(
            intent=QueryIntent.UNKNOWN,
            original_query=user_query,
            confidence=0.0
        )

    try:
        # Build prompt with instructions and examples
        system_prompt = build_intent_extraction_prompt()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]

        # Use structured output if available (OpenAI, Anthropic support this)
        if hasattr(llm, 'with_structured_output'):
            logger.debug(f"Using structured output for query parsing (user: {user_id})")
            structured_llm = llm.with_structured_output(TransactionQueryIntent)
            intent = structured_llm.invoke(messages)

            # Add original_query since structured output might not include it
            if not intent.original_query:
                intent.original_query = user_query

            logger.info(f"Successfully parsed query via structured output (user: {user_id}): intent={intent.intent}")
        else:
            # Fallback to JSON parsing for LLMs without structured output
            logger.debug(f"Using JSON parsing fallback (user: {user_id})")
            response = llm.invoke(messages)
            intent_json = response.content
            logger.debug(f"LLM response: {intent_json}")

            # Parse into Pydantic model
            intent = TransactionQueryIntent.model_validate_json(intent_json)
            logger.info(f"Successfully parsed query via JSON (user: {user_id}): intent={intent.intent}")

        # Log if confidence is low or intent is unknown
        if intent.intent == QueryIntent.UNKNOWN or (intent.confidence and intent.confidence < 0.7):
            logger.warning(
                f"Low confidence query parsing (user: {user_id}): "
                f"query='{user_query}', intent={intent.intent}, confidence={intent.confidence}"
            )

        return intent

    except Exception as e:
        logger.error(f"Failed to parse query (user: {user_id}): {e}", exc_info=True)
        return TransactionQueryIntent(
            intent=QueryIntent.UNKNOWN,
            original_query=user_query,
            confidence=0.0
        )