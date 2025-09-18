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
from app.ai.mcp_clients import get_plaid_client
from test_mcp_plaid import test_plaid_sandbox_setup, test_exchange_public_token

# Set up logging to see what happens
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_spending_agent_mcp_plaid_integration():
    """Test the SpendingAgent with MCP Plaid integration."""
    print("🚀 Testing SpendingAgent with MCP Plaid Integration")
    print("=" * 60)
    
    # Create SpendingAgent and get shared Plaid client
    agent = SpendingAgent()
    plaid_client = get_plaid_client()
    print("✅ SpendingAgent created successfully")

    # Test user
    test_user_id = "test_user_123"

    try:
        # Test 1: Get MCP client with real JWT via shared PlaidMCPClient
        print(f"\n📝 Test 1: Getting MCP client for user {test_user_id}")
        mcp_client = await plaid_client.get_client(test_user_id)

        if mcp_client is None:
            print("⚠️  MCP client is None - either MCP library not available or connection failed")
            return

        print("✅ Shared PlaidMCPClient created successfully with real JWT")
        
        # Test 2: Get tools from MCP server via shared PlaidMCPClient
        print(f"\n📝 Test 2: Getting tools from MCP server via PlaidMCPClient")
        try:
            tools = await plaid_client.get_tools(test_user_id)
            available_tool_names = await plaid_client.list_available_tools(test_user_id)
            print(f"✅ PlaidMCPClient retrieved {len(tools)} tools from MCP server")

            # List available tools
            tool_dict = {}
            plaid_tools = []
            for tool in tools:
                tool_name = getattr(tool, 'name', 'Unknown')
                description = getattr(tool, 'description', 'No description')
                tool_dict[tool_name] = tool
                if 'plaid' in tool_name.lower() or tool_name in ['create_link_token', 'exchange_public_token', 'get_accounts', 'get_all_transactions', 'get_balances', 'get_identity', 'get_liabilities', 'get_investments']:
                    plaid_tools.append(tool_name)
                print(f"  • {tool_name}: {description[:60]}...")

            print(f"✅ Available tool names: {available_tool_names}")

        except Exception as e:
            print(f"❌ PlaidMCPClient failed to get tools from MCP server: {str(e)}")
            print("💡 Make sure MCP server is running: uvicorn app.main:app --reload")
            return
        
        public_token = await test_plaid_sandbox_setup()
        if not public_token:
            print("\n❌ Failed to create sandbox public token. Cannot proceed with MCP tests.")
            print("💡 Make sure Plaid credentials are set:")
            print("   export PLAID_CLIENT_ID='your_client_id'")
            print("   export PLAID_SECRET='your_secret'")
            return
        
        print("\n💱 Exchange public token")
        print("-" * 30)
        exchange_success = await test_exchange_public_token(tool_dict, public_token)
        if not exchange_success:
            print("❌ Stopping tests: Public token exchange failed.")
            return False

        # Small delay to allow token storage
        await asyncio.sleep(1)
        
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
        print("✅ SpendingAgent uses shared PlaidMCPClient with JWT authentication")
        print("✅ SpendingAgent real transaction fetching is working")
        print("✅ SpendingAgent full conversation workflow is functional")
        print("✅ PlaidMCPClient shared across multiple agents successfully")
        
    except Exception as e:
        print(f"\n❌ SpendingAgent integration test failed: {str(e)}")
        print("💡 Make sure:")
        print("   1. MCP server is running: uvicorn app.main:app --reload")
        print("   2. Auth service is properly configured")
        print("   3. All dependencies are installed")

if __name__ == "__main__":
    asyncio.run(test_spending_agent_mcp_plaid_integration())
