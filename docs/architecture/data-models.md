# Data Models

## Core Business Entities

Based on POC requirements (Epic 1 & 2), here are the essential data models:

### Python Data Models for In-Memory Storage

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RiskTolerance(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AccountType(Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    MORTGAGE = "mortgage"

@dataclass
class Goal:
    id: str
    title: str
    description: str  # Plain text description for LLM understanding
    target_amount: Optional[float] = None  # May be vague/undefined
    target_date: Optional[str] = None  # May be vague/undefined
    priority: Priority = Priority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class User:
    id: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    profile_complete: bool = False

@dataclass
class UserProfile:
    user_id: str
    short_term_goals: List[Goal] = field(default_factory=list)
    medium_term_goals: List[Goal] = field(default_factory=list)
    long_term_goals: List[Goal] = field(default_factory=list)
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    values: List[str] = field(default_factory=list)
    ethical_investing: bool = False
    lifestyle_preferences: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PlaidAccount:
    id: str
    user_id: str
    plaid_account_id: str
    plaid_access_token: str  # Encrypted storage
    account_type: AccountType
    account_name: str
    balance: float
    last_synced: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class Transaction:
    id: str
    account_id: str
    plaid_transaction_id: str
    amount: float  # Negative for expenses, positive for income
    category: str
    subcategory: Optional[str] = None
    description: str
    date: str  # ISO date string
    pending: bool = False
    auto_categorized: bool = False  # Flag for automatic categorization

@dataclass
class Message:
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationSession:
    id: str
    user_id: str
    session_type: str  # 'onboarding', 'general', 'support'
    thread_id: str  # LangGraph thread identifier
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    # LangGraph handles conversation state via checkpointer
```

## LangGraph Integration for ConversationSession

**LangGraph Checkpointer System**:

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
