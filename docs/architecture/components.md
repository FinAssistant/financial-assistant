# Components

## Backend Components

### Authentication Service
**Responsibility**: Google OAuth integration, JWT token management, and user session handling

**Key Interfaces**:
- POST /auth/google - Google OAuth callback
- POST /auth/refresh - JWT token refresh
- POST /auth/logout - Session termination

**Dependencies**: Google OAuth client, JWT library
**Technology Stack**: FastAPI OAuth2, python-jose for JWT

### AI Conversation Service  
**Responsibility**: LangGraph orchestration, conversation state management, and AI response generation

**Key Interfaces**:
- POST /api/conversation/send - Send message to AI
- GET /api/conversation/history/{session_id} - Retrieve conversation history
- POST /api/conversation/onboarding - Onboarding-specific AI interactions

**Dependencies**: LangGraph, LLM provider APIs, conversation storage
**Technology Stack**: LangGraph, OpenAI/Claude APIs via environment configuration

### Plaid Integration Service
**Responsibility**: Plaid API integration with periodic data synchronization and minimal transaction storage

**Key Interfaces**:
- POST /api/plaid/link-token - Generate Plaid Link token
- POST /api/plaid/exchange - Exchange public token for access token  
- GET /api/plaid/accounts - Retrieve connected accounts with fresh data
- GET /api/plaid/transactions/{account_id} - Fetch transactions on-demand
- POST /api/plaid/sync - Manual sync trigger for development

**Periodic Sync Strategy**:
```python
import asyncio
from datetime import datetime, timedelta

class PlaidSyncService:
    def __init__(self):
        self.sync_interval = 3600  # 1 hour for POC
        
    async def start_periodic_sync(self):
        """Background task for periodic data synchronization"""
        while True:
            await self.sync_all_accounts()
            await asyncio.sleep(self.sync_interval)
    
    async def sync_all_accounts(self):
        """Sync all active accounts and update balances"""
        for account in self.get_active_accounts():
            fresh_data = await self.plaid_client.get_account_data(account.plaid_access_token)
            account.balance = fresh_data.balance
            account.last_synced = datetime.now()
            # Don't store transactions, fetch on-demand
```

**Dependencies**: Plaid Python client, secure token storage
**Technology Stack**: Plaid Python SDK, encrypted token storage

### Financial Analysis Service
**Responsibility**: Real-time transaction categorization and cash flow analysis without persistent transaction storage

**Key Interfaces**:
- POST /api/analysis/categorize-transactions - Categorize transactions on-demand
- GET /api/analysis/cash-flow/{user_id} - Generate cash flow from live Plaid data
- POST /api/analysis/onboarding-profile - Generate initial financial profile
- GET /api/analysis/spending-patterns/{user_id} - Analyze spending without storing transactions

**Automatic Categorization Flow**:
```python
class FinancialAnalysisService:
    async def categorize_user_transactions(self, user_id: str) -> Dict[str, Any]:
        """Categorize transactions during onboarding or periodic sync"""
        accounts = self.get_user_accounts(user_id)
        all_categorized = []
        
        for account in accounts:
            # Fetch fresh transactions from Plaid
            transactions = await self.plaid_service.get_transactions(account.id)
            
            # Auto-categorize using simple rules + LLM for unclear cases
            categorized = await self.auto_categorize_transactions(transactions)
            all_categorized.extend(categorized)
        
        # Generate insights without storing transactions
        return self.generate_spending_insights(all_categorized)
    
    async def auto_categorize_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """Automatic categorization using rules + LLM fallback"""
        for transaction in transactions:
            # First: Rule-based categorization
            category = self.rule_based_categorize(transaction.description)
            
            if not category:
                # Fallback: LLM categorization for unclear transactions
                category = await self.llm_categorize(transaction.description)
            
            transaction.category = category
            transaction.auto_categorized = True
            
        return transactions
```

**Dependencies**: Transaction data, user profile data
**Technology Stack**: Python data processing, basic ML for categorization

## Frontend Components

### Redux Store Architecture
**Responsibility**: Centralized state management for authentication, onboarding, and financial data

**Key Interfaces**:
- authSlice - User authentication state
- onboardingSlice - Wizard progress and data
- accountsSlice - Financial accounts and transactions
- uiSlice - Application UI state

**Dependencies**: Redux Toolkit, Redux Persist
**Technology Stack**: RTK with RTK Query for API integration

### AI Conversation Interface  
**Responsibility**: Real-time chat interface with AI using streaming responses

**Key Interfaces**:
- useChat hook for conversation management
- Message display with typing indicators
- User input with smart suggestions

**Dependencies**: AI-SDK, Redux for state integration
**Technology Stack**: AI-SDK React hooks, styled-components

### Plaid Link Component
**Responsibility**: Secure bank account connection interface using Plaid Link

**Key Interfaces**:
- PlaidLink wrapper component
- Account connection status display
- Error handling and retry logic

**Dependencies**: react-plaid-link, RTK Query for API calls
**Technology Stack**: Plaid React SDK, Redux state management

### Financial Dashboard Components
**Responsibility**: Account overview, transaction display, and goal progress visualization

**Key Interfaces**:
- AccountCard for individual account display
- TransactionList with categorization
- GoalProgress indicators
- SpendingChart visualization

**Dependencies**: Redux state, chart libraries
**Technology Stack**: React components with styled-components, chart libraries TBD
