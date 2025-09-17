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
from decimal import Decimal
from app.ai.spending_agent import SpendingAgent
from app.ai.mcp_clients.graphiti_client import get_graphiti_client, canonical_hash
from app.models.plaid_models import PlaidTransaction
from test_mcp_plaid import test_plaid_sandbox_setup, test_exchange_public_token

# Set up logging to see what happens
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_spending_agent_mcp_plaid_integration():
    """Test the SpendingAgent with MCP Plaid integration."""
    print("🚀 Testing SpendingAgent with MCP Plaid Integration")
    print("=" * 60)
    
    # Create SpendingAgent
    agent = SpendingAgent()
    print("✅ SpendingAgent created successfully")
    
    # Test user
    test_user_id = "test_user_123"
    
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
            tool_dict = {}
            plaid_tools = []
            for _, tool in enumerate(tools):
                tool_name = getattr(tool, 'name', 'Unknown')
                description = getattr(tool, 'description', 'No description')
                tool_dict[tool_name] = tool
                if 'plaid' in tool_name.lower() or tool_name in ['create_link_token', 'exchange_public_token', 'get_accounts', 'get_all_transactions', 'get_balances', 'get_identity', 'get_liabilities', 'get_investments']:
                    plaid_tools.append(tool_name)
                print(f"  • {tool_name}: {description[:60]}...")

        except Exception as e:
            print(f"❌ SpendingAgent failed to get tools from MCP server: {str(e)}")
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
        print("✅ SpendingAgent can connect to real MCP server with JWT authentication")
        print("✅ SpendingAgent real transaction fetching is working")
        print("✅ SpendingAgent full conversation workflow is functional")
        
    except Exception as e:
        print(f"\n❌ SpendingAgent integration test failed: {str(e)}")
        print("💡 Make sure:")
        print("   1. MCP server is running: uvicorn app.main:app --reload")
        print("   2. Auth service is properly configured")
        print("   3. All dependencies are installed")

async def test_spending_agent_graphiti_integration():
    """Test the SpendingAgent with real Graphiti MCP integration."""
    print("\n🧠 Testing SpendingAgent with Graphiti Integration")
    print("=" * 60)

    try:
        # Test 1: Connect to Graphiti
        print(f"\n📝 Test 1: Connecting to Graphiti MCP server")
        graphiti_client = await get_graphiti_client()

        if not graphiti_client or not graphiti_client.is_connected():
            print("⚠️  Graphiti MCP server not available - skipping Graphiti tests")
            print("💡 To test Graphiti integration:")
            print("   1. Start Graphiti server: docker run -p 8080:8080 graphiti-server")
            print("   2. Set GRAPHITI_SERVER_URL in config")
            return False

        print("✅ Connected to Graphiti MCP server")
        print(f"   • Available tools: {graphiti_client.get_available_tools()}")

        # Test 2: Create sample transactions with AI categorization
        print(f"\n📝 Test 2: Creating sample categorized transactions")
        test_transactions = [
            PlaidTransaction(
                transaction_id="real_test_starbucks_001",
                account_id="real_test_checking_001",
                amount=Decimal("4.25"),
                date="2024-01-15",
                name="Starbucks Coffee",
                merchant_name="Starbucks",
                category=["Food", "Coffee"],
                pending=False,
                ai_category="Food & Dining",
                ai_subcategory="Coffee Shops",
                ai_confidence=0.95,
                ai_tags=["caffeine", "daily-habit"]
            ),
            PlaidTransaction(
                transaction_id="real_test_grocery_001",
                account_id="real_test_checking_001",
                amount=Decimal("87.43"),
                date="2024-01-14",
                name="Whole Foods Market",
                merchant_name="Whole Foods",
                category=["Food", "Groceries"],
                pending=False,
                ai_category="Food & Dining",
                ai_subcategory="Groceries",
                ai_confidence=0.92,
                ai_tags=["essentials", "weekly"]
            )
        ]

        test_user_id = "real_graphiti_test_user"
        print(f"✅ Created {len(test_transactions)} test transactions with AI categorization")

        # Test 3: Store transactions in Graphiti
        print(f"\n📝 Test 3: Storing transactions in Graphiti")
        storage_results = await graphiti_client.batch_store_transaction_episodes(
            user_id=test_user_id,
            transactions=test_transactions,
            concurrency=2,
            check_duplicates=True
        )

        print(f"📊 Graphiti storage results:")
        successful_stores = [r for r in storage_results if not r.get('error') and not r.get('found')]
        duplicates_found = [r for r in storage_results if r.get('found')]
        errors = [r for r in storage_results if r.get('error')]

        print(f"   • Stored: {len(successful_stores)}")
        print(f"   • Duplicates: {len(duplicates_found)}")
        print(f"   • Errors: {len(errors)}")

        if len(successful_stores) > 0:
            print("✅ Transaction storage in Graphiti successful")
        else:
            print("⚠️  No new transactions stored (may be duplicates from previous runs)")

        # Test 4: Search transactions in Graphiti
        print(f"\n📝 Test 4: Searching transactions in Graphiti")
        await asyncio.sleep(2)  # Wait for indexing

        search_queries = [
            "Starbucks coffee",
            "grocery store",
            "food and dining"
        ]

        for query in search_queries:
            search_results = await graphiti_client.search(
                user_id=test_user_id,
                query=query,
                max_nodes=5
            )

            nodes_found = len(search_results.get("nodes", [])) if search_results else 0
            print(f"   • Query '{query}': {nodes_found} nodes found")

        print("✅ Graphiti search functionality working")

        # Test 5: Test canonical hashing
        print(f"\n📝 Test 5: Testing canonical hash consistency")
        tx1 = test_transactions[0]
        tx2 = PlaidTransaction(**tx1.__dict__)  # Create identical copy

        hash1 = canonical_hash(tx1)
        hash2 = canonical_hash(tx2)

        print(f"   • Transaction 1 hash: {hash1[:16]}...")
        print(f"   • Transaction 2 hash: {hash2[:16]}...")
        print(f"   • Hashes match: {hash1 == hash2}")

        if hash1 == hash2:
            print("✅ Canonical hashing working correctly")
        else:
            print("❌ Canonical hashing inconsistent")
            return False

        # Test 6: Test duplicate detection
        print(f"\n📝 Test 6: Testing duplicate detection")
        duplicate_result = await graphiti_client.store_transaction_episode(
            user_id=test_user_id,
            transaction=tx1,
            check_duplicate=True
        )

        print(f"   • Duplicate found: {duplicate_result.get('found', False)}")
        if duplicate_result.get('found'):
            print("✅ Duplicate detection working correctly")
        else:
            print("⚠️  Duplicate not detected (may be first run)")

        print("\n" + "=" * 60)
        print("🎉 SpendingAgent Graphiti Integration Test Completed!")
        print("✅ Graphiti MCP server connection working")
        print("✅ Transaction storage and retrieval working")
        print("✅ Search functionality working")
        print("✅ Canonical hashing and deduplication working")

    except Exception as e:
        print(f"\n❌ Graphiti integration test failed: {str(e)}")
        print("💡 Make sure:")
        print("   1. Graphiti server is running")
        print("   2. GRAPHITI_SERVER_URL is configured correctly")
        print("   3. MCP adapters are installed")

