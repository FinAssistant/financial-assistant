# Dual-Storage Architecture Pattern

## Architecture Overview

The AI Financial Assistant employs a sophisticated dual-storage architecture that separates structured operational data from dynamic financial context learning:

- **SQLite**: Stores all structured data (PersonalContext demographics + Transaction ledger)
- **Graphiti**: Stores dynamic Financial Profile (goals, risk tolerance, values, relationships, insights)

## Storage Responsibilities

### SQLite Storage (Structured Data)
**Purpose**: Fast queries for app routing, demographic calculations, and transaction analysis

**Data Types**:

**PersonalContext Tables**:
- Age ranges and life stages (affects app features and cost-of-living)
- Family structure and dependent information (drives emergency fund calculations)
- Marital status and basic spouse info (affects tax planning)
- Location context (cost-of-living adjustments)
- Caregiving responsibilities (affects available resources)

**Transaction Tables**:
- Canonical transaction data (canonical_hash as primary key)
- Financial amounts, dates, merchants, and categories
- AI-categorized spending classifications and confidence scores
- Account associations and transaction metadata
- Structured data for spending pattern analysis

**Key Characteristics**:
- Structured, enumerated data types
- ACID transaction consistency across user data and financial records
- Enables efficient SQL queries for demographic logic AND spending analysis
- Single source of truth for all queryable financial data
- Required for immediate app functionality and transaction lookups

### Graphiti Storage (Financial Profile & Insights)
**Purpose**: Conversational learning, relationship-based financial understanding, and derived insights

**Data Types**:
- Financial goals and their complex relationships
- Risk preferences with contextual reasoning
- Spending constraints and trade-off decisions
- Values and investment philosophy evolution
- Behavioral patterns and insights derived from transaction analysis
- Spending clusters and anomaly detection results
- Cross-merchant and cross-category relationship patterns
- LLM-generated financial insights and recommendations

**Key Characteristics**:
- Relationship-rich, graph-based connections
- Evolving through conversations and analytics
- Captures nuanced financial context and derived intelligence
- Enables sophisticated AI recommendations based on both structured data and conversational context
- Stores high-level insights rather than raw transaction data

## Agent Access Patterns

### Onboarding Agent Workflow with Graphiti Integration

The onboarding agent implements explicit conversation storage in Graphiti through a dedicated `_store_memory` node in its LangGraph workflow. This approach ensures that user conversations are preserved for building comprehensive financial profiles.

**Key Integration Points:**
- **Conversation Storage**: After each LLM interaction, conversations are stored in Graphiti using the `add_episode` MCP tool
- **User Data Isolation**: Critical security implementation using `user_id` as `group_id` to ensure complete data separation between users
- **Context Preservation**: Both user messages and AI responses are stored to maintain conversation continuity
- **Graceful Degradation**: Graphiti storage failures don't interrupt the onboarding flow

**Profile Building Strategy**: The agent combines structured demographic data (SQLite) with conversational context (Graphiti) to create comprehensive user profiles that capture both factual information and nuanced preferences expressed naturally.

**Enhanced Life Change Detection**: Advanced prompting enables the agent to detect significant life events (job loss, family changes, relocations) and update profiles accordingly, supporting dynamic financial planning needs.

*Implementation: See `backend/app/ai/onboarding.py` - `_store_memory` method*

### Spending Agent Data Access
```python
async def analyze_spending_patterns(user_id: str):
    # Get demographic context for calculations
    personal_context = await sqlite_storage.get_personal_context(user_id)
    family_size = personal_context.total_dependents_count

    # Get structured transaction data for analysis
    recent_transactions = await sqlite_storage.get_transactions(
        user_id=user_id,
        date_range=last_30_days(),
        limit=100
    )

    # Get financial values and spending insights from conversations
    financial_context = await graphiti.search(user_id, "spending priorities values constraints")
    spending_insights = await graphiti.search(user_id, "spending patterns anomalies")

    # Combine structured data with conversational context
    return generate_spending_analysis(
        personal_context=personal_context,
        transactions=recent_transactions,
        financial_context=financial_context,
        existing_insights=spending_insights
    )
```

## Data Flow Integration

### Transaction Processing Pipeline

The transaction processing pipeline demonstrates the hybrid architecture in action:

```python
async def process_transaction_batch(user_id: str, plaid_transactions: List[PlaidTransaction]):
    # Phase 1: Store canonical transaction data in SQLite
    for transaction in plaid_transactions:
        # AI categorization
        categorized_tx = await categorize_transaction(transaction)

        # Store in SQLite as source of truth
        await sqlite_storage.store_transaction(user_id, categorized_tx)

    # Phase 2: Generate insights for Graphiti (asynchronous)
    await generate_spending_insights_async(user_id, plaid_transactions)

async def generate_spending_insights_async(user_id: str, new_transactions: List[PlaidTransaction]):
    # Analyze patterns from SQLite data
    spending_analysis = await analyze_spending_patterns_from_sqlite(user_id)

    # Detect anomalies or interesting patterns
    if spending_analysis.monthly_food_spending > spending_analysis.historical_average * 1.5:
        await graphiti.add_episode(
            user_id=user_id,
            content=f"Unusual food spending detected: {spending_analysis.monthly_food_spending} vs historical average {spending_analysis.historical_average}",
            source_description="spending_analytics"
        )

    # Store merchant relationship insights
    if spending_analysis.new_merchant_detected:
        await graphiti.add_episode(
            user_id=user_id,
            content=f"New spending location: {spending_analysis.new_merchant_name} in {spending_analysis.merchant_category}",
            source_description="merchant_analytics"
        )
```

