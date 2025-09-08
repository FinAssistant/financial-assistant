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
from fastmcp.server.dependencies import get_access_token, AccessToken

from fastmcp.server.auth.providers.jwt import JWTVerifier
from app.services.auth_service import AuthService
from app.services.plaid_service import PlaidService

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level)
)
logger = logging.getLogger(__name__)

# Get auth service for JWT configuration
auth_service = AuthService()

# Initialize PlaidService
plaid_service = PlaidService()

# Configure JWT verifier with your existing secret key
jwt_verifier = JWTVerifier(
    public_key=auth_service.secret_key,  # Use your existing secret key
    algorithm=auth_service.algorithm,  # HS256
)

# Initialize FastMCP server
mcp = FastMCP(
    name=config.server_name,
    version=config.server_version,
    auth=jwt_verifier
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


@mcp.tool
async def whoami() -> Dict[str, Any]:
    """
    Get information about the authenticated user from JWT token.
    
    Returns:
        Authenticated user information from JWT context
    """
    logger.info("🐛 whoami tool called")

    try:
        token: AccessToken | None = get_access_token()
        logger.info(f"🐛 Token type: {type(token)}")

        if token is None:
            logger.info("🐛 No token found, returning unauthenticated")
            result = {"authenticated": False, "debug": "no_token"}
            logger.info(f"🐛 Returning: {result}")
            return result

        logger.info(f"🐛 Token attributes: client_id={getattr(token, 'client_id', 'N/A')}, scopes={getattr(token, 'scopes', 'N/A')}")
        logger.info(f"🐛 Token claims: {getattr(token, 'claims', 'N/A')}")

        result = {
            "authenticated": True,
            "user_id": token.claims.get("sub", {}).get("user_id"),
            "email": token.claims.get("sub", {}).get("email"),
            "name": token.claims.get("sub", {}).get("name"),
            "scopes": token.scopes,
            "expires_at": token.expires_at,
            "debug": "token_found"
        }

        logger.info(f"🐛 Returning authenticated result")
        return result

    except Exception as e:
        logger.error(f"🐛 Exception in whoami: {e}")
        logger.error(f"🐛 Exception type: {type(e)}")
        import traceback
        logger.error(f"🐛 Traceback: {traceback.format_exc()}")

        error_result = {
            "authenticated": False, 
            "error": str(e),
            "debug": "exception_occurred"
        }
        logger.info(f"🐛 Returning error result: {error_result}")
        return error_result



def get_mcp_app():
    """
    Get the FastMCP ASGI application for integration with FastAPI.
    
    Returns:
        ASGI application that can be mounted in FastAPI
    """
    # Register tools with PlaidService instance
    register_plaid_tools(mcp, plaid_service)
    logger.info("Registered Plaid tools with PlaidService")
    
    # Return the ASGI app for mounting in FastAPI
    return mcp.http_app(path="/", stateless_http=True, transport="streamable-http")


def run_server():
    """Run the MCP server standalone (for testing)."""
    logger.info(f"Starting MCP server: {config.server_name} v{config.server_version}")
    logger.info(f"Server will run on port: {config.server_port}")
    
    # Register Plaid tools with PlaidService
    register_plaid_tools(mcp, plaid_service)
    logger.info("Registered Plaid tools with PlaidService")
    
    # Run the FastMCP server with HTTP transport
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=config.server_port
    )


if __name__ == "__main__":
    run_server()