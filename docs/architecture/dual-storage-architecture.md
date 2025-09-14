# Dual-Storage Architecture Pattern

## Architecture Overview

The AI Financial Assistant employs a sophisticated dual-storage architecture that separates structured demographic data from dynamic financial context learning:

- **SQLite**: Stores structured PersonalContext (demographics, family structure, life stage)
- **Graphiti**: Stores dynamic Financial Profile (goals, risk tolerance, values, relationships)

## Storage Responsibilities

### SQLite Storage (PersonalContext)
**Purpose**: Fast queries for app routing and demographic-based calculations

**Data Types**:
- Age ranges and life stages (affects app features and cost-of-living)
- Family structure and dependent information (drives emergency fund calculations)
- Marital status and basic spouse info (affects tax planning)
- Location context (cost-of-living adjustments)
- Caregiving responsibilities (affects available resources)

**Key Characteristics**:
- Structured, enumerated data types
- Stable demographic information
- Enables efficient SQL queries for app logic
- Required for immediate app functionality

### Graphiti Storage (Financial Profile)
**Purpose**: Conversational learning and relationship-based financial understanding

**Data Types**:
- Financial goals and their complex relationships
- Risk preferences with contextual reasoning
- Spending constraints and trade-off decisions
- Values and investment philosophy evolution
- Behavioral patterns and insights over time

**Key Characteristics**:
- Relationship-rich, graph-based connections
- Evolving through conversations
- Captures nuanced financial context
- Enables sophisticated AI recommendations

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
    
    # Get financial values and constraints  
    financial_context = await graphiti.search(user_id, "spending priorities values")
    
    # Combine for personalized analysis
    return generate_spending_insights(personal_context, financial_context)
```

## Data Flow Integration

### User Profile Composition
Complete user understanding requires data from both systems:

```python
class UserProfileService:
    async def get_complete_profile(self, user_id: str):
        # Structured demographic data
        personal_context = await self.sqlite_storage.get_personal_context(user_id)
        
        # Dynamic financial understanding
        financial_insights = await self.graphiti.search(user_id, 
            "goals risk_tolerance values constraints")
        
        return {
            "demographics": personal_context,
            "financial_profile": financial_insights,
            "profile_completeness": self.assess_completeness(
                personal_context, financial_insights
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
- SQLite provides ACID transactions for demographic updates
- Graphiti handles eventual consistency for conversational learning
- No strong consistency required between storage systems

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
- Agents query both systems as needed for complete context
- MCP server provides unified tool interface to both storage types
- Global state in LangGraph coordinates cross-system data access

### Migration Strategy
- PersonalContext can be migrated between structured storage systems
- Graphiti content grows organically and doesn't require migration
- Clear separation enables independent scaling of each storage type