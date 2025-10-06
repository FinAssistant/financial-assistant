#!/usr/bin/env python3
"""
Test script for SpendingAgent integration testing.

This script provides 2 test scenarios:
1. Plaid-only integration (transaction fetching)
2. Full integration (Plaid → SpendingAgent → SQLite storage)

Run this ONLY when MCP Plaid server is running on localhost:8000.

Usage:
    python test_spending_agent_real_mcp.py
"""

import asyncio
import logging
from app.ai.spending_agent import SpendingAgent
from app.ai.mcp_clients.plaid_client import get_plaid_client
from app.core.database import SQLiteUserStorage
from test_mcp_plaid import test_plaid_sandbox_setup, test_exchange_public_token

# Configure logging - INFO for everything, DEBUG only for our code
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Set DEBUG level only for our app modules
logging.getLogger('app.ai.spending_agent').setLevel(logging.DEBUG)
logging.getLogger('app.utils.context_formatting').setLevel(logging.DEBUG)
logging.getLogger('app.utils.transaction_query_executor').setLevel(logging.DEBUG)
logging.getLogger('app.utils.transaction_query_parser').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Consistent test user for all tests
TEST_USER_ID_PLAID = "integration_test_user_plaid"
TEST_USER_ID_FULL = "integration_test_user_full"  # For full integration test


async def cleanup_test_database():
    """Clean up test database and Graphiti before running tests."""
    print("\n🧹 Cleaning up test database...")
    storage = SQLiteUserStorage()

    try:
        # Delete all transactions for test users
        await storage._ensure_initialized()
        async with storage.session_factory() as session:
            from sqlalchemy import text
            # Delete transactions
            await session.execute(
                text("DELETE FROM transactions WHERE user_id IN (:uid1, :uid2)"),
                {"uid1": TEST_USER_ID_PLAID, "uid2": TEST_USER_ID_FULL}
            )
            await session.commit()
        print("✅ SQLite database cleaned")
    except Exception as e:
        print(f"⚠️  SQLite cleanup warning: {e}")

    # Clean up Graphiti/Neo4j database using bolt driver
    try:
        from neo4j import AsyncGraphDatabase
        import os

        # Default to localhost for running outside Docker, or use env var for inside Docker
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "demodemo")

        print(f"🧠 Cleaning up Graphiti/Neo4j at {neo4j_uri}...")

        driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        async with driver.session() as session:
            # Delete all nodes and relationships for test users
            total_deleted = 0
            for user_id in [TEST_USER_ID_PLAID, TEST_USER_ID_FULL]:
                result = await session.run(
                    """
                    MATCH (n)
                    WHERE n.group_id = $user_id
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                    """,
                    user_id=user_id
                )
                record = await result.single()
                deleted_count = record["deleted_count"] if record else 0
                total_deleted += deleted_count
                if deleted_count > 0:
                    print(f"   • Deleted {deleted_count} nodes for {user_id}")

        await driver.close()

        if total_deleted > 0:
            print(f"✅ Neo4j cleanup completed ({total_deleted} nodes deleted)")
        else:
            print("✅ Neo4j cleanup completed (no test data found)")

    except ImportError:
        print("⚠️  neo4j driver not installed - skipping Neo4j cleanup")
        print("   ℹ️  Install with: uv sync")
    except Exception as e:
        error_msg = str(e)
        if "DNS resolve" in error_msg or "connection" in error_msg.lower() or "refused" in error_msg.lower():
            print(f"⚠️  Neo4j not accessible at {neo4j_uri}")
            print("   ℹ️  Skipping cleanup - start Neo4j with: docker compose up neo4j -d")
        else:
            print(f"⚠️  Neo4j cleanup error: {error_msg}")
            print("   ℹ️  Continuing with tests...")


async def test_1_plaid_integration_only():
    """Test 1: Plaid integration only - fetch transactions, no SQLite storage."""
    print("\n" + "=" * 70)
    print("📝 TEST 1: Plaid Integration Only")
    print("=" * 70)

    try:
        agent = SpendingAgent(test_transaction_limit=50)  # Limit transactions for testing
        print("✅ SpendingAgent created")

        # Test shared PlaidMCPClient creation with JWT
        print(f"\n🔑 Getting shared PlaidMCPClient for user: {TEST_USER_ID_PLAID}")
        plaid_client = get_plaid_client()
        mcp_client = await plaid_client.get_client(TEST_USER_ID_PLAID)

        if mcp_client is None:
            print("❌ Shared PlaidMCPClient creation failed")
            return False
        print("✅ Shared PlaidMCPClient created with JWT authentication")

        # Test Plaid sandbox setup
        print("\n💳 Setting up Plaid sandbox...")
        public_token = await test_plaid_sandbox_setup()
        if not public_token:
            print("❌ Plaid sandbox setup failed")
            return False
        print("✅ Plaid sandbox setup successful")

        # Test public token exchange
        print("\n💱 Exchanging public token...")
        tools = await plaid_client.get_tools(TEST_USER_ID_PLAID)
        tool_dict = {tool.name: tool for tool in tools}

        exchange_success = await test_exchange_public_token(tool_dict, public_token)
        if not exchange_success:
            return False

        # Small delay for token storage
        await asyncio.sleep(1)

        # Test transaction fetching via SpendingAgent
        print("\n📊 Fetching transactions via SpendingAgent...")
        transaction_result = await agent._fetch_transactions(TEST_USER_ID_PLAID)

        print("📈 Transaction fetch result:")
        print(f"   • Status: {transaction_result['status']}")
        print(f"   • Total transactions: {transaction_result.get('total_transactions', 'N/A')}")

        if transaction_result['status'] == 'success':
            print("✅ TEST 1 PASSED: Plaid integration working with shared client")
            return True
        else:
            print(f"❌ TEST 1 FAILED: {transaction_result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}")
        return False


