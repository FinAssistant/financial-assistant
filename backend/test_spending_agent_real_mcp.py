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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Consistent test user for all tests
TEST_USER_ID_PLAID = "integration_test_user_plaid"
TEST_USER_ID_FULL = "integration_test_user_full"  # For full integration test


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
        agent = SpendingAgent(test_transaction_limit=5)  # Limit transactions for testing
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
                print(f"     - AI Category: {sample_tx.get('ai_category', 'N/A')}")
                print(f"     - AI Confidence: {sample_tx.get('ai_confidence', 0):.2f}")
            else:
                print("   ⚠️  No transaction data found in SQLite")
                all_passed = False
        except Exception as e:
            print(f"   ⚠️  Could not verify SQLite storage: {e}")
            all_passed = False

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
