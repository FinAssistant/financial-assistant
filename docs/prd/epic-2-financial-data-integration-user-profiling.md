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
4. Clear "Ready to Use" completion state communicated conversationally and reflected in app functionality
5. Conversation state persistence across sessions using LangGraph checkpointing and SQLite storage

**Technical Implementation (references architecture/data-models.md):**
6. PersonalContextModel creation and SQLite persistence for structured data
7. LangGraph Onboarding Agent initialization with user context
8. Integration with existing authentication system and user profile
9. Wizard completion triggers user.profile_complete = True update

**User Experience:**
10. Conversational completion celebration and seamless transition to main app
11. Clear conversational indication that ongoing learning will enhance recommendations  
12. Natural language ability to modify essential information through conversational profile updates

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
    

## Story 2.2: Plaid Integration and Account Connection

As a user,I want to securely connect my bank accounts, credit cards, and loans with AI guidance,so that the system can analyze my complete financial picture safely and easily.

**Acceptance Criteria:**

1.  Plaid Link integration in React frontend within wizard flow
    
2.  Onboarding Agent access to Plaid APIs via MCP server tools
    
3.  Secure storage of Plaid access tokens (in-memory for POC)
    
4.  Account list display with balances and account types
    
5.  Error handling for connection failures with AI assistance
    
6.  Account disconnection capability
    
7.  AI explanations for why each account type is beneficial to connect

**Dependencies:** Requires Story 2.0 (LLM Provider Integration & Agent Foundation) and Story 2.1a (Essential Onboarding Setup) for user profile foundation and "Ready to Use" state.
    

## Story 2.3: Spending Agent - Transaction Analysis and Insights

As a user,I want my transactions automatically categorized and analyzed,so that I can understand my spending patterns without manual work.

**Acceptance Criteria:**

1.  Spending Agent implementation as LangGraph subgraph with MCP tool access
    
2.  Fetch and store transaction data via MCP server Plaid tools
    
3.  Automatic transaction categorization (dining, groceries, utilities, etc.)
    
4.  Cash flow calculation (income vs expenses)
    
5.  Residual cash availability computation
    
6.  Transaction history display with categories
    
7.  Basic spending pattern analysis

**Conversational Context Integration:**
8. Integration with Story 2.1b conversational discovery for context-aware analysis
9. Spending pattern analysis enhanced by user goals and values from Graphiti
10. Category suggestions informed by user lifestyle and preferences
11. Contextual insights that reference user's stated financial objectives

**Technical Implementation:**
12. LangGraph Spending Agent queries Graphiti for relevant user context
13. Spending analysis incorporates conversational financial goals and constraints
14. Agent coordination ensures consistent context across spending and goal discussions

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