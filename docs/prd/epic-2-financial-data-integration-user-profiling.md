# Epic 2: Financial Data Integration & User Profiling

**Epic Goal:** Implement two-phase AI-powered onboarding: essential setup for immediate app usage, followed by ongoing conversational discovery that builds comprehensive user financial profiles for personalized AI recommendations. Integrate LangGraph agent architecture with SQLite persistence and Graphiti knowledge management.

## Story 2.0: LLM Provider Integration & Agent Foundation

As a system architect,
I want LLM providers configured with LangGraph agent orchestration foundation,
so that AI agents can process conversations and make intelligent routing decisions for all Epic 2 functionality.

**Acceptance Criteria:**
1. LLM API key configuration system supporting multiple providers (OpenAI, Anthropic)
2. Core LangGraph workflow setup with GlobalState model for shared agent context
3. Orchestrator Agent with LLM-powered intent recognition and agent routing
4. Basic conversation state management with SQLite checkpointing for persistence
5. MCP client integration for centralized tool access across all agents
6. Integration with existing JWT authentication for user context in agent operations

**Dependencies:** Requires completion of Epic 1 authentication and MCP server foundation.

## Story 2.1a: Essential Onboarding Setup

As a user,
I want to complete essential setup information to start using the app immediately,
so that I can access core functionality while the AI learns my preferences over time.

**Acceptance Criteria:**

**Essential Information Capture:**
1. Conversational onboarding flow guided by LangGraph Onboarding Agent with progress awareness
2. Natural language extraction of demographic data into PersonalContextModel (age_range, marital_status, has_dependents)
3. LLM-guided account connection process with contextual explanations and Plaid Link integration
4. Clear "Ready to Use" completion state achieved only after successful Plaid account connection, communicated conversationally and reflected in app functionality
5. Conversation state persistence across sessions using LangGraph checkpointing and SQLite storage

**Technical Implementation (references architecture/data-models.md):**
6. PersonalContextModel creation and SQLite persistence for structured data
7. LangGraph Onboarding Agent initialization with user context
8. Integration with existing authentication system and user profile
9. Secure storage of Plaid access tokens (in SQLite DB for POC)
10. Wizard completion triggers PersonalContext.is_complete = True update

**User Experience:**
11. Conversational completion celebration and seamless transition to main app
12. Clear conversational indication that ongoing learning will enhance recommendations
13. Natural language ability to modify essential information through conversational profile updates

**Dependencies:** Requires completion of Epic 1 authentication and MCP server foundation, AND Story 2.0 (LLM Provider Integration & Agent Foundation).


## Story 2.1b: Conversational Profile Discovery  

As a user,
I want the AI to gradually understand my financial preferences through natural conversations,
so that recommendations become increasingly personalized without requiring lengthy forms.

**Acceptance Criteria:**

**Conversational Learning Implementation:**
1. LangGraph agents capture financial context from natural conversations
2. Automatic extraction and storage of financial goals in Graphiti knowledge graph
3. Progressive discovery of risk tolerance through scenario-based discussions
4. Investment philosophy and ethical preferences learned through conversation
5. Complex family obligations and constraints understood through contextual discussion

**Technical Implementation (references architecture/data-models.md):**
6. Graphiti integration for relationship and preference storage
7. LangGraph conversation state management with SQLite checkpointing
8. Context queries enable agents to reference previously learned information  
9. Conversation history persistence across sessions and agent handoffs

**Ongoing Enhancement:**
10. Profile insights dashboard showing how understanding has evolved
11. User awareness of ongoing learning without pressure to complete everything
12. Smooth integration with financial conversations across all app interactions
13. Ability to explicitly correct or update learned preferences

**Parallel Track:** Runs continuously alongside user interactions, enhancing all other Epic 2 stories over time.


## Story 2.1c: UI Completion State Management

As a user,
I want the interface to only show relevant features based on my onboarding completion status,
so that I'm not confused by features I can't use until setup is complete.

**Acceptance Criteria:**

**Incomplete Onboarding UI:**
1. Show only chatbot interface and profile completion progress indicator
2. Display collected profile data in a progress-aware format
3. Hide main navigation and dashboard features until "Ready to Use" state
4. Clear visual indication of onboarding progress and next steps

