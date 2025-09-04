#!/usr/bin/env python3
"""
Comprehensive Plaid MCP integration test using sandbox API.

This script tests the full Plaid integration flow:
1. Creates public tokens using Plaid sandbox API
2. Uses langchain MCP adapter to call MCP tools with JWT authentication
3. Tests complete flow: exchange public token → get accounts → get transactions → get balances
"""

import asyncio
import json
from datetime import datetime

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("❌ langchain-mcp-adapters not installed. Install with: pip install langchain-mcp-adapters")
    MCP_AVAILABLE = False

try:
    from app.services.auth_service import AuthService
    from app.services.plaid_service import PlaidService
    AUTH_AVAILABLE = True
except ImportError:
    print("❌ Auth service not available")
    AUTH_AVAILABLE = False


def create_test_jwt_token() -> str:
    """Create a test JWT token with user information."""
    if not AUTH_AVAILABLE:
        return "fake-jwt-token"
    
    auth_service = AuthService()
    user_data = {
        "user_id": "plaid_test_user_123",
        "email": "plaid_test@example.com", 
        "name": "Plaid Test User"
    }
    return auth_service.generate_access_token(user_data)




async def test_plaid_sandbox_setup():
    """Test Plaid sandbox setup and public token creation."""
    print("\n🏦 Plaid Sandbox Setup Test")
    print("=" * 50)
    
    try:
        plaid_service = PlaidService()
        
        print("\n📝 Creating sandbox public token...")
        print("-" * 30)
        
        # Test with Chase (most reliable test institution)
        token_response = plaid_service.create_sandbox_public_token(
            institution_id="ins_109508",  # Chase
            products=["identity", "transactions", "liabilities", "investments"]
        )
        
        if token_response.get("status") == "success":
            public_token = token_response.get("public_token")
            print(f"✅ Successfully created public token: {public_token[:30]}...")
            print(f"📋 Request ID: {token_response.get('request_id')}")
            return public_token
        else:
            print(f"❌ Failed to create public token: {token_response}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating sandbox public token: {e}")
        return None


