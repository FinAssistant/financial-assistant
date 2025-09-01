"""
Configuration for MCP Server.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class MCPConfig(BaseSettings):
    """MCP Server configuration."""
    
    # Core settings
    server_name: str = Field(default="financial-assistant-mcp", description="MCP server name")
    server_version: str = Field(default="0.1.0", description="Server version")
    server_port: int = Field(default=8001, description="Port for standalone MCP server mode")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Plaid configuration (will be used in Story 1.6)
    plaid_client_id: Optional[str] = Field(default=None, description="Plaid client ID")
    plaid_secret: Optional[str] = Field(default=None, description="Plaid secret key")
    plaid_env: str = Field(default="sandbox", description="Plaid environment")
    plaid_products: List[str] = Field(
        default_factory=lambda: ["transactions", "accounts", "balances"],
        description="Plaid products to use"
    )
    
    model_config = ConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create config from environment variables."""
        return cls()


# Global config instance
config = MCPConfig.from_env()