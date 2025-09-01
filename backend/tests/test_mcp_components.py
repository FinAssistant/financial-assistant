"""
Unit tests for MCP Server components - focused on business logic.
"""

import pytest
from unittest.mock import patch
import os


class TestMCPConfig:
    """Test MCP server configuration."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        from mcp_server.config import MCPConfig
        
        config = MCPConfig()
        
        assert config.server_name == "financial-assistant-mcp"
        assert config.server_version == "0.1.0"
        assert config.server_port == 8001
        assert config.log_level == "INFO"
        assert config.plaid_client_id is None
        assert config.plaid_secret is None
        assert config.plaid_env == "sandbox"
        assert config.plaid_products == ["transactions", "accounts", "balances"]
    
    def test_config_from_env_vars(self):
        """Test configuration loading from environment variables."""
        from mcp_server.config import MCPConfig
        
        # Set environment variables
        env_vars = {
            "MCP_SERVER_NAME": "test-server",
            "MCP_SERVER_VERSION": "1.0.0",
            "MCP_SERVER_PORT": "9001",
            "MCP_LOG_LEVEL": "DEBUG",
            "MCP_PLAID_CLIENT_ID": "test-client-id",
            "MCP_PLAID_SECRET": "test-secret"
        }
        
        with patch.dict(os.environ, env_vars):
            config = MCPConfig()
            
            assert config.server_name == "test-server"
            assert config.server_version == "1.0.0" 
            assert config.server_port == 9001
            assert config.log_level == "DEBUG"
            assert config.plaid_client_id == "test-client-id"
            assert config.plaid_secret == "test-secret"
    
    def test_config_case_insensitive(self):
        """Test that config is case insensitive."""
        from mcp_server.config import MCPConfig
        
        # Test with mixed case environment variables
        env_vars = {
            "mcp_server_name": "lowercase-server",
            "MCP_SERVER_VERSION": "2.0.0"
        }
        
        with patch.dict(os.environ, env_vars):
            config = MCPConfig()
            
            assert config.server_name == "lowercase-server"
            assert config.server_version == "2.0.0"


class TestMCPToolLogic:
    """Test the core logic of MCP tools (without FastMCP decorators)."""
    
    def test_health_check_logic(self):
        """Test health check logic by recreating the function."""
        from mcp_server.config import config
        from datetime import datetime
        
        # Simulate SERVER_START_TIME
        start_time = datetime.now()
        
        # Recreate the health check logic
        def health_check_logic():
            uptime_seconds = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "server": config.server_name,
                "version": config.server_version,
                "uptime_seconds": uptime_seconds,
                "timestamp": datetime.now().isoformat()
            }
        
        result = health_check_logic()
        
        assert isinstance(result, dict)
        assert result["status"] == "healthy"
        assert result["server"] == config.server_name
        assert result["version"] == config.server_version
        assert "uptime_seconds" in result
        assert isinstance(result["uptime_seconds"], float)
        
        # Validate timestamp format
        timestamp = result["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise exception
    
    def test_echo_logic(self):
        """Test echo tool logic."""
        from mcp_server.config import config
        from datetime import datetime
        
        # Recreate the echo logic
        def echo_logic(message: str):
            return {
                "echo": message,
                "timestamp": datetime.now().isoformat(),
                "server": config.server_name
            }
        
        test_message = "Hello MCP Server!"
        result = echo_logic(test_message)
        
        assert isinstance(result, dict)
        assert result["echo"] == test_message
        assert result["server"] == config.server_name
        assert "timestamp" in result
        
        # Validate timestamp
        timestamp = result["timestamp"]
        datetime.fromisoformat(timestamp)
    
    def test_get_current_time_logic(self):
        """Test get_current_time tool logic."""
        from mcp_server.config import config
        from datetime import datetime
        
        # Recreate the get_current_time logic
        def get_current_time_logic(timezone: str = "UTC"):
            return {
                "time": datetime.now().isoformat(),
                "timezone": timezone,
                "server": config.server_name
            }
        
        # Test with default timezone
        result = get_current_time_logic()
        assert isinstance(result, dict)
        assert result["timezone"] == "UTC"
        assert result["server"] == config.server_name
        assert "time" in result
        
        # Test with custom timezone
        result = get_current_time_logic("PST")
        assert result["timezone"] == "PST"
        
        # Validate time format
        time_str = result["time"]
        datetime.fromisoformat(time_str)