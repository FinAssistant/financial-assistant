"""
Shared MCP client for Plaid integration with JWT authentication.

This module provides a reusable client for connecting to the Plaid MCP server
and accessing its tools for account linking and transaction retrieval.
Each user gets their own authenticated client with proper token management.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("langchain-mcp-adapters not available - Plaid MCP tools will be mocked")


class PlaidMCPClient:
    """
    Shared MCP client for Plaid operations with per-user JWT authentication.

    Provides a simple interface for agents to access Plaid tools without needing
    to manage MCP connections and authentication directly.
    """

    def __init__(self, plaid_mcp_url: str = "http://localhost:8000/mcp/"):
        """
        Initialize Plaid MCP client manager.

        Args:
            plaid_mcp_url: URL of the Plaid MCP server endpoint
        """
        self.plaid_mcp_url = plaid_mcp_url
        self._auth_service = AuthService()
        self._user_clients: Dict[str, MultiServerMCPClient] = {}
        self._client_locks: Dict[str, asyncio.Lock] = {}
        self._tools_cache: Dict[str, List[Any]] = {}  # Cache tools per user

    async def get_client(self, user_id: str) -> Optional[MultiServerMCPClient]:
        """
        Get or create authenticated MCP client for the specified user.

        Each user gets their own client with a personalized JWT token for secure
        access to their Plaid data through the MCP server.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Authenticated MCP client or None if unavailable/failed
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP library not available - Plaid operations will be mocked")
            return None

        # Ensure we have a lock for this user
        if user_id not in self._client_locks:
            self._client_locks[user_id] = asyncio.Lock()

        async with self._client_locks[user_id]:
            # Check if we already have a client for this user
            if user_id in self._user_clients:
                logger.debug(f"Returning existing Plaid MCP client for user: {user_id}")
                return self._user_clients[user_id]

            try:
                # Generate JWT token for the specific user
                jwt_token = self._auth_service.generate_access_token(user_id)
                logger.info(f"Generated JWT token for Plaid MCP authentication (user: {user_id})")

                # Create authenticated MCP client
                client = MultiServerMCPClient({
                    "plaid": {
                        "transport": "streamable_http",
                        "url": self.plaid_mcp_url,
                        "headers": {
                            "Authorization": f"Bearer {jwt_token}"
                        }
                    }
                })

                # Cache the client for this user
                self._user_clients[user_id] = client
                logger.info(f"Plaid MCP client initialized with JWT authentication for user: {user_id}")

                # Initialize tools cache for this user
                await self._cache_tools(user_id, client)

                return client

            except Exception as e:
                logger.error(f"Failed to create Plaid MCP client for user {user_id}: {str(e)}")
                return None

    async def _cache_tools(self, user_id: str, client: MultiServerMCPClient) -> None:
        """Cache available tools for the user's client."""
        try:
            tools = await client.get_tools()
            self._tools_cache[user_id] = tools
            tool_names = [getattr(tool, 'name', 'unknown') for tool in tools]
            logger.debug(f"Cached {len(tools)} Plaid MCP tools for user {user_id}: {tool_names}")
        except Exception as e:
            logger.warning(f"Failed to cache tools for user {user_id}: {e}")
            self._tools_cache[user_id] = []

    async def get_tools(self, user_id: str) -> List[Any]:
        """
        Get available Plaid MCP tools for the user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            List of available tools for the user's client
        """
        client = await self.get_client(user_id)
        if not client:
            return []

        # Return cached tools if available
        if user_id in self._tools_cache:
            return self._tools_cache[user_id]

        # Fallback to direct tool retrieval
        try:
            tools = await client.get_tools()
            self._tools_cache[user_id] = tools
            return tools
        except Exception as e:
            logger.error(f"Failed to get tools for user {user_id}: {e}")
            return []

    async def get_tool_by_name(self, user_id: str, tool_name: str) -> Optional[Any]:
        """
        Get a specific Plaid MCP tool by name for the user.

        Args:
            user_id: Unique identifier for the user
            tool_name: Name of the tool to retrieve

        Returns:
            The requested tool or None if not found
        """
        tools = await self.get_tools(user_id)

        for tool in tools:
            if getattr(tool, 'name', '') == tool_name:
                logger.debug(f"Found Plaid MCP tool '{tool_name}' for user: {user_id}")
                return tool

        logger.warning(f"Plaid MCP tool '{tool_name}' not found for user: {user_id}")
        return None

    async def call_tool(self, user_id: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Generic method to call any Plaid MCP tool with the provided arguments.

        Args:
            user_id: Unique identifier for the user
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool

        Returns:
            Dict containing the tool result or error information

        Examples:
            # Create link token
            result = await client.call_tool(user_id, "create_link_token", user_id=user_id)

            # Exchange public token
            result = await client.call_tool(user_id, "exchange_public_token",
                                          user_id=user_id, public_token=token)

            # Get accounts
            result = await client.call_tool(user_id, "get_accounts", user_id=user_id)

            # Get transactions
            result = await client.call_tool(user_id, "get_all_transactions", user_id=user_id)
        """
        try:
            tool = await self.get_tool_by_name(user_id, tool_name)
            if not tool:
                return {
                    "status": "error",
                    "error": f"{tool_name} tool not available"
                }

            # Call the tool with provided arguments
            result = await tool.ainvoke(kwargs)

            logger.info(f"Called Plaid MCP tool '{tool_name}' for user: {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error calling Plaid MCP tool '{tool_name}' for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def list_available_tools(self, user_id: str) -> List[str]:
        """
        Get a list of available tool names for the user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            List of available tool names
        """
        tools = await self.get_tools(user_id)
        return [getattr(tool, 'name', 'unknown') for tool in tools]

    async def invalidate_client(self, user_id: str) -> None:
        """
        Invalidate and cleanup the MCP client for a specific user.

        This should be called when a user logs out or their session expires.

        Args:
            user_id: Unique identifier for the user
        """
        if user_id in self._client_locks:
            async with self._client_locks[user_id]:
                if user_id in self._user_clients:
                    # TODO: Add proper client cleanup if MultiServerMCPClient has cleanup methods
                    del self._user_clients[user_id]
                    logger.info(f"Invalidated Plaid MCP client for user: {user_id}")

                if user_id in self._tools_cache:
                    del self._tools_cache[user_id]
                    logger.debug(f"Cleared tools cache for user: {user_id}")

    async def cleanup_all_clients(self) -> None:
        """
        Cleanup all MCP clients and caches.

        This should be called during application shutdown.
        """
        logger.info("Cleaning up all Plaid MCP clients")

        # Clear all client references
        for user_id in list(self._user_clients.keys()):
            await self.invalidate_client(user_id)

        # Clear all data structures
        self._user_clients.clear()
        self._client_locks.clear()
        self._tools_cache.clear()

        logger.info("Plaid MCP client cleanup completed")


# Global instance following the established pattern
_plaid_mcp_client = None


def get_plaid_client() -> PlaidMCPClient:
    """
    Get or create the global PlaidMCPClient instance.

    Returns:
        Global PlaidMCPClient instance for reuse across agents
    """
    global _plaid_mcp_client
    if _plaid_mcp_client is None:
        _plaid_mcp_client = PlaidMCPClient()
        logger.info("Global PlaidMCPClient instance created")
    return _plaid_mcp_client