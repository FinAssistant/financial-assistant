#!/usr/bin/env python3
"""
Test script for SpendingAgent integration testing.

This script provides 3 separate test scenarios:
1. Plaid-only integration (transaction fetching)
2. Graphiti-only integration (mock data storage and retrieval)
3. Full integration (Plaid → Graphiti → SpendingAgent analysis)

Run this ONLY when MCP servers are running on localhost:8000 and localhost:8080.

Usage:
    python test_spending_agent_real_mcp.py
"""

import asyncio
import logging
from decimal import Decimal
from app.ai.spending_agent import SpendingAgent
from app.ai.mcp_clients.graphiti_client import get_graphiti_client
from app.models.plaid_models import PlaidTransaction
from test_mcp_plaid import test_plaid_sandbox_setup, test_exchange_public_token

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Consistent test user for all tests
TEST_USER_ID = "integration_test_user"

async def get_connected_graphiti_client():
    """Get connected Graphiti client or None if unavailable."""
    try:
        graphiti_client = await get_graphiti_client()
        if graphiti_client and graphiti_client.is_connected():
            return graphiti_client
    except Exception as e:
        print(f"⚠️  Graphiti connection error: {e}")
    return None

async def clear_graphiti_data():
    """Clear test data from Graphiti before each test."""
    graphiti_client = await get_connected_graphiti_client()
    if graphiti_client:
        try:
            clear_tool = graphiti_client._get_tool("clear_graph")
            await clear_tool.ainvoke({})
            print("🧹 Cleared Graphiti test data")
            return True
        except Exception as e:
            print(f"⚠️  Could not clear Graphiti data: {e}")
    return False

async def store_mock_transactions_in_graphiti(graphiti_client, user_id, transactions, show_results=True):
    """Store mock transactions in Graphiti and optionally show results."""
    storage_results = await graphiti_client.batch_store_transaction_episodes(
        user_id=user_id,
        transactions=transactions,
        concurrency=2,
        check_duplicates=True
    )

    if show_results:
        successful_stores = [r for r in storage_results if not r.get('error') and not r.get('found')]
        duplicates = [r for r in storage_results if r.get('found')]
        errors = [r for r in storage_results if r.get('error')]

        print(f"📊 Storage results:")
        print(f"   • Stored: {len(successful_stores)}")
        print(f"   • Duplicates: {len(duplicates)}")
        print(f"   • Errors: {len(errors)}")

        return len(errors) == 0
    return True

def create_mock_transactions():
    """Create consistent mock transactions for testing."""
    return [
        PlaidTransaction(
            transaction_id="test_starbucks_001",
            account_id="test_checking_001",
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
            transaction_id="test_grocery_001",
            account_id="test_checking_001",
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
        ),
        PlaidTransaction(
            transaction_id="test_gas_001",
            account_id="test_checking_001",
            amount=Decimal("45.80"),
            date="2024-01-13",
            name="Shell Gas Station",
            merchant_name="Shell",
            category=["Transportation", "Gas"],
            pending=False,
            ai_category="Transportation",
            ai_subcategory="Gas Stations",
            ai_confidence=0.98,
            ai_tags=["essential", "commute"]
        )
    ]