**Key Benefits of This Approach**:
- **SQLite**: Immediate, reliable storage with SQL queries for transaction lookups
- **Graphiti**: High-level insights and patterns derived from structured data
- **Asynchronous Processing**: Transaction storage doesn't block on insight generation
- **Single Source of Truth**: All transaction queries go through SQLite, Graphiti provides context

### User Profile Composition
Complete user understanding requires data from both systems:

```python
class UserProfileService:
    async def get_complete_profile(self, user_id: str):
        # Structured demographic and transaction data
        personal_context = await self.sqlite_storage.get_personal_context(user_id)
        recent_transactions = await self.sqlite_storage.get_transactions(
            user_id=user_id,
            limit=50
        )
        spending_summary = await self.sqlite_storage.get_spending_summary(user_id)

        # Dynamic financial understanding and insights
        financial_insights = await self.graphiti.search(user_id,
            "goals risk_tolerance values constraints")
        spending_insights = await self.graphiti.search(user_id,
            "spending patterns anomalies merchant relationships")

        return {
            "demographics": personal_context,
            "financial_profile": financial_insights,
            "transaction_data": {
                "recent_transactions": recent_transactions,
                "spending_summary": spending_summary
            },
            "behavioral_insights": spending_insights,
            "profile_completeness": self.assess_completeness(
                personal_context, financial_insights, recent_transactions
            )
        }
```

### Two-Phase Onboarding Support
The dual-storage architecture directly enables Epic 2.1's two-phase approach:

**Phase 1 (Essential Setup)**:
- Captures structured PersonalContext in SQLite
- Enables immediate app functionality
- Clear completion criteria (essential fields populated)

**Phase 2 (Ongoing Discovery)**:
- Builds rich Financial Profile in Graphiti
- No completion requirements - continuous learning
- Relationship-based understanding evolution

## Benefits

### Technical Benefits
✅ **Performance**: Fast SQL queries for app routing decisions  
✅ **Flexibility**: Graph relationships for complex financial contexts  
✅ **Scalability**: Appropriate storage choice for each data type  
✅ **Evolution**: Financial understanding improves over time

### User Experience Benefits  
✅ **Immediate Value**: App works after Phase 1 completion  
✅ **Progressive Enhancement**: Recommendations improve with usage  
✅ **Natural Learning**: No forced schema constraints for financial complexity  
✅ **Transparency**: Clear distinction between setup and learning phases

## Implementation Considerations

### Data Consistency
- SQLite provides ACID transactions for demographic updates AND transaction storage
- Transaction data is the canonical source of truth for all financial calculations
- Graphiti handles eventual consistency for conversational learning and derived insights
- Strong consistency within SQLite for user data and transactions; eventual consistency between SQLite and Graphiti for insights

### Graphiti MCP Tools Integration

**Core MCP Tools Used:**
- **`add_memory`**: Stores conversation episodes with automatic entity extraction
- **`search_memory_nodes`**: Retrieves relevant financial context based on semantic search
- **User Data Isolation**: All operations use `group_id = user_id` pattern for security

**MCP Client Architecture**: 
- Shared `GraphitiMCPClient` provides consistent interface across all agents
- Handles connection management and error recovery automatically  
- Enhanced content processing for financial conversations with context metadata

*Implementation: See `backend/app/ai/mcp_clients/graphiti_client.py`*

### Agent Coordination
- Agents query SQLite for structured data (demographics + transactions)
- Agents query Graphiti for conversational context and derived insights
- MCP server provides unified tool interface to both storage types
- Global state in LangGraph coordinates cross-system data access

### Transaction Storage Schema (SQLite)
**Core Tables**:
```sql
-- Canonical transaction storage
CREATE TABLE transactions (
    canonical_hash TEXT PRIMARY KEY,           -- Unique transaction identifier
    user_id TEXT NOT NULL,                     -- User association
    transaction_id TEXT UNIQUE,                -- Plaid transaction ID
    account_id TEXT,                           -- Associated account
    amount DECIMAL(10,2),                      -- Transaction amount
    date DATE,                                 -- Transaction date
    merchant_name TEXT,                        -- Merchant/payee
    category TEXT,                             -- Plaid category
    ai_category TEXT,                          -- AI-categorized category
    ai_subcategory TEXT,                       -- AI subcategory
    ai_confidence REAL,                        -- AI categorization confidence
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for common queries
    INDEX idx_transactions_user_date (user_id, date),
    INDEX idx_transactions_merchant (merchant_name),
    INDEX idx_transactions_category (ai_category)
);
```

**Benefits**:
- **Deduplication**: canonical_hash prevents duplicate storage
- **Performance**: Indexed queries for date ranges and spending analysis
- **Consistency**: ACID properties ensure reliable financial data
- **Analytics**: SQL aggregations for spending patterns and trends

## Completion State Consolidation

**Current Issue**: "Ready to Use" completion state was originally fragmented across multiple storage systems:
- User.onboarding_progress (primary flag)
- PersonalContext model (profile data)
- LangGraph SQLite checkpointer (conversation state)
- GlobalState.connected_accounts (Plaid connection status)

**Current Approach**: Use PersonalContext model as single source of truth for completion state. PersonalContext is only marked complete after both demographic data collection AND successful Plaid account linking, eliminating the need for complex aggregation logic.

**Future Simplification**: Remove redundant completion flags from User model and other locations once PersonalContext-based completion is fully validated.

### Migration Strategy
- PersonalContext can be migrated between structured storage systems
- Graphiti content grows organically and doesn't require migration
- Clear separation enables independent scaling of each storage type