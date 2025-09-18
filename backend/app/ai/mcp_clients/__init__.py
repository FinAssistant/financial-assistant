"""
MCP clients for connecting to external MCP servers.

TODO: Consolidate mcp_clients and mcp_server directories into a single 'mcp' folder
      to better organize MCP-related code (server and clients together).
"""

from .graphiti_client import get_graphiti_client
from .plaid_client import get_plaid_client

__all__ = ['get_graphiti_client', 'get_plaid_client']