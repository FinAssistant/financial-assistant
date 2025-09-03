"""
Services module for core business logic.
Story 2.3: Spending Agent - Transaction Analysis and Insights

Contains service layer implementations for:
- Spending analysis and categorization
- Budget management and tracking  
- Optimization recommendations
- Pattern detection and insights
"""

from .spending_service import SpendingService, get_spending_service

__all__ = [
    "SpendingService",
    "get_spending_service",
]