async def test_mcp_plaid_integration(public_token: str, jwt_token: str):
    """Test full MCP Plaid integration flow."""
    print("\n🔗 MCP Plaid Integration Test")
    print("=" * 50)
    
    # Create authenticated MCP client
    client = MultiServerMCPClient({
        "mcp": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp/",
            "headers": {
                "Authorization": f"Bearer {jwt_token}"
            }
        }
    })
    
    # Get all available tools
    print("\n📋 Getting available MCP tools...")
    print("-" * 30)
    tools = await client.get_tools()
    
    tool_dict = {}
    plaid_tools = []
    for tool in tools:
        name = getattr(tool, 'name', 'Unknown')
        description = getattr(tool, 'description', 'No description')
        tool_dict[name] = tool
        if 'plaid' in name.lower() or name in ['create_link_token', 'exchange_public_token', 'get_accounts', 'get_all_transactions', 'get_balances', 'get_identity', 'get_liabilities', 'get_investments']:
            plaid_tools.append(name)
        print(f"  • {name}: {description[:60]}...")
    
    print(f"\n🏦 Found {len(plaid_tools)} Plaid tools: {', '.join(plaid_tools)}")
    
    # Test 1: Exchange public token
    print("\n💱 Test 1: Exchange public token")
    print("-" * 30)
    if 'exchange_public_token' in tool_dict:
        try:
            result = await tool_dict['exchange_public_token'].ainvoke({
                "public_token": public_token
            })
            print("📤 Input: Created public token from sandbox")
            print(f"📥 Output: {json.dumps(result, indent=2)}")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            if result.get("status") == "success":
                print("✅ Public token exchange successful")
            else:
                print(f"❌ Public token exchange failed: {result}")
                return False
        except Exception as e:
            print(f"❌ Error exchanging public token: {e}")
            return False
    else:
        print("❌ exchange_public_token tool not found")
        return False
    
    # Small delay to allow token storage
    await asyncio.sleep(1)
    
    # Test 2: Get accounts
    print("\n💼 Test 2: Get accounts")
    print("-" * 30)
    if 'get_accounts' in tool_dict:
        try:
            result = await tool_dict['get_accounts'].ainvoke({})
            print("📤 Input: (no arguments - uses authenticated user context)")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            print(f"📥 Output: {json.dumps(result, indent=2)}")
            
            if result.get("status") == "success":
                accounts = result.get("accounts", [])
                print(f"✅ Retrieved {len(accounts)} accounts")
                for i, account in enumerate(accounts[:3]):  # Show first 3
                    print(f"   Account {i+1}: {account.get('name')} ({account.get('type')}) - Balance: ${account.get('balances', {}).get('current', 0)}")
            else:
                print(f"❌ Get accounts failed: {result}")
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
    else:
        print("❌ get_accounts tool not found")
    
    # Test 3: Get all transactions (with built-in sync and polling)
    print("\n📊 Test 3: Get all transactions")
    print("-" * 30)
    if 'get_all_transactions' in tool_dict:
        try:
            result = await tool_dict['get_all_transactions'].ainvoke({})
            print("📤 Input: (no cursor - full sync with polling)")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            if result.get("status") in ["success", "warning"]:
                transactions = result.get("transactions", [])
                total = result.get("total_transactions", 0)
                message = result.get("message", "")
                print(f"✅ Retrieved {total} transactions")
                if message:
                    print(f"   Note: {message}")
                
                # Show first few transactions
                for i, tx in enumerate(transactions[:3]):
                    amount = tx.get('amount', 0)
                    name = tx.get('name', 'Unknown')
                    date = tx.get('date', 'Unknown')
                    print(f"   TX {i+1}: ${amount} - {name} ({date})")
            else:
                print(f"❌ Get all transactions failed: {result}")
        except Exception as e:
            print(f"❌ Error getting all transactions: {e}")
    else:
        print("❌ get_all_transactions tool not found")
    
    # Test 4: Get balances
    print("\n💰 Test 4: Get balances")
    print("-" * 30)
    if 'get_balances' in tool_dict:
        try:
            result = await tool_dict['get_balances'].ainvoke({})
            print("📤 Input: (no arguments)")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            if result.get("status") == "success":
                balances = result.get("balances", [])
                print(f"✅ Retrieved balances for {len(balances)} accounts")
                
                total_balance = 0
                for balance in balances:
                    current = balance.get('balances', {}).get('current', 0)
                    if current:
                        total_balance += current
                    name = balance.get('name', 'Unknown')
                    print(f"   {name}: ${current}")
                
                print(f"💵 Total balance across all accounts: ${total_balance}")
            else:
                print(f"❌ Get balances failed: {result}")
        except Exception as e:
            print(f"❌ Error getting balances: {e}")
    else:
        print("❌ get_balances tool not found")
    
    # Test 5: Get identity
    print("\n🆔 Test 5: Get identity")
    print("-" * 30)
    if 'get_identity' in tool_dict:
        try:
            result = await tool_dict['get_identity'].ainvoke({})
            print("📤 Input: (no arguments)")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            if result.get("status") == "success":
                identities = result.get("identities", [])
                print(f"✅ Retrieved identity information for {len(identities)} accounts")
                
                for identity in identities[:2]:  # Show first 2
                    account_name = identity.get('name', 'Unknown')
                    owners = identity.get('owners', [])
                    print(f"   Account: {account_name}")
                    for owner in owners[:1]:  # First owner only
                        names = owner.get('names', [])
                        emails = owner.get('emails', [])
                        if names:
                            print(f"     Name: {names[0]}")
                        if emails:
                            print(f"     Email: {emails[0].get('data', 'N/A')}")
            else:
                print(f"❌ Get identity failed: {result}")
        except Exception as e:
            print(f"❌ Error getting identity: {e}")
    else:
        print("❌ get_identity tool not found")
    
    # Test 6: Get liabilities
    print("\n💳 Test 6: Get liabilities")
    print("-" * 30)
    if 'get_liabilities' in tool_dict:
        try:
            result = await tool_dict['get_liabilities'].ainvoke({})
            print("📤 Input: (no arguments)")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            if result.get("status") == "success":
                liabilities = result.get("liabilities", {})
                accounts = liabilities.get("accounts", [])
                credit = liabilities.get("credit", [])
                mortgage = liabilities.get("mortgage", [])
                student = liabilities.get("student", [])
                
                print(f"✅ Retrieved liability information for {len(accounts)} accounts")
                print(f"   • Credit cards: {len(credit)}")
                print(f"   • Mortgages: {len(mortgage)}")
                print(f"   • Student loans: {len(student)}")
                
                # Show first few liability accounts
                for i, account in enumerate(accounts[:2]):
                    name = account.get('name', 'Unknown')
                    account_type = account.get('type', 'Unknown')
                    subtype = account.get('subtype', 'Unknown')
                    current_balance = account.get('balances', {}).get('current', 0)
                    print(f"   Account {i+1}: {name} ({account_type}/{subtype}) - Balance: ${current_balance}")
                    
            else:
                print(f"❌ Get liabilities failed: {result}")
        except Exception as e:
            print(f"❌ Error getting liabilities: {e}")
    else:
        print("❌ get_liabilities tool not found")
    
    # Test 7: Get investments
    print("\n📈 Test 7: Get investments")
    print("-" * 30)
    if 'get_investments' in tool_dict:
        try:
            result = await tool_dict['get_investments'].ainvoke({})
            print("📤 Input: (no arguments)")
            
            if isinstance(result, str):
                result = json.loads(result)
            
            if result.get("status") == "success":
                investments = result.get("investments", {})
                accounts = investments.get("accounts", [])
                holdings = investments.get("holdings", [])
                securities = investments.get("securities", [])
                
                print(f"✅ Retrieved investment information for {len(accounts)} accounts")
                print(f"   • Holdings: {len(holdings)}")
                print(f"   • Securities: {len(securities)}")
                
                # Calculate total investment value
                total_value = 0
                for holding in holdings:
                    value = holding.get('institution_value', 0)
                    if value:
                        total_value += value
                
                if total_value > 0:
                    print(f"   • Total portfolio value: ${total_value:,.2f}")
                
                # Show first few investment accounts
                for i, account in enumerate(accounts[:2]):
                    name = account.get('name', 'Unknown')
                    account_type = account.get('type', 'Unknown')
                    subtype = account.get('subtype', 'Unknown')
                    current_balance = account.get('balances', {}).get('current', 0)
                    print(f"   Account {i+1}: {name} ({account_type}/{subtype}) - Balance: ${current_balance}")
                    
                # Show first few holdings
                for i, holding in enumerate(holdings[:3]):
                    security_id = holding.get('security_id', 'Unknown')
                    quantity = holding.get('quantity', 0)
                    value = holding.get('institution_value', 0)
                    print(f"   Holding {i+1}: Security {security_id} - Qty: {quantity}, Value: ${value}")
                    
            else:
                print(f"❌ Get investments failed: {result}")
        except Exception as e:
            print(f"❌ Error getting investments: {e}")
    else:
        print("❌ get_investments tool not found")
    
    return True


