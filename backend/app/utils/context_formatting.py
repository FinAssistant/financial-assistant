"""
Shared utilities for formatting user context and managing LLM context limits across different components.
"""

from typing import Dict, Any, List


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
    if hasattr(llm, 'model_name'):
        model = llm.model_name.lower()
        if 'gpt' in model or 'openai' in model:
            return LLM_CONTEXT_LIMITS["openai"]
        elif 'claude' in model or 'anthropic' in model:
            return LLM_CONTEXT_LIMITS["anthropic"]
        elif 'gemini' in model or 'google' in model:
            return LLM_CONTEXT_LIMITS["google"]

    # Conservative default
    return LLM_CONTEXT_LIMITS["openai"]


def format_transaction_insights_for_llm_context(
    data_items: List[Dict[str, Any]],
    llm,
    reserved_tokens: int = 1500,
    chars_per_token: int = 4
) -> str:
    """
    Format data items for LLM with dynamic truncation based on context limits.

    Args:
        data_items: List of data items to format
        llm: LLM instance to determine context limits
        reserved_tokens: Tokens to reserve for system prompt and response
        chars_per_token: Estimated characters per token

    Returns:
        Formatted string that fits within context limits
    """
    context_limit = get_llm_context_limit(llm)
    available_tokens = context_limit - reserved_tokens
    max_chars = available_tokens * chars_per_token

    formatted_data = []
    char_count = 0

    for item in data_items:
        # Format each item (customize this based on data structure)
        if isinstance(item, dict):
            item_text = f"• {item.get('name', 'Unknown')}: {item.get('summary', 'No summary')}"
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