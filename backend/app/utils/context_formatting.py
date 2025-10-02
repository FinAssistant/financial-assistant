"""
Shared utilities for formatting user context and managing LLM context limits across different components.
"""

from datetime import datetime
from typing import Dict, Any, List, Union, Optional, Literal
import logging
from unicodedata import category

logger = logging.getLogger(__name__)

# Data structure types we can identify
DataStructureType = Literal["spending_summary", "category_breakdown", "individual_transaction", "generic"]


def build_user_context_string(user_context: Dict[str, Any]) -> str:
    """
    Build a formatted user context string for LLM prompts.
    Reusable across all components that need to format user context.
    
    Args:
        user_context: Dictionary containing user demographics and financial context
            Expected structure: {
                "demographics": {"age_range": "26_35", "occupation": "engineer", ...},
                "financial_context": {"has_dependents": False, ...}
            }
            
    Returns:
        Formatted string ready for inclusion in LLM prompts
    """
    if not user_context:
        return "No user context available"
    
    context_parts = []
    
    # Extract demographics
    demographics = user_context.get("demographics", {})
    if demographics:
        context_parts.append("DEMOGRAPHICS:")
        
        if "age_range" in demographics:
            context_parts.append(f"- Age range: {demographics['age_range']}")
        
        if "occupation" in demographics:
            context_parts.append(f"- Occupation: {demographics['occupation']}")
        
        if "location" in demographics:
            context_parts.append(f"- Location: {demographics['location']}")
        
        if "income_level" in demographics:
            context_parts.append(f"- Income Level: {demographics['income_level']}")
    
    # Extract financial context
    financial_context = user_context.get("financial_context", {})
    if financial_context:
        context_parts.append("\nFINANCIAL PROFILE:")
        
        if "has_dependents" in financial_context:
            dependents = "Yes" if financial_context["has_dependents"] else "No"
            context_parts.append(f"- Has dependents: {dependents}")
        
        if "homeowner" in financial_context:
            homeowner = "Yes" if financial_context["homeowner"] else "No"
            context_parts.append(f"- Homeowner: {homeowner}")
        
        if "investment_experience" in financial_context:
            context_parts.append(f"- Investment Experience: {financial_context['investment_experience']}")
        
        if "risk_tolerance" in financial_context:
            context_parts.append(f"- Risk Tolerance: {financial_context['risk_tolerance']}")
    
    # Handle flat structure (for backward compatibility)
    if not demographics and not financial_context:
        if "name" in user_context:
            context_parts.append(f"User: {user_context['name']}")
        
        if "location" in user_context:
            context_parts.append(f"Location: {user_context['location']}")
        
        if "income_level" in user_context:
            context_parts.append(f"Income Level: {user_context['income_level']}")
        
        if "spending_personality" in user_context:
            context_parts.append(f"Spending Style: {user_context['spending_personality']}")
    
    return "\n".join(context_parts) if context_parts else "Limited user context available"


# LLM Context Management Helpers (extracted from transaction_categorization.py)

# Context window limits for different LLM providers
LLM_CONTEXT_LIMITS = {
    "openai": 128000,     # GPT-4o
    "anthropic": 200000,  # Claude Sonnet
    "google": 1048576     # Gemini Flash
}


def get_llm_context_limit(llm) -> int:
    """
    Get context limit for current LLM provider.

    Args:
        llm: LLM instance with model_name attribute

    Returns:
        Context limit in tokens
    """
    if hasattr(llm, 'model_name') and llm.model_name:
        model = str(llm.model_name).lower()
        if 'gpt' in model or 'openai' in model:
            return LLM_CONTEXT_LIMITS["openai"]
        elif 'claude' in model or 'anthropic' in model:
            return LLM_CONTEXT_LIMITS["anthropic"]
        elif 'gemini' in model or 'google' in model:
            return LLM_CONTEXT_LIMITS["google"]

    # Conservative default for tests and unknown models
    return LLM_CONTEXT_LIMITS["openai"]


def _identify_data_structure(item: Dict[str, Any]) -> DataStructureType:
    """
    Identify the data structure type of a query result item.

    Args:
        item: Dictionary data item from query results

    Returns:
        DataStructureType indicating the identified structure
    """
    if not isinstance(item, dict):
        return "generic"

    # Type 1: Spending Summary (aggregate data)
    if 'transaction_count' in item or 'total_amount' in item:
        return "spending_summary"

    # Type 2: Category Breakdown
    elif 'category' in item and ('total' in item or 'count' in item):
        return "category_breakdown"

    # Type 3: Individual Transaction
    elif 'amount' in item or 'date' in item:
        return "individual_transaction"

    # Type 4: Generic/Unknown
    return "generic"


