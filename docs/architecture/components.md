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
**Responsibility**: LangGraph orchestration with agentic routing, conversation state management, and AI response generation

**Key Interfaces**:
- POST /api/conversation/send - Send message to AI (routes through Orchestrator Agent)
- GET /api/conversation/history/{session_id} - Retrieve conversation history
- POST /api/conversation/onboarding - Direct onboarding agent access
- POST /api/conversation/spending - Direct spending agent access

**Agent Architecture**:
```python
# Single LangGraph with multiple agent subgraphs
class FinancialAssistantGraph:
    agents = {
        "orchestrator": OrchestratorAgent,
        "onboarding": OnboardingAgent, 
        "spending": SpendingAgent
    }
    
    shared_state = GlobalState  # Shared across all agents
    mcp_client = FinancialMCPClient  # Centralized tool access
```

**Dependencies**: LangGraph multi-agent, MCP client, LLM provider APIs, conversation storage
**Technology Stack**: LangGraph subgraphs, MCP Python SDK, OpenAI/Claude APIs via environment configuration

### MCP Server Service
**Responsibility**: Model Context Protocol server providing centralized tool access for AI agents

**Key Interfaces**:
- Tool: plaid_get_link_token - Generate Plaid Link token
- Tool: plaid_exchange_token - Exchange public token for access token  
- Tool: plaid_get_accounts - Retrieve connected accounts with fresh data
- Tool: plaid_get_transactions - Fetch transactions on-demand
- Tool: plaid_categorize_transactions - AI-powered transaction categorization with user feedback learning
- Tool: plaid_analyze_spending_patterns - Identify recurring expenses, seasonal trends, and anomalies
- Tool: plaid_detect_subscription_services - Find duplicate and unused recurring payments
- Tool: graphiti_store_context - Store user context in graph database
- Tool: graphiti_query_relationships - Query user financial relationships
- Tool: graphiti_store_conversation - Store conversation context
- Tool: graphiti_store_personality_profile - Store spending personality insights and risk tolerance
- Tool: graphiti_query_spending_behaviors - Query historical spending patterns and triggers
- Tool: budget_manage_categories - Create, update, and track category-wise budget limits
- Tool: budget_generate_alerts - Create real-time budget variance notifications
- Tool: optimization_suggest_cost_reductions - Generate personality-tailored expense reduction strategies
- Tool: optimization_analyze_cash_flow - Forecast trends and identify surplus allocation opportunities

**MCP Architecture**:
```python
class FinancialMCPServer:
    tools = {
        # Plaid Integration Tools
        "plaid_get_link_token": PlaidLinkTokenTool,
        "plaid_exchange_token": PlaidExchangeTool,
        "plaid_get_accounts": PlaidAccountsTool,
        "plaid_get_transactions": PlaidTransactionsTool,
        "plaid_categorize_transactions": PlaidCategorizationTool,
        "plaid_analyze_spending_patterns": PlaidPatternAnalysisTool,
        "plaid_detect_subscription_services": PlaidSubscriptionDetectionTool,
        
        # Graphiti Context & Personality Tools
        "graphiti_store_context": GraphitiStoreTool,
        "graphiti_query_relationships": GraphitiQueryTool,
        "graphiti_store_conversation": GraphitiConversationTool,
        "graphiti_store_personality_profile": GraphitiPersonalityTool,
        "graphiti_query_spending_behaviors": GraphitiBehaviorQueryTool,
        
        # Budget Management Tools
        "budget_manage_categories": BudgetManagementTool,
        "budget_generate_alerts": BudgetAlertTool,
        
        # Optimization & Analysis Tools
        "optimization_suggest_cost_reductions": CostOptimizationTool,
        "optimization_analyze_cash_flow": CashFlowAnalysisTool
    }
```

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
**Responsibility**: Comprehensive financial analysis including transaction categorization, personality profiling, budget management, and optimization recommendations