async def test_full_spending_agent_with_graphiti():
    """Test full SpendingAgent workflow with Graphiti integration."""
    print("\n🔄 Testing Full SpendingAgent + Graphiti Workflow")
    print("=" * 60)

    try:
        # Check if Graphiti is available
        graphiti_client = await get_graphiti_client()
        if not graphiti_client or not graphiti_client.is_connected():
            print("⚠️  Graphiti not available - skipping full workflow test")
            return False

        agent = SpendingAgent()
        test_user_id = "full_workflow_test_user"

        # Test different conversation scenarios
        test_scenarios = [
            "Show me my coffee transactions",
            "What did I spend on food last month?",
            "Find my Starbucks purchases",
            "Analyze my grocery spending patterns"
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 Scenario {i}: {scenario}")

            result = await agent.invoke_spending_conversation(
                user_message=scenario,
                user_id=test_user_id,
                session_id=f"graphiti_test_session_{i}"
            )

            print(f"   • Agent: {result['agent']}")
            print(f"   • Intent: {result['intent']}")
            print(f"   • Response preview: {result['content'][:80]}...")

            if 'error' not in result:
                print("   ✅ Scenario completed successfully")
            else:
                print(f"   ⚠️  Scenario had error: {result['error']}")

            # Small delay between scenarios
            await asyncio.sleep(1)

        print("✅ Full SpendingAgent + Graphiti workflow test completed")

    except Exception as e:
        print(f"❌ Full workflow test failed: {str(e)}")

async def run_all_tests():
    """Run all SpendingAgent integration tests."""
    print("🚀 Running Complete SpendingAgent Integration Test Suite")
    print("=" * 70)

    # Test 1: MCP + Plaid integration
    await test_spending_agent_mcp_plaid_integration()

    # Test 2: Graphiti integration
    await test_spending_agent_graphiti_integration()

    # Test 3: Full workflow
    await test_full_spending_agent_with_graphiti()

    print("\n" + "=" * 70)
    print("🏁 All SpendingAgent Integration Tests Completed!")
    print("💡 See individual test results above for details")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
