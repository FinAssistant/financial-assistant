"""
Hybrid date parsing utilities (rule-based + LLM fallback).

Strategy:
1. Try fast rule-based parsing for common patterns
2. Fallback to LLM for complex/ambiguous expressions
3. Provide reusable date calculation helpers

Shared across:
- insights_generator (spending insights date ranges)
- transaction_query_parser (transaction query dates)
- spending_agent (any date-based analysis)
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


# ============================================================================
# Reusable Date Calculation Helpers
# ============================================================================

def get_month_range(month_date: datetime) -> Tuple[str, str]:
    """
    Get start and end dates for a given month.

    Args:
        month_date: Any date within the target month

    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)

    Examples:
        >>> get_month_range(datetime(2025, 9, 15))
        ('2025-09-01', '2025-09-30')
    """
    start_date = month_date.replace(day=1)
    # Get last day of month
    next_month = start_date.replace(day=28) + timedelta(days=4)
    end_date = next_month - timedelta(days=next_month.day)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def get_quarter_range(year: int, quarter: int) -> Tuple[str, str]:
    """
    Get start and end dates for a given quarter.

    Args:
        year: Year (e.g., 2025)
        quarter: Quarter number (1-4)

    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)

    Examples:
        >>> get_quarter_range(2025, 3)
        ('2025-07-01', '2025-09-30')
    """
    if not 1 <= quarter <= 4:
        raise ValueError(f"Quarter must be 1-4, got: {quarter}")

    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2

    start_date = datetime(year, start_month, 1)
    # Get last day of end month
    if end_month == 12:
        end_date = datetime(year, 12, 31)
    else:
        next_month = datetime(year, end_month + 1, 1)
        end_date = next_month - timedelta(days=1)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def get_year_range(year: int) -> Tuple[str, str]:
    """
    Get start and end dates for a given year.

    Args:
        year: Year (e.g., 2025)

    Returns:
        Tuple of (start_date, end_date) in ISO format (YYYY-MM-DD)

    Examples:
        >>> get_year_range(2025)
        ('2025-01-01', '2025-12-31')
    """
    return f"{year}-01-01", f"{year}-12-31"


# ============================================================================
# Hybrid Date Range Parser (Rule-based + LLM Fallback)
# ============================================================================

def parse_date_range(
    text: str,
    llm = None,
    reference_date: Optional[datetime] = None
) -> Dict[str, Optional[str]]:
    """
    Parse natural language date expressions using hybrid strategy.

    Strategy:
    1. Try fast rule-based parsing (covers ~80% of cases, no API cost)
    2. Fallback to LLM for complex/ambiguous expressions
    3. Default to current month if all parsing fails

    Args:
        text: Natural language date expression
        llm: Optional LangChain LLM instance for complex parsing
        reference_date: Reference date for relative expressions (defaults to now)

    Returns:
        Dictionary with 'start_date', 'end_date', 'month' keys (ISO format)
        Example: {"start_date": "2025-09-01", "end_date": "2025-09-30", "month": "2025-09"}

    Examples:
        >>> parse_date_range("last month")
        {"start_date": "2025-09-01", "end_date": "2025-09-30", "month": "2025-09"}

        >>> parse_date_range("Q3 2025")
        {"start_date": "2025-07-01", "end_date": "2025-09-30", "month": None}

        >>> parse_date_range("from January to March 2025")  # Complex -> LLM
        {"start_date": "2025-01-01", "end_date": "2025-03-31", "month": None}
    """
    ref_date = reference_date or datetime.now()
    text_lower = text.lower().strip()

    # Step 1: Try rule-based parsing (fast, no API cost)
    result = _try_rule_based_parsing(text_lower, ref_date)

    if result:
        logger.info(f"✅ Rule-based parsing: '{text}' -> {result}")
        return result

    # Step 2: Fallback to LLM for complex expressions
    if llm:
        logger.info(f"🤖 Using LLM for complex date parsing: '{text}'")
        result = _parse_with_llm(text, llm, ref_date)
        if result:
            return result

    # Step 3: Default to current month
    logger.warning(f"⚠️  Could not parse '{text}', defaulting to current month")
    start, end = get_month_range(ref_date)
    return {
        "start_date": start,
        "end_date": end,
        "month": ref_date.strftime("%Y-%m")
    }


def _try_rule_based_parsing(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """
    Try all rule-based parsing strategies in order of specificity.

    Returns parsed result or None if no pattern matches.
    """
    # Try patterns in order of specificity
    parsers = [
        _parse_last_n_days,
        _parse_relative_month,
        _parse_relative_quarter,
        _parse_relative_year,
        _parse_specific_month,
        _parse_specific_quarter,
        _parse_specific_year,
    ]

    for parser in parsers:
        result = parser(text, ref_date)
        if result:
            return result

    return None


# ============================================================================
# Rule-based Parsing Functions
# ============================================================================

def _parse_last_n_days(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse 'last N days' patterns."""
    patterns = [
        r"last (\d+) days?",
        r"past (\d+) days?",
        r"previous (\d+) days?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            days = int(match.group(1))
            end_date = ref_date
            start_date = end_date - timedelta(days=days - 1)  # Inclusive

            return {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "month": None,
            }

    return None


def _parse_relative_month(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse relative month expressions (this month, last month, etc.)."""
    if "this month" in text or "current month" in text:
        start, end = get_month_range(ref_date)
        return {
            "start_date": start,
            "end_date": end,
            "month": ref_date.strftime("%Y-%m")
        }

    if "last month" in text or "previous month" in text:
        last_month = ref_date.replace(day=1) - timedelta(days=1)
        start, end = get_month_range(last_month)
        return {
            "start_date": start,
            "end_date": end,
            "month": last_month.strftime("%Y-%m")
        }

    if "next month" in text:
        # Get first day of next month
        if ref_date.month == 12:
            next_month = ref_date.replace(year=ref_date.year + 1, month=1, day=1)
        else:
            next_month = ref_date.replace(month=ref_date.month + 1, day=1)
        start, end = get_month_range(next_month)
        return {
            "start_date": start,
            "end_date": end,
            "month": next_month.strftime("%Y-%m")
        }

    # Pattern: "N months ago"
    match = re.search(r"(\d+) months? ago", text)
    if match:
        months_ago = int(match.group(1))
        target_date = ref_date
        for _ in range(months_ago):
            target_date = target_date.replace(day=1) - timedelta(days=1)
        start, end = get_month_range(target_date)
        return {
            "start_date": start,
            "end_date": end,
            "month": target_date.strftime("%Y-%m")
        }

    return None


def _parse_relative_quarter(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse relative quarter expressions (this quarter, last quarter, etc.)."""
    current_quarter = (ref_date.month - 1) // 3 + 1

    if "this quarter" in text or "current quarter" in text:
        start, end = get_quarter_range(ref_date.year, current_quarter)
        return {"start_date": start, "end_date": end, "month": None}

    if "last quarter" in text or "previous quarter" in text:
        if current_quarter == 1:
            start, end = get_quarter_range(ref_date.year - 1, 4)
        else:
            start, end = get_quarter_range(ref_date.year, current_quarter - 1)
        return {"start_date": start, "end_date": end, "month": None}

    return None


def _parse_relative_year(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse relative year expressions (this year, last year, etc.)."""
    if "this year" in text or "current year" in text:
        start, end = get_year_range(ref_date.year)
        return {"start_date": start, "end_date": end, "month": None}

    if "last year" in text or "previous year" in text:
        start, end = get_year_range(ref_date.year - 1)
        return {"start_date": start, "end_date": end, "month": None}

    return None


def _parse_specific_month(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse specific month references (September 2025, Sep 2025, 2025-09, etc.)."""
    # Month names mapping
    month_names = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    # Pattern: "Month YYYY" or "Month, YYYY"
    for month_name, month_num in month_names.items():
        pattern = rf"\b{month_name}\s*,?\s*(\d{{4}})\b"
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            target_date = datetime(year, month_num, 1)
            start, end = get_month_range(target_date)
            return {
                "start_date": start,
                "end_date": end,
                "month": target_date.strftime("%Y-%m")
            }

    # Pattern: "YYYY-MM" (ISO format)
    match = re.search(r"\b(\d{4})-(\d{2})\b", text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        if 1 <= month <= 12:
            target_date = datetime(year, month, 1)
            start, end = get_month_range(target_date)
            return {
                "start_date": start,
                "end_date": end,
                "month": target_date.strftime("%Y-%m")
            }

    return None


def _parse_specific_quarter(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse specific quarter references (Q3 2025, Q1, etc.)."""
    # Pattern: "Q1 2025" or "Q1"
    match = re.search(r"\bq([1-4])\s*(?:(\d{4}))?\b", text)
    if match:
        quarter = int(match.group(1))
        year_str = match.group(2)

        year = int(year_str) if year_str else ref_date.year

        start, end = get_quarter_range(year, quarter)
        return {"start_date": start, "end_date": end, "month": None}

    return None


def _parse_specific_year(text: str, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """Parse specific year references (2025, etc.)."""
    # Pattern: standalone 4-digit year
    match = re.search(r"\b(20\d{2})\b", text)
    if match:
        year = int(match.group(1))
        start, end = get_year_range(year)
        return {"start_date": start, "end_date": end, "month": None}

    return None


# ============================================================================
# LLM Fallback Parsing
# ============================================================================

def _parse_with_llm(text: str, llm, ref_date: datetime) -> Optional[Dict[str, Optional[str]]]:
    """
    Use LLM to parse complex date expressions.

    Handles cases like:
    - "from January to March 2025"
    - "the first half of 2024"
    - "between Christmas and New Year"
    """
    try:
        system_prompt = f"""You are a date range parser. Today is {ref_date.strftime('%Y-%m-%d')}.

Convert the user's date expression into a JSON object with:
- "start_date": ISO format (YYYY-MM-DD)
- "end_date": ISO format (YYYY-MM-DD)
- "month": ISO month (YYYY-MM) if single month, null otherwise

Examples:
- "from January to March 2025" → {{"start_date": "2025-01-01", "end_date": "2025-03-31", "month": null}}
- "first half of 2024" → {{"start_date": "2024-01-01", "end_date": "2024-06-30", "month": null}}

Respond ONLY with valid JSON, no other text."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=text)
        ]

        response = llm.invoke(messages)

        # Extract JSON from response
        import json
        result = json.loads(response.content)

        logger.info(f"LLM parsed '{text}' -> {result}")
        return result

    except Exception as e:
        logger.error(f"LLM date parsing failed for '{text}': {e}")
        return None