**Key Interfaces**:
- POST /api/analysis/categorize-transactions - AI-powered transaction categorization with user feedback learning
- GET /api/analysis/cash-flow/{user_id} - Generate cash flow analysis with trend detection and forecasting
- POST /api/analysis/onboarding-profile - Generate initial financial profile with personality assessment
- GET /api/analysis/spending-patterns/{user_id} - Comprehensive spending pattern analysis with behavioral insights
- POST /api/analysis/personality-profile - Generate spending personality profile (Saver, Spender, Planner, etc.)
- GET /api/analysis/anomaly-detection/{user_id} - Detect unusual transactions and spending spikes
- POST /api/analysis/budget-recommendations - Generate intelligent budget suggestions based on history and personality
- GET /api/analysis/optimization-opportunities/{user_id} - Identify cost reduction and efficiency improvements
- POST /api/analysis/subscription-analysis - Analyze recurring payments for duplicates and unused services
- GET /api/analysis/goal-alignment/{user_id} - Compare spending habits against stated financial objectives

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
        
        # Store insights in Graphiti, not raw transactions
        await self.graphiti.store_spending_insights(user_id, all_categorized)
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
**Responsibility**: Advanced spending visualization, interactive analytics, and personalized financial insights display

**Key Interfaces**:
- AccountCard for individual account display with real-time balance updates
- TransactionList with AI-powered categorization and natural language search
- SpendingPatternChart with drill-down capabilities and trend analysis
- PersonalityProfileDisplay showing spending type and behavioral insights
- BudgetTracker with real-time progress indicators and variance alerts
- OptimizationRecommendations displaying personality-tailored cost reduction strategies
- SubscriptionAnalyzer showing recurring payments with optimization suggestions
- CashFlowForecast with trend detection and surplus allocation recommendations
- InteractiveReports with conversational query interface
- BudgetSetupWizard with guided category selection and limit setting

**Advanced Visualization Features**:
- Interactive spending charts with multi-dimensional filtering
- Personality-aware communication adapting tone to user profile
- Real-time budget alerts with contextual explanations
- Anomaly detection visualizations with spending spike highlights
- Goal alignment progress displays comparing habits to objectives

**Dependencies**: Redux state, advanced charting libraries (D3.js/Chart.js), AI-SDK for conversational queries
**Technology Stack**: React components with styled-components, D3.js for interactive charts, Recharts for standard visualizations

## Agent Communication Patterns

### Global State Management
**Responsibility**: Shared state across all agent subgraphs in single LangGraph process

```python
class GlobalState(BaseModel):
    # User Context
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    
    # Current Request Processing
    user_message: str
    current_intent: Optional[str] = None
    active_agent: Optional[str] = None
    
    # Shared Financial Data
    user_profile: Optional[Dict[str, Any]] = None
    connected_accounts: List[Dict[str, Any]] = []
    
    # Agent Coordination
    agent_handoff_context: Optional[Dict[str, Any]] = None
    
    # Response Building
    response_chunks: List[str] = []
    final_response: Optional[str] = None
    
    # MCP Tool Results (shared across agents)
    mcp_tool_results: Dict[str, Any] = {}
```

### Agent Subgraph Patterns
**LLM Orchestrator Agent**: Uses LLM for intelligent routing decisions based on user intent, conversation context, and available data
- Analyzes user messages with conversation history and user profile context
- Makes routing decisions with confidence scoring and reasoning
- Handles simple queries directly or routes to specialized agents
- Manages conversation flow and context switches

**Specialized Agents**: Domain-focused processing (Onboarding, Spending) with access to shared state and MCP tools
- Onboarding Agent: Account setup, goal setting, initial financial profiling
- Spending Agent: Expense analysis, budgeting, cash flow recommendations

**Error Handling**: Graceful degradation with fallback to orchestrator for failed agent operations

**LLM Routing Examples**:
```python
# High confidence routing
"Connect my bank account" → onboarding (0.95 confidence)
"Where do I spend too much?" → spending (0.9 confidence)
"What is compound interest?" → orchestrator direct response (0.85 confidence)

# Context-aware routing  
"How much should I save?" + user_has_accounts → spending (0.75 confidence)
"Can you help with money stuff?" → orchestrator clarification (0.6 confidence)
```

### MCP Integration Pattern
All agents access external tools through standardized MCP interface:
- Single MCP client shared across agent subgraphs
- Tool results cached in global state for cross-agent access
- Simple error handling with graceful degradation for MVP
