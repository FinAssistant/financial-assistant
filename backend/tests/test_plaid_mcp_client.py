"""
Unit tests for PlaidMCPClient functionality.

Tests the shared MCP client for Plaid integration including JWT authentication,
per-user caching, and tool access functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.mcp_clients.plaid_client import PlaidMCPClient, get_plaid_client


class TestPlaidMCPClient:
    """Test suite for PlaidMCPClient class."""

    def setup_method(self):
        """Setup method called before each test."""
        self.client = PlaidMCPClient()

    def test_plaid_mcp_client_initialization(self):
        """Test PlaidMCPClient initializes correctly."""
        assert self.client is not None
        assert self.client.plaid_mcp_url == "http://localhost:8000/mcp/"
        assert hasattr(self.client, '_auth_service')
        assert hasattr(self.client, '_user_clients')
        assert hasattr(self.client, '_client_locks')
        assert hasattr(self.client, '_tools_cache')

    def test_get_plaid_client_singleton(self):
        """Test get_plaid_client returns singleton instance."""
        client1 = get_plaid_client()
        client2 = get_plaid_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_get_client_generates_real_jwt(self):
        """Test that get_client generates real JWT tokens for users."""
        user_id = "test_jwt_user_123"

        # Mock MultiServerMCPClient creation to focus on JWT generation
        with patch('app.ai.mcp_clients.plaid_client.MultiServerMCPClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            # Mock the tools caching to avoid extra calls
            with patch.object(self.client, '_cache_tools'):
                # Call the PlaidMCPClient's get_client method
                client = await self.client.get_client(user_id)

                # Verify client was created
                assert client is mock_client_instance

                # Verify MultiServerMCPClient was called with proper config
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args[0][0]  # Get the config dict

                # Validate MCP config structure
                assert "plaid" in call_args
                assert "transport" in call_args["plaid"]
                assert "url" in call_args["plaid"]
                assert "headers" in call_args["plaid"]
                assert "Authorization" in call_args["plaid"]["headers"]

                # Validate JWT token format
                auth_header = call_args["plaid"]["headers"]["Authorization"]
                assert auth_header.startswith("Bearer ")
                jwt_token = auth_header.replace("Bearer ", "")

                # Validate JWT token is real (not mock placeholder)
                assert jwt_token != "mock-jwt-token-placeholder"
                assert len(jwt_token) > 20  # Real JWT tokens are much longer
                assert "." in jwt_token  # JWT tokens have dots as separators

                # Verify token can be validated by AuthService
                validated_user_id = self.client._auth_service.validate_access_token(jwt_token)
                assert validated_user_id == user_id, "Generated JWT should validate to the original user_id"

    @pytest.mark.asyncio
    async def test_get_client_error_handling(self):
        """Test get_client error handling when MCP client creation fails."""
        user_id = "test_error_user"

        # Mock MultiServerMCPClient to raise an exception
        with patch('app.ai.mcp_clients.plaid_client.MultiServerMCPClient', side_effect=Exception("Connection failed")):
            client = await self.client.get_client(user_id)

            # Should return None when creation fails
            assert client is None

    @pytest.mark.asyncio
    async def test_per_user_client_caching(self):
        """Test that MCP clients are cached per user and use different JWT tokens."""
        user_id_1 = "user_123"
        user_id_2 = "user_456"

        with patch('app.ai.mcp_clients.plaid_client.MultiServerMCPClient') as mock_client_class:
            # Create mock client instances
            mock_client_1 = AsyncMock()
            mock_client_2 = AsyncMock()
            mock_client_class.side_effect = [mock_client_1, mock_client_2]

            # Mock the tools caching to avoid extra calls
            with patch.object(self.client, '_cache_tools'):
                # Get clients for two different users
                client_1_first = await self.client.get_client(user_id_1)
                client_2_first = await self.client.get_client(user_id_2)

                # Get clients again for same users (should return cached)
                client_1_second = await self.client.get_client(user_id_1)
                client_2_second = await self.client.get_client(user_id_2)

                # Verify different users get different client instances
                assert client_1_first is mock_client_1
                assert client_2_first is mock_client_2

                # Verify caching - same users get same client instances
                assert client_1_second is mock_client_1
                assert client_2_second is mock_client_2

                # Verify MultiServerMCPClient was only called twice (once per user)
                assert mock_client_class.call_count == 2

                # Verify different JWT tokens were generated for different users
                call_args_1 = mock_client_class.call_args_list[0][0][0]
                call_args_2 = mock_client_class.call_args_list[1][0][0]

                jwt_token_1 = call_args_1["plaid"]["headers"]["Authorization"].replace("Bearer ", "")
                jwt_token_2 = call_args_2["plaid"]["headers"]["Authorization"].replace("Bearer ", "")

                # Tokens should be different for different users
                assert jwt_token_1 != jwt_token_2

                # But both should validate to their respective users
                assert self.client._auth_service.validate_access_token(jwt_token_1) == user_id_1
                assert self.client._auth_service.validate_access_token(jwt_token_2) == user_id_2

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool calling through PlaidMCPClient."""
        user_id = "test_user"
        tool_name = "get_all_transactions"

        # Mock tool response
        mock_tool = AsyncMock()
        mock_tool.name = tool_name
        mock_tool.ainvoke = AsyncMock(return_value={
            "status": "success",
            "transactions": [{"id": "tx1", "amount": 100.0}],
            "total_transactions": 1
        })

        # Mock get_tool_by_name to return our mock tool
        with patch.object(self.client, 'get_tool_by_name', return_value=mock_tool):
            result = await self.client.call_tool(user_id, tool_name, some_param="value")

            # Verify successful response
            assert result["status"] == "success"
            assert "transactions" in result
            assert result["total_transactions"] == 1

            # Verify tool was called with correct arguments
            mock_tool.ainvoke.assert_called_once_with({"some_param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        """Test call_tool when tool is not available."""
        user_id = "test_user"
        tool_name = "nonexistent_tool"

        # Mock get_tool_by_name to return None (tool not found)
        with patch.object(self.client, 'get_tool_by_name', return_value=None):
            result = await self.client.call_tool(user_id, tool_name)

            # Verify error response
            assert result["status"] == "error"
            assert "not available" in result["error"]

    @pytest.mark.asyncio
    async def test_get_tools_caching(self):
        """Test that tools are cached per user."""
        user_id = "test_user"

        # Mock client and tools
        mock_client = AsyncMock()
        mock_tools = [MagicMock(name="tool1"), MagicMock(name="tool2")]
        mock_client.get_tools = AsyncMock(return_value=mock_tools)

        # Mock get_client to return our mock client
        with patch.object(self.client, 'get_client', return_value=mock_client):
            # First call should fetch tools and cache them
            tools1 = await self.client.get_tools(user_id)

            # Second call should return cached tools
            tools2 = await self.client.get_tools(user_id)

            # Verify tools are returned correctly
            assert tools1 == mock_tools
            assert tools2 == mock_tools

            # Verify tools are cached (get_client called only once during first call)
            assert user_id in self.client._tools_cache
            assert self.client._tools_cache[user_id] == mock_tools

    @pytest.mark.asyncio
    async def test_invalidate_client(self):
        """Test client invalidation and cleanup."""
        user_id = "test_user"

        # Set up client and cache data
        mock_client = AsyncMock()
        self.client._user_clients[user_id] = mock_client
        self.client._tools_cache[user_id] = ["tool1", "tool2"]

        # Add a lock for the user
        import asyncio
        self.client._client_locks[user_id] = asyncio.Lock()

        # Invalidate the client
        await self.client.invalidate_client(user_id)

        # Verify cleanup
        assert user_id not in self.client._user_clients
        assert user_id not in self.client._tools_cache

    @pytest.mark.asyncio
    async def test_cleanup_all_clients(self):
        """Test cleanup of all clients and caches."""
        # Set up multiple users
        user_ids = ["user1", "user2", "user3"]

        for user_id in user_ids:
            self.client._user_clients[user_id] = AsyncMock()
            self.client._tools_cache[user_id] = ["tool1"]
            import asyncio
            self.client._client_locks[user_id] = asyncio.Lock()

        # Cleanup all clients
        await self.client.cleanup_all_clients()

        # Verify all data structures are empty
        assert len(self.client._user_clients) == 0
        assert len(self.client._tools_cache) == 0
        assert len(self.client._client_locks) == 0

    @pytest.mark.asyncio
    async def test_list_available_tools(self):
        """Test listing available tool names."""
        user_id = "test_user"

        # Mock tools with proper name attributes
        mock_tool1 = MagicMock()
        mock_tool1.name = "create_link_token"
        mock_tool2 = MagicMock()
        mock_tool2.name = "get_accounts"
        mock_tool3 = MagicMock()
        mock_tool3.name = "get_all_transactions"

        mock_tools = [mock_tool1, mock_tool2, mock_tool3]

        # Mock get_tools to return our mock tools
        with patch.object(self.client, 'get_tools', return_value=mock_tools):
            tool_names = await self.client.list_available_tools(user_id)

            # Verify tool names are returned
            expected_names = ["create_link_token", "get_accounts", "get_all_transactions"]
            assert tool_names == expected_names

    @pytest.mark.asyncio
    async def test_get_tool_by_name_found(self):
        """Test getting a specific tool by name when it exists."""
        user_id = "test_user"
        target_tool_name = "get_accounts"

        # Mock tools with proper name attributes
        mock_tool1 = MagicMock()
        mock_tool1.name = "create_link_token"
        mock_tool2 = MagicMock()
        mock_tool2.name = "get_accounts"
        mock_tool3 = MagicMock()
        mock_tool3.name = "get_all_transactions"

        mock_tools = [mock_tool1, mock_tool2, mock_tool3]

        # Mock get_tools to return our mock tools
        with patch.object(self.client, 'get_tools', return_value=mock_tools):
            found_tool = await self.client.get_tool_by_name(user_id, target_tool_name)

            # Verify correct tool was found
            assert found_tool is mock_tool2  # The "get_accounts" tool

    @pytest.mark.asyncio
    async def test_get_tool_by_name_not_found(self):
        """Test getting a specific tool by name when it doesn't exist."""
        user_id = "test_user"
        target_tool_name = "nonexistent_tool"

        # Mock tools (without the target tool) with proper name attributes
        mock_tool1 = MagicMock()
        mock_tool1.name = "create_link_token"
        mock_tool2 = MagicMock()
        mock_tool2.name = "get_accounts"

        mock_tools = [mock_tool1, mock_tool2]

        # Mock get_tools to return our mock tools
        with patch.object(self.client, 'get_tools', return_value=mock_tools):
            found_tool = await self.client.get_tool_by_name(user_id, target_tool_name)

            # Verify tool was not found
            assert found_tool is None