async def test_1_plaid_integration_only():
    """Test 1: Plaid integration only - fetch transactions, no Graphiti storage."""
    print("\n" + "=" * 70)
    print("📝 TEST 1: Plaid Integration Only")
    print("=" * 70)

    try:
        agent = SpendingAgent(test_transaction_limit=50)  # Limit transactions for testing
        print("✅ SpendingAgent created")

        # Test MCP client creation with JWT
        print(f"\n🔑 Creating MCP client for user: {TEST_USER_ID}")
        mcp_client = await agent._get_mcp_client(TEST_USER_ID)

        if mcp_client is None:
            print("❌ MCP client creation failed")
            return False
        print("✅ MCP client created with JWT authentication")

        # Test Plaid sandbox setup
        print("\n💳 Setting up Plaid sandbox...")
        public_token = await test_plaid_sandbox_setup()
        if not public_token:
            print("❌ Plaid sandbox setup failed")
            return False
        print("✅ Plaid sandbox setup successful")

        # Test public token exchange
        print("\n💱 Exchanging public token...")
        tools = await mcp_client.get_tools()
        tool_dict = {tool.name: tool for tool in tools}

        exchange_success = await test_exchange_public_token(tool_dict, public_token)
        if not exchange_success:
            print("❌ Public token exchange failed")
            return False
        print("✅ Public token exchange successful")

        # Small delay for token storage
        await asyncio.sleep(1)

        # Test transaction fetching
        print("\n📊 Fetching transactions...")
        transaction_result = await agent._fetch_transactions(TEST_USER_ID)

        print(f"📈 Transaction fetch result:")
        print(f"   • Status: {transaction_result['status']}")
        print(f"   • Total transactions: {transaction_result.get('total_transactions', 'N/A')}")

        if transaction_result['status'] == 'success':
            print("✅ TEST 1 PASSED: Plaid integration working")
            return True
        else:
            print(f"❌ TEST 1 FAILED: {transaction_result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}")
        return False

async def test_2_graphiti_integration_only():
    """Test 2: Graphiti integration only - store and retrieve mock transactions."""
    print("\n" + "=" * 70)
    print("📝 TEST 2: Graphiti Integration Only")
    print("=" * 70)

    # Clear data before test
    await clear_graphiti_data()

    try:
        # Test Graphiti connection
        print("\n🧠 Connecting to Graphiti...")
        graphiti_client = await get_connected_graphiti_client()

        if not graphiti_client:
            print("❌ Graphiti connection failed")
            return False
        print("✅ Graphiti connection successful")
        print(f"   • Available tools: {graphiti_client.get_available_tools()}")

        # Create mock transactions
        print("\n📦 Creating mock transactions...")
        mock_transactions = create_mock_transactions()
        print(f"✅ Created {len(mock_transactions)} mock transactions")

        # Store transactions in Graphiti
        print("\n💾 Storing transactions in Graphiti...")
        storage_success = await store_mock_transactions_in_graphiti(
            graphiti_client, TEST_USER_ID, mock_transactions, show_results=True
        )

        if not storage_success:
            print("❌ TEST 2 FAILED: Storage errors occurred")
            return False

        # Test search functionality
        print("\n🔍 Testing search functionality...")
        search_queries = ["coffee", "Starbucks", "food", "grocery"]

        for query in search_queries:
            search_results = await graphiti_client.search(
                user_id=TEST_USER_ID,
                query=query,
                max_nodes=10
            )
            nodes_found = len(search_results.get("nodes", [])) if search_results else 0
            print(f"   • Query '{query}': {nodes_found} nodes found")

        print("✅ TEST 2 PASSED: Graphiti integration working")
        return True

    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}")
        return False

