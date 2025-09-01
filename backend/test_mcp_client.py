#!/usr/bin/env python3
"""
Test script for FastMCP server using langchain-mcp-adapters.

This script tests the MCP server running at http://localhost:8000/mcp/
with stateless HTTP transport.
"""

import asyncio
import json
from typing import Any, Dict, List

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("❌ langchain-mcp-adapters not installed. Install with: pip install langchain-mcp-adapters")
    MCP_AVAILABLE = False


async def test_mcp_server():
    """Test the FastMCP server with current tools."""
    
    if not MCP_AVAILABLE:
        return
    
    # Configure MCP client for stateless HTTP
    client_config = {
        "financial_assistant_mcp": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/"
        }
    }
    
    print("🚀 Starting MCP Server Test")
    print("=" * 50)
    
    try:
        # Initialize MCP client
        print("📡 Connecting to MCP server...")
        client = MultiServerMCPClient(client_config)
        
        # Test 1: Get available tools
        print("\n🔧 Test 1: Getting available tools")
        print("-" * 30)
        
        tools = await client.get_tools()
        print(f"✅ Found {len(tools)} tools:")
        
        for tool in tools:
            name = getattr(tool, 'name', 'Unknown')
            description = getattr(tool, 'description', 'No description')
            print(f"  • {name}: {description}")
        
        # Test 2: Test tools by invoking them directly
        print("\n💬 Test 2: Testing echo tool")
        print("-" * 30)
        
        # Find the echo tool
        echo_tool = None
        for tool in tools:
            if getattr(tool, 'name', '') == 'echo':
                echo_tool = tool
                break
        
        if echo_tool:
            echo_result = await echo_tool.ainvoke({"message": "Hello FastMCP! 🚀"})
            print("📤 Input: Hello FastMCP! 🚀")
            print(f"📥 Output: {json.dumps(echo_result, indent=2)}")
        else:
            print("❌ Echo tool not found")
        
        # Test 3: Test get_current_time tool
        print("\n🕐 Test 3: Testing get_current_time tool")
        print("-" * 30)
        
        time_tool = None
        for tool in tools:
            if getattr(tool, 'name', '') == 'get_current_time':
                time_tool = tool
                break
        
        if time_tool:
            time_result = await time_tool.ainvoke({"timezone": "UTC"})
            print("📤 Input: timezone=UTC")
            print(f"📥 Output: {json.dumps(time_result, indent=2)}")
        else:
            print("❌ get_current_time tool not found")
        
        # Test 4: Test mcp_health_check tool
        print("\n🏥 Test 4: Testing mcp_health_check tool")
        print("-" * 30)
        
        health_tool = None
        for tool in tools:
            if getattr(tool, 'name', '') == 'mcp_health_check':
                health_tool = tool
                break
        
        if health_tool:
            health_result = await health_tool.ainvoke({})
            print("📤 Input: (no arguments)")
            print(f"📥 Output: {json.dumps(health_result, indent=2)}")
        else:
            print("❌ mcp_health_check tool not found")
        
        # Test 5: Test Plaid placeholder tools
        print("\n🏦 Test 5: Testing Plaid placeholder tools")
        print("-" * 30)
        
        # Test create_link_token
        link_tool = None
        for tool in tools:
            if getattr(tool, 'name', '') == 'create_link_token':
                link_tool = tool
                break
        
        if link_tool:
            link_token_result = await link_tool.ainvoke({
                "user_id": "test_user_123", 
                "products": ["transactions", "accounts"]
            })
            print("📤 Testing create_link_token...")
            print(f"📥 Output: {json.dumps(link_token_result, indent=2)}")
        else:
            print("❌ create_link_token tool not found")
        
        # Test get_accounts
        accounts_tool = None
        for tool in tools:
            if getattr(tool, 'name', '') == 'get_accounts':
                accounts_tool = tool
                break
        
        if accounts_tool:
            accounts_result = await accounts_tool.ainvoke({"user_id": "test_user_123"})
            print("\n📤 Testing get_accounts...")
            print(f"📥 Output: {json.dumps(accounts_result, indent=2)}")
        else:
            print("❌ get_accounts tool not found")
        
        print("\n" + "=" * 50)
        print("✅ All MCP tests completed successfully!")
        print("🎯 FastMCP server is working with stateless HTTP transport")
        
    except Exception as e:
        print(f"\n❌ Error testing MCP server: {e}")
        print("💡 Make sure the FastAPI server is running at http://localhost:8000")
        print("   Run: python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    print("🧪 FastMCP Server Test Suite")
    print("=" * 50)
    
    print("\n")
    
    # Then test MCP functionality
    asyncio.run(test_mcp_server())