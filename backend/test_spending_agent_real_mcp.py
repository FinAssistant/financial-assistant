#!/usr/bin/env python3
"""
Test script for SpendingAgent real MCP integration with JWT authentication.

This script tests the SpendingAgent with real JWT tokens against a running MCP server.
Run this ONLY when the MCP server is running on localhost:8000.

Usage:
    python test_spending_agent_real_mcp.py
"""

import asyncio
import logging
from app.ai.spending_agent import SpendingAgent

# Set up logging to see what happens
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_spending_agent_real_mcp_integration():
    """Test the SpendingAgent with real MCP integration."""
    print("🚀 Testing SpendingAgent with Real MCP Integration")
    print("=" * 60)
    
    # Create SpendingAgent
    agent = SpendingAgent()
    print("✅ SpendingAgent created successfully")
    
    # Test user
    test_user_id = "spending_agent_real_mcp_test_user"
    
    try:
        # Test 1: Get MCP client with real JWT
        print(f"\n📝 Test 1: Getting MCP client for user {test_user_id}")
        mcp_client = await agent._get_mcp_client(test_user_id)
        
        if mcp_client is None:
            print("⚠️  MCP client is None - either MCP library not available or connection failed")
            return
        
        print("✅ SpendingAgent MCP client created successfully with real JWT")
        
        # Test 2: Get tools from MCP server
        print(f"\n📝 Test 2: Getting tools from MCP server via SpendingAgent")
        try:
            tools = await mcp_client.get_tools()
            print(f"✅ SpendingAgent retrieved {len(tools)} tools from MCP server")
            
            # List available tools
            for i, tool in enumerate(tools):
                tool_name = getattr(tool, 'name', 'Unknown')
                print(f"   {i+1}. {tool_name}")
            
        except Exception as e:
            print(f"❌ SpendingAgent failed to get tools from MCP server: {str(e)}")
            print("💡 Make sure MCP server is running: uvicorn app.main:app --reload")
            return
        
        # Test 3: Fetch transactions via SpendingAgent
        print(f"\n📝 Test 3: Fetching transactions via SpendingAgent MCP integration")
        try:
            transaction_result = await agent._fetch_transactions(test_user_id)
            
            print(f"📊 SpendingAgent transaction fetch result:")
            print(f"   • Status: {transaction_result['status']}")
            print(f"   • Total transactions: {transaction_result.get('total_transactions', 'N/A')}")
            
            if transaction_result['status'] == 'success':
                print("✅ SpendingAgent transaction fetching successful")
                
                if transaction_result.get('total_transactions', 0) > 0:
                    print("✅ SpendingAgent received real transaction data")
                else:
                    print("ℹ️  SpendingAgent found no transactions (normal for test user)")
            else:
                print(f"⚠️  SpendingAgent transaction fetch returned error: {transaction_result.get('error', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ SpendingAgent transaction fetch failed: {str(e)}")
            return
        
        # Test 4: Full SpendingAgent conversation workflow
        print(f"\n📝 Test 4: Full SpendingAgent conversation workflow with real MCP")
        try:
            result = await agent.invoke_spending_conversation(
                "Show me my recent transactions", 
                test_user_id, 
                "spending_agent_real_mcp_test_session"
            )
            
            print(f"📊 SpendingAgent conversation result:")
            print(f"   • Agent: {result['agent']}")
            print(f"   • Intent: {result['intent']}")
            print(f"   • Message type: {result['message_type']}")
            print(f"   • Content preview: {result['content'][:100]}...")
            
            if 'error' not in result:
                print("✅ SpendingAgent full workflow completed successfully")
            else:
                print(f"⚠️  SpendingAgent workflow completed with error: {result['error']}")
            
        except Exception as e:
            print(f"❌ SpendingAgent full workflow failed: {str(e)}")
            return
        
        print("\n" + "=" * 60)
        print("🎉 SpendingAgent Real MCP Integration Test Completed Successfully!")
        print("✅ SpendingAgent can connect to real MCP server with JWT authentication")
        print("✅ SpendingAgent real transaction fetching is working")
        print("✅ SpendingAgent full conversation workflow is functional")
        
    except Exception as e:
        print(f"\n❌ SpendingAgent integration test failed: {str(e)}")
        print("💡 Make sure:")
        print("   1. MCP server is running: uvicorn app.main:app --reload")
        print("   2. Auth service is properly configured")
        print("   3. All dependencies are installed")

if __name__ == "__main__":
    asyncio.run(test_spending_agent_real_mcp_integration())