def _format_item_by_type(item: Dict[str, Any], data_type: DataStructureType) -> str:
    """
    Format a data item based on its identified structure type.

    Args:
        item: Dictionary data item from query results
        data_type: Identified data structure type

    Returns:
        Formatted string representation
    """
    if data_type == "spending_summary":
        count = item.get('transaction_count', 0)
        total = item.get('total_amount', 0)
        avg = item.get('average_amount', 0)
        min_amt = item.get('min_amount')
        max_amt = item.get('max_amount')

        category = item.get('category')

        merchant = item.get('merchant_name')

        text = f"📊 Spending Summary:\n"
        text += f"  • Total Transactions: {count}\n"
        text += f"  • Total Amount: ${total:.2f}\n"
        text += f"  • Average per Transaction: ${avg:.2f}"

        if category:
            text += f"  • Category: {category}"

        if merchant:
            text += f"  • Merchant: {merchant}"

        if min_amt is not None and max_amt is not None:
            text += f"\n  • Range: ${min_amt:.2f} - ${max_amt:.2f}"

        return text

    elif data_type == "category_breakdown":
        category = item.get('category', 'Unknown Category')
        total = item.get('total', 0)
        count = item.get('count') or item.get('transaction_count', 0)
        percentage = item.get('percentage')

        text = f"• {category}: ${total:.2f}"
        if count:
            text += f" ({count} transactions"
            if percentage:
                text += f", {percentage:.1f}%"
            text += ")"
        return text

    elif data_type == "individual_transaction":
        merchant = item.get('merchant_name') or item.get('name', 'Unknown Merchant')
        amount = item.get('amount', 0)
        date = item.get('date', 'Unknown date')

        category = item.get('ai_category')
        subcategory = item.get('ai_subcategory')

        if category and subcategory:
            category_str = f"{category} > {subcategory}"
        elif category:
            category_str = category
        else:
            category_str = 'Uncategorized'

        amount_str = f"${abs(amount):.2f}"
        return f"• {merchant}: {amount_str} on {date} [{category_str}]"

    else:  # generic
        return f"• {item.get('name', 'Unknown')}: {item.get('summary', 'No summary')}"


def format_transaction_insights_for_llm_context(
    data_items: List[Dict[str, Any]],
    llm,
    reserved_tokens: int = 1500,
    chars_per_token: int = 4,
    query_intent: Optional[str] = None
) -> str:
    """
    Format data items for LLM with dynamic truncation based on context limits.

    Handles three types of query results:
    1. Spending summaries (aggregate data with transaction_count, total_amount)
    2. Category breakdowns (category with total/count)
    3. Individual transactions (merchant_name, amount, date, category)

    Args:
        data_items: List of data items to format
        llm: LLM instance to determine context limits
        reserved_tokens: Tokens to reserve for system prompt and response
        chars_per_token: Estimated characters per token
        query_intent: Optional query intent type (e.g., "spending_summary", "spending_by_category")

    Returns:
        Formatted string that fits within context limits
    """
    if not data_items:
        logger.warning("Empty data_items provided to formatter")
        return "No data available"

    # Validate input types
    if not isinstance(data_items, list):
        logger.error(f"data_items must be a list, got {type(data_items)}")
        return "Invalid data format"

    context_limit = get_llm_context_limit(llm)
    available_tokens = context_limit - reserved_tokens
    max_chars = available_tokens * chars_per_token

    formatted_data = []

    # Add query intent header if provided
    if query_intent:
        intent_label = query_intent.replace('_', ' ').title()
        formatted_data.append(f"Query Type: {intent_label}\n")

    today_date = datetime.now().date()
    formatted_data.append(f"Today Date: {today_date.isoformat()}\n")

    char_count = sum(len(line) for line in formatted_data)

    for item in data_items:
        # Identify data structure and format accordingly
        if isinstance(item, dict):
            data_type = _identify_data_structure(item)
            item_text = _format_item_by_type(item, data_type)
        else:
            item_text = f"• {str(item)}"

        # Check if adding this item would exceed context limit
        if char_count + len(item_text) > max_chars:
            remaining_count = len(data_items) - len(formatted_data)
            if remaining_count > 0:
                formatted_data.append(f"... and {remaining_count} more items (truncated for context limit)")
            break

        formatted_data.append(item_text)
        char_count += len(item_text)

    return "\n".join(formatted_data)