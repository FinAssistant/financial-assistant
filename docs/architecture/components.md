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
- Tool: graphiti_store_context - Store user context in graph database
- Tool: graphiti_query_relationships - Query user financial relationships

**MCP Architecture**:
```python
class FinancialMCPServer:
    tools = {
        # Plaid Integration Tools (External API Access)
        "plaid_get_link_token": PlaidLinkTokenTool,
        "plaid_exchange_token": PlaidExchangeTool,
        "plaid_get_accounts": PlaidAccountsTool,
        "plaid_get_transactions": PlaidTransactionsTool,
        
        # Graphiti General-Purpose Tools
        "graphiti_store_context": GraphitiStoreTool,
        "graphiti_query_relationships": GraphitiQueryTool,
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
**Responsibility**: Minimal dashboard for account overview with conversational-first approach

**Key Interfaces**:
- AccountCard for basic account display with current balances
- TransactionList for simple transaction history viewing
- ChatInterface for AI-powered financial insights and analysis

**Design Approach**:
- Conversational-first: Users get insights through AI chat, not complex visualizations
- Minimal UI: Essential account and transaction data only
- Analysis via conversation: Spending patterns, personality insights, and recommendations delivered through AI conversation

**Dependencies**: Redux state, basic UI components, AI-SDK for conversational interface
**Technology Stack**: React components with styled-components, minimal charting for basic summaries

## Agent Communication Patterns

### Global State Management
**Responsibility**: Shared state across all agent subgraphs in single LangGraph process following LangGraph best practices

```python
class GlobalState(BaseModel):
    # Messages (LangGraph standard pattern with automatic management)
    messages: Annotated[list[AnyMessage], add_messages]
    
    # Shared Data (lazy-loaded when needed)
    connected_accounts: Optional[List[Dict[str, Any]]] = None  # Basic account info only
    profile_context: Optional[str] = None  # Cached user profile context string for LLM
    profile_context_timestamp: Optional[datetime] = None  # Cache invalidation tracking
```

**Key Architectural Decisions**:
- **Messages over conversation_history**: Uses LangGraph's `add_messages` reducer for automatic message management
- **Removed processing fields**: `user_message`, `current_intent`, `active_agent` - agents work directly from messages
- **User context via config**: `user_id` and `session_id` passed via LangGraph config, not stored in state
- **Checkpointer handles metadata**: LangGraph's SQLite checkpointer manages creation/update timestamps automatically
- **Lazy-loaded profile context**: Profile data fetched from SQLite on first access, cached as formatted string for LLM system prompts
- **Optional shared data**: All cached data fields use `Optional[T] = None` pattern for lazy loading
- **No handoff context**: Agent coordination handled through LangGraph subgraph state sharing
- **No MCP results caching**: MCP integration patterns to be determined

**Usage Patterns**:
```python
# Nodes access user context from config
def agent_node(state: GlobalState, config: dict) -> dict:
    user_id = config["configurable"]["user_id"]
    session_id = config["configurable"]["thread_id"]  # For checkpointer
    
    # Lazy-load profile context (cached across runs via checkpointer)
    profile_context = state.get_profile_context(user_id)
    
    # Use in LLM system prompt
    system_message = f"You are a financial assistant. {profile_context}"
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
