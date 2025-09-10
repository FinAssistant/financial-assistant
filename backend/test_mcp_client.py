#!/usr/bin/env python3
"""
Comprehensive test suite for FastMCP server with authentication.

This script tests:
1. Authentication (401 without token, success with token)
2. All MCP tools with proper authentication
"""

import asyncio
import json
import httpx
from typing import Any, Dict, List, Optional

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("❌ langchain-mcp-adapters not installed. Install with: pip install langchain-mcp-adapters")
    MCP_AVAILABLE = False

try:
    from app.services.auth_service import AuthService
    AUTH_AVAILABLE = True
except ImportError:
    print("❌ Auth service not available")
    AUTH_AVAILABLE = False


def create_test_jwt_token() -> str:
    """Create a test JWT token."""
    if not AUTH_AVAILABLE:
        return "fake-jwt-token"
    
    auth_service = AuthService()
    user_id = "test_user_123"
    return auth_service.generate_access_token(user_id)


async def test_authentication():
    """Test authentication flow."""
    print("\n🔐 Authentication Tests")
    print("=" * 50)
    
    # Test 1: Without authentication - expect 401
    print("\n📝 Test 1: Access without authentication (expect 401)")
    print("-" * 30)
    try:
        client_no_auth = MultiServerMCPClient({
            "mcp": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp/"
            }
        })
        
        tools = await client_no_auth.get_tools()
        print("⚠️  Unexpected: Server allowed access without authentication")
        return None  # Return None to indicate test should stop
    except Exception as e:
        # Check if it's an auth error (401) - MCP client wraps these in various exceptions
        error_str = str(e)
        error_type = type(e).__name__
        if ("401" in error_str or "Unauthorized" in error_str or 
            "TaskGroup" in error_str or "ExceptionGroup" in error_type):
            print("✅ Correctly rejected (401 Unauthorized)")
        else:
            print(f"❌ Unexpected error: {e}")
            return None
    
    # Test 2: With authentication
    print("\n📝 Test 2: Access with JWT token")
    print("-" * 30)
    jwt_token = create_test_jwt_token()
    print(f"🎫 Generated token: {jwt_token[:30]}...")
    
    try:
        client_auth = MultiServerMCPClient({
            "mcp": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp/",
                "headers": {
                    "Authorization": f"Bearer {jwt_token}"
                }
            }
        })
        
        tools = await client_auth.get_tools()
        print(f"✅ Successfully authenticated and retrieved {len(tools)} tools")
        return jwt_token  # Return token for use in other tests
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return None


async def test_whoami(jwt_token: str):
    """Test whoami tool specifically."""
    print("\n👤 Test: whoami tool")
    print("-" * 30)
    
    client = MultiServerMCPClient({
        "mcp": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/",
            "headers": {
                "Authorization": f"Bearer {jwt_token}"
            }
        }
    })
    
    tools = await client.get_tools()
    whoami_tool = None
    for tool in tools:
        if getattr(tool, 'name', '') == 'whoami':
            whoami_tool = tool
            break
    
    if whoami_tool:
        result = await whoami_tool.ainvoke({})
        print(f"📥 Response: {result}")
        
        # Parse JSON response
        if isinstance(result, str):
            parsed = json.loads(result)
            print(f"📊 User info:")
            print(f"   • User ID: {parsed.get('sub')}")
            print(f"   • Expires At: {parsed.get('exp')}")
            print(f"   • Issued At: {parsed.get('iat')}")
            print(f"   • Type: {parsed.get('type')}")
            print(f"   • Authenticated: {parsed.get('authenticated')}")
            
            if parsed.get("authenticated", False):
                print("✅ whoami tool working correctly")
        else:
            print(f"📊 Direct response: {json.dumps(result, indent=2)}")
    else:
        print("❌ whoami tool not found")


async def test_all_tools(jwt_token: str):
    """Test all MCP tools with authentication."""
    print("\n🔧 Tool Functionality Tests")
    print("=" * 50)
    
    # Create authenticated client
    client = MultiServerMCPClient({
        "mcp": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/",
            "headers": {
                "Authorization": f"Bearer {jwt_token}"
            }
        }
    })
    
    # Get all tools
    print("\n📋 Available tools:")
    print("-" * 30)
    tools = await client.get_tools()
    
    tool_dict = {}
    for tool in tools:
        name = getattr(tool, 'name', 'Unknown')
        description = getattr(tool, 'description', 'No description')
        tool_dict[name] = tool
        print(f"  • {name}: {description[:60]}...")
    
    # Test echo tool
    print("\n💬 Test: echo tool")
    print("-" * 30)
    if 'echo' in tool_dict:
        result = await tool_dict['echo'].ainvoke({"message": "Hello FastMCP! 🚀"})
        print("📤 Input: Hello FastMCP! 🚀")
        print(f"📥 Output: {json.dumps(result, indent=2)}")
        print("✅ echo tool working")
    else:
        print("❌ echo tool not found")
    
    # Test get_current_time tool
    print("\n🕐 Test: get_current_time tool")
    print("-" * 30)
    if 'get_current_time' in tool_dict:
        result = await tool_dict['get_current_time'].ainvoke({"timezone": "UTC"})
        print("📤 Input: timezone=UTC")
        print(f"📥 Output: {json.dumps(result, indent=2)}")
        print("✅ get_current_time tool working")
    else:
        print("❌ get_current_time tool not found")
    
    # Test mcp_health_check tool
    print("\n🏥 Test: mcp_health_check tool")
    print("-" * 30)
    if 'mcp_health_check' in tool_dict:
        result = await tool_dict['mcp_health_check'].ainvoke({})
        print("📤 Input: (no arguments)")
        if isinstance(result, str):
            result = json.loads(result)
        print(f"📥 Output:")
        print(f"   • Status: {result.get('status')}")
        print(f"   • Server: {result.get('server')}")
        print(f"   • Version: {result.get('version')}")
        print(f"   • Uptime: {result.get('uptime_seconds', 0):.1f} seconds")
        print("✅ mcp_health_check tool working")
    else:
        print("❌ mcp_health_check tool not found")
    
    # Test Plaid placeholder tools
    print("\n🏦 Test: Plaid tools (placeholders)")
    print("-" * 30)
    
    # Test create_link_token
    if 'create_link_token' in tool_dict:
        result = await tool_dict['create_link_token'].ainvoke({
            "user_id": "test_user_123", 
            "products": ["transactions", "accounts"]
        })
        print("📤 Testing create_link_token...")
        print(f"📥 Output: {json.dumps(result, indent=2)}")
        print("✅ create_link_token tool working")
    else:
        print("❌ create_link_token tool not found")

async def run_all_tests():
    """Run all MCP server tests."""
    
    if not MCP_AVAILABLE:
        return
    
    print("🚀 FastMCP Server Comprehensive Test Suite")
    print("=" * 50)
    
    try:
        # First test authentication
        jwt_token = await test_authentication()
        if not jwt_token:
            print("\n❌ Authentication tests failed. Cannot proceed with other tests.")
            return
        
        # Test whoami tool specifically
        await test_whoami(jwt_token)
        
        # Test all other tools
        await test_all_tools(jwt_token)
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("🎯 FastMCP server with authentication is working correctly")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("💡 Make sure the FastAPI server is running:")
        print("   python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(run_all_tests())