**Completion State Detection:**
5. Use PersonalContext model as single source of truth for completion status
6. Real-time updates to UI state based on completion changes
7. Seamless transition to full app interface upon completion

**User Experience:**
8. Clear progress indication showing onboarding steps completed
9. Encouraging messaging about benefits of completing setup
10. No broken or empty states visible to incomplete users

**Dependencies:** Requires Story 2.0 (LLM Provider Integration & Agent Foundation) and Story 2.1a (Essential Onboarding Setup) for completion state logic.


## Story 2.2: Account Management and Optimization

As a user, I want to view and manage my connected accounts with AI guidance for account portfolio optimization, so that I can maintain healthy account connections and maximize financial data completeness.

**Acceptance Criteria:**

**Account Display and Management:**
1. Comprehensive account list display with balances, account types, and connection status
2. Account disconnection capability with confirmation and impact explanation
3. Account health monitoring (connection status, last sync, error states)
4. Real-time balance updates and account status refresh

**Error Recovery and Maintenance:**
5. Intelligent error handling for expired tokens, bank changes, and connection issues
6. AI-assisted troubleshooting with step-by-step reconnection guidance
7. Proactive notifications for accounts requiring attention

**Account Portfolio Optimization:**
8. AI-driven analysis of account coverage gaps (missing account types)
9. Personalized prompts to connect additional beneficial accounts
10. Smart recommendations for account consolidation or optimization opportunities

**Dependencies:** Requires Story 2.0 (LLM Provider Integration & Agent Foundation) and Story 2.1a (Essential Onboarding Setup) for initial account connection foundation.
    

## Story 2.3: Spending Agent - Transaction Analysis and Insights

As a user, I want my transactions automatically categorized, analyzed, and transformed into actionable spending insights, so that I can understand my financial patterns and receive personalized recommendations to optimize my spending.

**Acceptance Criteria:**

### Technical Foundation
1. Spending Agent implementation as LangGraph subgraph with MCP tool access
2. Intelligent transaction fetching via MCP server Plaid tools with incremental updates
3. AI-powered transaction categorization with continuous user feedback learning
4. Transaction accuracy features: re-categorization, split transactions, pending transaction management

### Analysis & Intelligence
5. Comprehensive spending pattern recognition (recurring expenses, seasonal trends, anomalies)
6. Cash flow analysis with trend detection and forecasting capabilities
7. Spending personality profiling (Saver, Spender, Planner, Impulse, Convenience-focused)
8. Behavioral insight generation (spending triggers, timing patterns, stress spending)
9. Risk tolerance assessment and financial motivation profiling

### Optimization Engine
10. Smart expense reduction recommendations with personality-tailored strategies
11. Subscription and recurring payment optimization (duplicates, unused services, consolidation)
12. Cost optimization opportunities with savings calculations based on spending patterns
13. Residual cash optimization with surplus allocation recommendations

### Budget & Planning
14. Conversational budget guidance with spending awareness and category insights
15. Intelligent budget recommendations delivered through AI conversation based on spending history and personality
16. Budget alerts and variance insights delivered conversationally with adjustment suggestions
17. Goal alignment analysis comparing spending habits to stated objectives through AI conversation

### User Experience & Interface
18. Conversational transaction queries with natural language processing
19. Personality-aware communication with adaptive tone and messaging based on user insights stored in Graphiti

**Dependencies:** Requires Story 2.0 (LLM Provider Integration & Agent Foundation), Story 2.1a completion for account access, AND meaningful Story 2.1b context accumulation for intelligent analysis.
    

## Story 2.4: Financial Profile Dashboard

As a user,I want to see my complete financial profile in one place,so that I can understand my current financial health and baseline.

**Acceptance Criteria:**

1.  Dashboard data aggregated via Orchestrator Agent from specialized agents
    
2.  Comprehensive profile showing all connected accounts via agent coordination
    
3.  Net worth calculation and display
    
4.  Cash flow summary with income/expense breakdown
    
5.  Goal progress visualization
    
6.  Financial health score or indicator
    
7.  Profile completeness status

**Dependencies:** Requires Story 2.0 (LLM Provider Integration & Agent Foundation) for Orchestrator Agent functionality and all previous Epic 2 stories for comprehensive data aggregation.
