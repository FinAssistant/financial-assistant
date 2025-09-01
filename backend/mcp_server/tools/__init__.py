"""
MCP Tools module for financial assistant.

All tools are now implemented using FastMCP decorators.
"""

from .plaid_tools import register_plaid_tools

__all__ = ["register_plaid_tools"]