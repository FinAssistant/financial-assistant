"""
Core MCP Server implementation using FastMCP for AI Financial Assistant.
"""

from fastmcp import FastMCP
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import os

from .config import config
from .tools.plaid_tools import register_plaid_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level)
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name=config.server_name,
    version=config.server_version
)

# Server start time for health checks
SERVER_START_TIME = datetime.now()


@mcp.tool
def mcp_health_check() -> Dict[str, Any]:
    """
    Check MCP server health status.
    
    Returns:
        Dictionary containing health status information
    """
    uptime_seconds = (datetime.now() - SERVER_START_TIME).total_seconds()
    
    return {
        "status": "healthy",
        "server": config.server_name,
        "version": config.server_version,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now().isoformat()
    }


@mcp.tool
def echo(message: str) -> Dict[str, str]:
    """
    Echo the input message back.
    
    Args:
        message: Message to echo
        
    Returns:
        Dictionary with echoed message and metadata
    """
    return {
        "echo": message,
        "timestamp": datetime.now().isoformat(),
        "server": config.server_name
    }


@mcp.tool
def get_current_time(timezone: str = "UTC") -> Dict[str, str]:
    """
    Get the current time.
    
    Args:
        timezone: Timezone (currently only UTC supported)
        
    Returns:
        Current time information
    """
    return {
        "time": datetime.now().isoformat(),
        "timezone": timezone,
        "server": config.server_name
    }



def get_mcp_app():
    """
    Get the FastMCP ASGI application for integration with FastAPI.
    
    Returns:
        ASGI application that can be mounted in FastAPI
    """
    # Register tools first
    register_plaid_tools(mcp)
    logger.info("Registered Plaid tools (placeholders for Story 1.6)")
    
    # Return the ASGI app for mounting in FastAPI
    return mcp.http_app(path="/", stateless_http=True, transport="streamable-http")


def run_server():
    """Run the MCP server standalone (for testing)."""
    logger.info(f"Starting MCP server: {config.server_name} v{config.server_version}")
    logger.info(f"Server will run on port: {config.server_port}")
    
    # Register Plaid tools (will be implemented in Story 1.6)
    register_plaid_tools(mcp)
    logger.info("Registered Plaid tools (placeholders for Story 1.6)")
    
    # Run the FastMCP server with HTTP transport
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=config.server_port
    )


if __name__ == "__main__":
    run_server()