"""
Configuration for MCP Server.
"""

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