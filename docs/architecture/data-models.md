# Data Models

## Graph-First Financial Profile Data Model

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

# ===== ESSENTIAL ENUMS (For Structured Data Only) =====

class AgeRange(Enum):
    """Age ranges for demographic categorization and app routing logic"""
    UNDER_18 = "under_18"
    RANGE_18_25 = "18_25"
    RANGE_26_35 = "26_35"
    RANGE_36_45 = "36_45"
    RANGE_46_55 = "46_55"
    RANGE_56_65 = "56_65"
    OVER_65 = "over_65"

class LifeStage(Enum):
    """Life stages that affect financial planning approach and app features"""
    STUDENT = "student"
    YOUNG_PROFESSIONAL = "young_professional"
    EARLY_CAREER = "early_career"
    ESTABLISHED_CAREER = "established_career"
    FAMILY_BUILDING = "family_building"
    PEAK_EARNING = "peak_earning"
    PRE_RETIREMENT = "pre_retirement"
    RETIREMENT = "retirement"

class MaritalStatus(Enum):
    """Legal marital status - affects tax planning and joint account handling"""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    DOMESTIC_PARTNERSHIP = "domestic_partnership"

class FamilyStructure(Enum):
    """Family structure affects emergency fund needs and financial planning complexity"""
    SINGLE_NO_DEPENDENTS = "single_no_dependents"
    SINGLE_WITH_DEPENDENTS = "single_with_dependents" 
    MARRIED_DUAL_INCOME = "married_dual_income"
    MARRIED_SINGLE_INCOME = "married_single_income"
    MARRIED_NO_INCOME = "married_no_income"
    DOMESTIC_PARTNERSHIP = "domestic_partnership"
    DIVORCED_SHARED_CUSTODY = "divorced_shared_custody"
    DIVORCED_SOLE_CUSTODY = "divorced_sole_custody"

class EducationLevel(Enum):
    """Education levels for dependents - affects education cost calculations"""
    PRESCHOOL = "preschool"        # 3-5 years
    ELEMENTARY = "elementary"      # 6-10 years  
    MIDDLE_SCHOOL = "middle_school" # 11-13 years
    HIGH_SCHOOL = "high_school"    # 14-18 years
    COLLEGE_BOUND = "college_bound" # Planning for college
    COLLEGE_CURRENT = "college_current" # Currently in college
    POST_GRADUATE = "post_graduate"

class CaregivingResponsibility(Enum):
    """Caregiving responsibilities affect available financial resources"""
    NONE = "none"
    AGING_PARENTS = "aging_parents"
    DISABLED_FAMILY_MEMBER = "disabled_family_member"
    BOTH_CHILDREN_AND_PARENTS = "sandwich_generation"