async def test_3_full_integration():
    """Test 3: Full integration - Real Plaid → SpendingAgent → Graphiti workflow."""
    print("\n" + "=" * 70)
    print("📝 TEST 3: Full Integration (Real Plaid → SpendingAgent → Graphiti)")
    print("=" * 70)

    # Clear data before test for clean slate
    await clear_graphiti_data()

    try:
        # Step 1: Setup Plaid sandbox account
        print("\n💳 Setting up Plaid sandbox for full integration...")
        public_token = await test_plaid_sandbox_setup()
        if not public_token:
            print("❌ Plaid sandbox setup failed")
            return False
        print("✅ Plaid sandbox setup successful")

        # Step 2: Create SpendingAgent and setup MCP client
        print(f"\n🤖 Creating SpendingAgent and MCP client for user: {TEST_USER_ID}")
        agent = SpendingAgent(test_transaction_limit=5)  # Limit transactions for testing
        mcp_client = await agent._get_mcp_client(TEST_USER_ID)

        if mcp_client is None:
            print("❌ MCP client creation failed")
            return False
        print("✅ SpendingAgent and MCP client created")

        # Step 3: Exchange public token via MCP
        print("\n💱 Exchanging public token via MCP...")
        tools = await mcp_client.get_tools()
        tool_dict = {tool.name: tool for tool in tools}

        exchange_success = await test_exchange_public_token(tool_dict, public_token)
        if not exchange_success:
            return False

        # Small delay for token storage
        await asyncio.sleep(1)

        # Step 4: Test SpendingAgent workflow scenarios
        # These should trigger: Plaid fetch → categorization → Graphiti storage → analysis
        print("\n🔄 Testing full SpendingAgent workflow scenarios...")
        print("   (This will fetch from Plaid, store in Graphiti, and analyze)")

        test_scenarios = [
            "Show me my recent transactions",
            "What did I spend money on?",
            "Analyze my spending patterns"
        ]

        all_passed = True
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 Scenario {i}: {scenario}")

            try:
                result = await agent.invoke_spending_conversation(
                    user_message=scenario,
                    user_id=TEST_USER_ID,
                    session_id=f"full_integration_test_{i}"
                )

                print(f"   • Agent: {result['agent']}")
                print(f"   • Intent: {result['intent']}")
                print(f"   • Response preview: {result['content']}...")

                if 'error' not in result:
                    print("   ✅ Scenario completed successfully")
                else:
                    print(f"   ❌ Scenario failed: {result['error']}")
                    all_passed = False

            except Exception as e:
                print(f"   ❌ Scenario failed with exception: {str(e)}")
                all_passed = False

            # Small delay between scenarios
            await asyncio.sleep(2)

        # Step 5: Verify data was stored in Graphiti
        print("\n🔍 Verifying data was stored in Graphiti...")
        graphiti_client = await get_connected_graphiti_client()
        if graphiti_client:
            search_results = await graphiti_client.search(
                user_id=TEST_USER_ID,
                query="transaction",
                max_nodes=5
            )
            nodes_found = len(search_results.get("nodes", [])) if search_results else 0
            print(f"   • Found {nodes_found} transaction-related nodes in Graphiti")

            if nodes_found > 0:
                print("   ✅ Data successfully stored in Graphiti via SpendingAgent workflow")
            else:
                print("   ⚠️  No transaction data found in Graphiti")
                all_passed = False
        else:
            print("   ⚠️  Could not verify Graphiti storage")

        if all_passed:
            print("\n✅ TEST 3 PASSED: Full integration workflow working")
            print("   🎉 Plaid → SpendingAgent → Graphiti pipeline functional!")
            return True
        else:
            print("\n❌ TEST 3 FAILED: Some parts of the workflow failed")
            return False

    except Exception as e:
        print(f"❌ TEST 3 FAILED: {str(e)}")
        return False

async def run_all_tests():
    """Run all integration tests in sequence."""
    print("🚀 SpendingAgent Integration Test Suite")
    print("=" * 70)
    print("Testing: Plaid → Graphiti → SpendingAgent Integration")
    print("=" * 70)

    results = {
        "plaid_only": False,
        "graphiti_only": False,
        "full_integration": False
    }

    # Run tests in sequence
    # results["plaid_only"] = await test_1_plaid_integration_only()
    # results["graphiti_only"] = await test_2_graphiti_integration_only()
    results["full_integration"] = await test_3_full_integration()

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"✅ Test 1 - Plaid Only:        {'PASSED' if results['plaid_only'] else 'FAILED'}")
    print(f"✅ Test 2 - Graphiti Only:     {'PASSED' if results['graphiti_only'] else 'FAILED'}")
    print(f"✅ Test 3 - Full Integration:  {'PASSED' if results['full_integration'] else 'FAILED'}")

    all_passed = all(results.values())
    status = "🎉 ALL TESTS PASSED" if all_passed else "⚠️  SOME TESTS FAILED"
    print(f"\n{status}")

    if not all_passed:
        print("\n💡 Debugging tips:")
        print("   • Ensure MCP server is running: uvicorn app.main:app --reload")
        print("   • Ensure Graphiti server is running on localhost:8080")
        print("   • Check Plaid credentials are configured")
        print("   • Check server logs for detailed error information")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