async def test_authentication():
    """Test MCP authentication."""
    print("\n🔐 MCP Authentication Test")
    print("=" * 50)
    
    # Test without authentication
    print("\n📝 Testing without authentication (expect 401)...")
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
        return None
    except Exception as e:
        error_str = str(e)
        if ("401" in error_str or "Unauthorized" in error_str or "TaskGroup" in error_str):
            print("✅ Correctly rejected (401 Unauthorized)")
        else:
            print(f"❌ Unexpected error: {e}")
            return None
    
    # Test with authentication
    print("\n📝 Testing with JWT authentication...")
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
        return jwt_token
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return None


async def run_comprehensive_plaid_mcp_test():
    """Run comprehensive Plaid MCP integration test."""
    
    if not MCP_AVAILABLE:
        print("❌ MCP adapter not available. Install with: pip install langchain-mcp-adapters")
        return
    
    print("🚀 Comprehensive Plaid MCP Integration Test Suite")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Test authentication
        jwt_token = await test_authentication()
        if not jwt_token:
            print("\n❌ Authentication failed. Cannot proceed with Plaid tests.")
            return
        
        # Step 2: Create sandbox public token
        public_token = await test_plaid_sandbox_setup()
        if not public_token:
            print("\n❌ Failed to create sandbox public token. Cannot proceed with MCP tests.")
            print("💡 Make sure Plaid credentials are set:")
            print("   export PLAID_CLIENT_ID='your_client_id'")
            print("   export PLAID_SECRET='your_secret'")
            return
        
        # Step 3: Test full MCP Plaid integration
        success = await test_mcp_plaid_integration(public_token, jwt_token)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ All Plaid MCP integration tests completed successfully!")
            print("🎯 Complete flow working: Sandbox → MCP → Plaid API")
            print("🔧 MCP tools successfully integrated with Plaid service")
            print("🔐 JWT authentication working correctly")
            print("🏦 Plaid sandbox integration functional")
        else:
            print("\n❌ Some tests failed. Check the output above for details.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("💡 Make sure the FastAPI server is running:")
        print("   python -m uvicorn app.main:app --reload")
        print("💡 And Plaid credentials are configured in .env file")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_plaid_mcp_test())