class AccountType(Enum):
    """Plaid account types - maps to external API requirements"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    MORTGAGE = "mortgage"

class InvestmentTimeline(Enum):
    """Investment time horizon for risk and allocation decisions"""
    SHORT_TERM = "short_term"      # < 2 years
    MEDIUM_TERM = "medium_term"    # 2-10 years
    LONG_TERM = "long_term"        # 10+ years

class RiskTolerance(Enum):
    """Investment risk tolerance levels"""
    CONSERVATIVE = "conservative"   # Low volatility, capital preservation
    MODERATE = "moderate"          # Balanced growth and stability
    AGGRESSIVE = "aggressive"      # High growth potential, high volatility

class InvestmentExperience(Enum):
    """Previous investment experience levels"""
    NONE = "none"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# ===== CORE USER MODEL =====

@dataclass  
class OnboardingProgress:
    """Tracks concrete onboarding steps, not subjective profile completeness"""
    accounts_connected: bool = False        # Binary: Plaid integration complete
    first_conversation_completed: bool = False  # Binary: Had initial AI conversation
    graphiti_context_established: bool = False  # Binary: Has some context nodes
    risk_assessment_completed: bool = False # Binary: Investment risk tolerance assessed
    
    # Timestamps for understanding user engagement
    first_login: Optional[datetime] = None
    last_active: Optional[datetime] = None
    account_connection_date: Optional[datetime] = None
    
    # Dynamic contextual completeness - queried from Graphiti
    @property 
    def has_sufficient_context_for_recommendations(self) -> bool:
        """Determined by AI agent based on Graphiti context richness"""
        # This would query Graphiti to assess if we have enough context
        # Rather than checking arbitrary boolean flags
        return False  # Placeholder - would be implemented with Graphiti queries

@dataclass
class User:
    id: str
    email: str
    created_at: datetime
    onboarding_progress: OnboardingProgress
    last_profile_update: datetime = field(default_factory=datetime.now)

# ===== PERSONAL CONTEXT MODELS =====

@dataclass
class SpouseBasicInfo:
    """Minimal spouse information - financial details live in Graphiti relationships"""
    name: Optional[str] = None  # For personalization in conversations
    age_range: Optional[AgeRange] = None
    employment_status: Optional[str] = None  # Basic categorization for app logic
    # All financial info (income, risk preferences, account details) → Graphiti

@dataclass 
class Dependent:
    """Minimal dependent info - financial details live in Graphiti"""
    id: str
    relationship: str  # "child", "stepchild", "parent", "sibling", etc.
    age: Optional[int] = None
    age_range: Optional[AgeRange] = None  # If exact age not disclosed
    education_level: Optional[EducationLevel] = None  # Drives cost calculations
    special_needs: bool = False  # Boolean flag affects planning complexity
    # All financial info (costs, support amounts, savings progress) → Graphiti

@dataclass
class PersonalContext:
    """Core demographic and family structure - financial details in Graphiti"""
    
    # Basic Demographics (affect app routing and cost-of-living calculations)
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    occupation_type: Optional[str] = None  # Basic categorization for context
    location_context: Optional[str] = None  # Affects cost of living calculations
    
    # Family Structure (affects planning complexity and emergency fund needs)
    family_structure: Optional[FamilyStructure] = None
    marital_status: Optional[MaritalStatus] = None
    spouse_info: Optional[SpouseBasicInfo] = None
    
    # Dependents (basic info for app logic)
    dependents: List[Dependent] = field(default_factory=list)
    total_dependents_count: int = 0  # Quick reference for calculations
    children_count: int = 0  # Quick reference for calculations
    
    # Caregiving responsibilities (affects available resources)
    caregiving_responsibilities: List[CaregivingResponsibility] = field(default_factory=list)
    
    # All detailed financial info → Graphiti:
    # - Housing costs and moving plans
    # - Joint vs separate finances
    # - Life event planning and timelines
    # - Dependent support amounts and education costs

# ===== GRAPHITI INTEGRATION (Minimal - LangGraph handles conversation state) =====

@dataclass
class GraphitiQueryCache:
    """Optional cache for expensive Graphiti queries - may not be needed initially"""
    user_id: str
    query_type: str  # "financial_goals", "risk_context", "spending_patterns"
    query_result: Dict[str, Any] = field(default_factory=dict)  # JSON response from Graphiti
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

# Note: LangGraph checkpointer handles:
# - Conversation state and history
# - Message persistence across sessions  
# - Thread-based conversation management
# - State serialization/deserialization

# ===== INVESTMENT RISK MODELS =====

@dataclass
class RiskProfile:
    """Investment risk tolerance and preferences"""
    user_id: str
    risk_tolerance: Optional[RiskTolerance] = None
    investment_timeline: Optional[InvestmentTimeline] = None
    investment_percentage: Optional[float] = None  # % of savings to invest (0-100)
    volatility_comfort: Optional[int] = None  # Scale 1-10
    previous_experience: Optional[InvestmentExperience] = None
    assessment_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

# ===== ACCOUNT MODELS =====

@dataclass
class PlaidAccount:
    id: str
    user_id: str
    plaid_account_id: str
    plaid_access_token: str  # Encrypted storage
    account_type: AccountType
    account_name: str
    balance: Decimal
    last_synced: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class Transaction:
    id: str
    account_id: str
    plaid_transaction_id: str
    amount: Decimal  # Negative for expenses, positive for income
    category: str
    subcategory: Optional[str] = None
    description: str
    date: str  # ISO date string
    pending: bool = False
    auto_categorized: bool = False

# ===== NO SEPARATE FINANCIAL PROFILE NEEDED =====

# Financial data architecture:
# ✅ User + PersonalContext: Structured demographic data for app routing
# ✅ Graphiti: All financial knowledge (goals, preferences, constraints)
# ✅ LangGraph: Current conversation state and agent context
# ✅ PlaidAccount: External API integration data
#
# This eliminates the need for a separate FinancialProfile class

# ===== LANGGRAPH CONVERSATION INTEGRATION =====

# TODO: Design actual LangGraph workflow first to determine what thread metadata we need
# LangGraph checkpointer handles:
# - Message history and state persistence
# - Thread management and continuation
# - State serialization across sessions
#
# We may not need any additional conversation models until we understand
# the specific LangGraph implementation requirements
```

## Architecture Decision: Graph-First Approach

**Key Changes Made:**
- **Removed rigid financial schemas**: Goals, risk profiles, constraints, preferences now live in Graphiti
- **Added conversation capture models**: For feeding relationship learning
- **Simplified to essential structured data**: Only what needs SQL-like operations
- **Graph integration models**: References and caching for performance

**What Lives Where:**

**Structured Storage (PostgreSQL/In-Memory):**
- User identity & authentication
- Personal context (family structure, dependents) - affects app routing
- Account integration (Plaid tokens, balances) - external API contracts
- Conversation metadata - for debugging and analytics

**Graph Database (Graphiti + Neo4j):**
- Financial goals and their relationships
- Risk preferences and reasoning
- Spending constraints and trade-offs  
- Values and investment preferences
- Goal conflicts and prioritization
- Behavioral patterns and insights

**Benefits:**
✅ Natural conversational extraction
✅ Relationship learning and evolution
✅ Flexible goal and preference modeling
✅ No forced schema constraints
✅ Better handles nuanced financial contexts

**LangGraph + Graphiti Integration:**
```python
# LangGraph manages conversation flow and state
class FinancialAssistantState(BaseModel):
    user_message: str
    agent_response: str
    user_id: str
    # LangGraph checkpointer persists this state automatically

# Graphiti integration happens within agent nodes
async def onboarding_agent(state: FinancialAssistantState):
    # Store conversation in Graphiti for long-term learning
    await graphiti.add_episode(state.user_id, state.user_message)
    
    # Query Graphiti for context
    context = await graphiti.search(state.user_id, "financial goals and constraints")
    
    # Generate response (LangGraph manages the conversation flow)
    response = await llm.ainvoke([...])
    return {"agent_response": response}

# LangGraph handles:
# ✅ Conversation state management
# ✅ Agent orchestration  
# ✅ Thread persistence
# ✅ State checkpointing

# Graphiti handles:
# ✅ Long-term knowledge extraction
# ✅ Relationship learning
# ✅ Context queries for agent decision-making
```