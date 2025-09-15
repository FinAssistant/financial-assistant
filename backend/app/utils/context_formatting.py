"""
Shared utilities for formatting user context across different components.
"""

from typing import Dict, Any


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