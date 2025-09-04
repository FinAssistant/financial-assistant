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

### Onboarding Agent Workflow
```python
# Phase 1: Essential Information Collection
async def collect_essential_info(user_id: str):
    # Store structured data in SQLite
    personal_context = await extract_demographics(conversation)
    await sqlite_storage.store_personal_context(user_id, personal_context)
    
    # Store conversational context in Graphiti
    await graphiti.add_episode(user_id, conversation_context)

# Phase 2: Ongoing Conversational Discovery  
async def ongoing_discovery(user_id: str, conversation: str):
    # Query existing context from both sources
    personal_context = await sqlite_storage.get_personal_context(user_id)
    financial_context = await graphiti.search(user_id, "financial goals constraints")
    
    # Store new insights in appropriate system
    await graphiti.add_episode(user_id, conversation)
```

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

### Agent Coordination
- Agents query both systems as needed for complete context
- MCP server provides unified tool interface to both storage types
- Global state in LangGraph coordinates cross-system data access

### Migration Strategy
- PersonalContext can be migrated between structured storage systems
- Graphiti content grows organically and doesn't require migration
- Clear separation enables independent scaling of each storage type