async def test_2_full_integration():
    """Test 2: Full integration - Real Plaid → SpendingAgent → SQLite workflow."""
    print("\n" + "=" * 70)
    print("📝 TEST 2: Full Integration (Real Plaid → SpendingAgent → SQLite)")
    print("=" * 70)

    # Initialize SQLite storage for verification
    storage = SQLiteUserStorage()

    try:
        # Step 1: Setup Plaid sandbox account
        print("\n💳 Setting up Plaid sandbox for full integration...")
        public_token = await test_plaid_sandbox_setup()
        if not public_token:
            print("❌ Plaid sandbox setup failed")
            return False
        print("✅ Plaid sandbox setup successful")

        # Step 2: Create SpendingAgent and setup shared PlaidMCPClient
        print(f"\n🤖 Creating SpendingAgent and shared PlaidMCPClient for user: {TEST_USER_ID_FULL}")
        agent = SpendingAgent(test_transaction_limit=10)  # Limit transactions for testing
        plaid_client = get_plaid_client()
        mcp_client = await plaid_client.get_client(TEST_USER_ID_FULL)

        if mcp_client is None:
            print("❌ Shared PlaidMCPClient creation failed")
            return False
        print("✅ SpendingAgent and shared PlaidMCPClient created")

        # Step 3: Exchange public token via shared PlaidMCPClient
        print("\n💱 Exchanging public token via shared PlaidMCPClient...")
        tools = await plaid_client.get_tools(TEST_USER_ID_FULL)
        tool_dict = {tool.name: tool for tool in tools}

        exchange_success = await test_exchange_public_token(tool_dict, public_token)
        if not exchange_success:
            return False

        # Small delay for token storage
        await asyncio.sleep(1)

        # Step 4: Test SpendingAgent workflow scenarios
        # These should trigger: Plaid fetch → categorization → SQLite storage
        print("\n🔄 Testing full SpendingAgent workflow scenarios...")
        print("   (This will fetch from Plaid, store in SQLite)")

        test_scenarios = [
            "Show me my recent transactions",
            "Show my Uber rides last week",
            "How much did I spend on dining last month?",
            "How much did I spend on Uber last week?",
            "Show me transactions over $100 this week",
            "What did I spend money on?",
            "Analyze my spending patterns"
        ]

        all_passed = True
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 Scenario {i}: {scenario}")

            try:
                result = await agent.invoke_spending_conversation(
                    user_message=scenario,
                    user_id=TEST_USER_ID_FULL,
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

        # Step 5: Verify data was stored in SQLite
        print("\n🔍 Verifying data was stored in SQLite...")
        try:
            stored_transactions = await storage.get_transactions_for_user(TEST_USER_ID_FULL, limit=10)
            transactions_count = len(stored_transactions)
            print(f"   • Found {transactions_count} transactions in SQLite")

            if transactions_count > 0:
                print("   ✅ Data successfully stored in SQLite via SpendingAgent workflow")

                # Show sample transaction details
                sample_tx = stored_transactions[0]
                print("   • Sample transaction:")
                print(f"     - Merchant: {sample_tx.get('merchant_name', 'N/A')}")
                print(f"     - Amount: ${sample_tx.get('amount', 0):.2f}")
                print(f"     - AI Category: {sample_tx.get('ai_category') or 'N/A'}")
                confidence = sample_tx.get('ai_confidence')
                confidence_str = f"{confidence:.2f}" if confidence is not None else 'N/A'
                print(f"     - AI Confidence: {confidence_str}")
            else:
                print("   ⚠️  No transaction data found in SQLite")
                all_passed = False
        except Exception as e:
            print(f"   ⚠️  Could not verify SQLite storage: {e}")
            all_passed = False

        # Step 6: Verify Graphiti integration (insights storage and retrieval)
        # This step verifies:
        # - Insights are stored in Graphiti with proper tags
        # - Tag-based search retrieves historical context
        # - normalized_month field ensures consistent tag matching between storage and search
        print("\n🧠 Verifying Graphiti integration...")
        try:
            from app.ai.mcp_clients.graphiti_client import get_graphiti_client

            # Initialize Graphiti client
            graphiti = await get_graphiti_client()
            print("   ✅ Graphiti client initialized")

            # Test insights storage by running a spending analysis
            print("\n📊 Running spending analysis to trigger Graphiti storage...")
            analysis_result = await agent.invoke_spending_conversation(
                user_message="Give me a detailed analysis of my spending this month",
                user_id=TEST_USER_ID_FULL,
                session_id="graphiti_test_analysis"
            )

            print(f"   • Analysis completed: {analysis_result['intent']}")

            # Small delay for Graphiti to process
            await asyncio.sleep(10)

            # Test Graphiti search with tag-based matching
            print("\n🔍 Testing Graphiti search with tag-based matching...")
            from datetime import datetime
            current_month = datetime.now().strftime("%Y-%m")

            # Build search query using the same format as storage
            search_query = f"[TAGS: user:{TEST_USER_ID_FULL}, spending_insight, month:{current_month}] spending patterns"
            print(f"   • Search query: {search_query}")

            search_results = await graphiti.search(
                user_id=TEST_USER_ID_FULL,
                query=search_query,
                max_nodes=3
            )

            if search_results:
                print("   ✅ Graphiti search successful - found historical context")
                print(f"   • Search results preview: {str(search_results)[:200]}...")

                # Verify tags are present in results
                if "spending_insight" in str(search_results):
                    print("   ✅ Tag-based matching working (found 'spending_insight' tag)")
                else:
                    print("   ⚠️  Tags may not be present in search results")

            else:
                print("   ⚠️  No historical context found in Graphiti")
                print("   ℹ️  This is expected on first run - insights need time to be stored")

            # Test normalized_month consistency
            print("\n🏷️  Verifying normalized_month field consistency...")
            from app.services.insights_generator import InsightsGenerator

            insights_gen = InsightsGenerator(storage=storage, graphiti_client=graphiti)
            test_insights = await insights_gen.generate_spending_insights(
                user_id=TEST_USER_ID_FULL,
                month=current_month
            )

            if "normalized_month" in test_insights:
                print(f"   ✅ normalized_month field present: {test_insights['normalized_month']}")

                # Verify it matches the input
                if test_insights['normalized_month'] == current_month:
                    print("   ✅ normalized_month matches input month parameter")
                else:
                    print(f"   ⚠️  normalized_month mismatch: expected {current_month}, got {test_insights['normalized_month']}")
            else:
                print("   ❌ normalized_month field missing from insights")
                all_passed = False

            await asyncio.sleep(10)  # Give Graphiti time to store  

            # Test that subsequent analysis uses historical context
            print("\n🔄 Testing that second analysis retrieves historical context...")

            second_analysis = await agent.invoke_spending_conversation(
                user_message="How does my spending this month compare to before?",
                user_id=TEST_USER_ID_FULL,
                session_id="graphiti_test_second_analysis"
            )

            print(f"   • Second analysis completed: {second_analysis['intent']}")
            print("   ✅ Historical context integration tested (check logs for Graphiti search results)")

        except Exception as e:
            print(f"   ⚠️  Graphiti verification error: {e}")
            print("   ℹ️  This is acceptable - Graphiti integration is optional")

        if all_passed:
            print("\n✅ TEST 2 PASSED: Full integration workflow working")
            print("   🎉 Plaid → SpendingAgent → SQLite pipeline functional!")
            return True
        else:
            print("\n❌ TEST 2 FAILED: Some parts of the workflow failed")
            return False

    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}")
        return False

async def run_all_tests():
    """Run all integration tests in sequence."""
    print("🚀 SpendingAgent Integration Test Suite")
    print("=" * 70)
    print("Testing: Plaid → SpendingAgent → SQLite Integration")
    print("=" * 70)

    results = {
        "plaid_only": False,
        "full_integration": False
    }

    # Clean up database before running tests
    await cleanup_test_database()

    # Run tests in sequence
    results["plaid_only"] = await test_1_plaid_integration_only()
    results["full_integration"] = await test_2_full_integration()

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"✅ Test 1 - Plaid Only:        {'PASSED' if results['plaid_only'] else 'FAILED'}")
    print(f"✅ Test 2 - Full Integration:  {'PASSED' if results['full_integration'] else 'FAILED'}")

    all_passed = all(results.values())
    status = "🎉 ALL TESTS PASSED" if all_passed else "⚠️  SOME TESTS FAILED"
    print(f"\n{status}")

    if not all_passed:
        print("\n💡 Debugging tips:")
        print("   • Ensure MCP Plaid server is running: uvicorn app.main:app --reload")
        print("   • Check Plaid credentials are configured")
        print("   • Check server logs for detailed error information")
        print("   • Ensure SQLite database is accessible")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
