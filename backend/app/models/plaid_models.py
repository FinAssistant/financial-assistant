"""
Pydantic models for Plaid API data structures.
These models represent the sanitized transaction and account data from Plaid.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from decimal import Decimal

class PlaidTransaction(BaseModel):
    """
    Pydantic model representing a sanitized Plaid transaction.
    
    This model matches the structure returned by PlaidService._sanitize_transaction_data()
    and represents the core transaction data used throughout the application.
    """
    
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    transaction_id: str = Field(..., description="Unique transaction identifier from Plaid")
    account_id: str = Field(..., description="Account identifier this transaction belongs to")
    amount: Decimal = Field(..., description="Transaction amount (positive for debits, negative for credits)")
    date: Optional[str] = Field(None, description="Transaction date as string")
    name: str = Field(..., description="Transaction name/description")
    merchant_name: Optional[str] = Field(None, description="Merchant name if available")
    category: List[str] = Field(default_factory=list, description="Plaid transaction categories")
    pending: bool = Field(default=False, description="Whether transaction is pending")
    
    # AI categorization fields - to be populated by AI analysis
    ai_category: Optional[str] = Field(None, description="AI-generated category")
    ai_subcategory: Optional[str] = Field(None, description="AI-generated subcategory")
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI categorization confidence score")
    ai_tags: List[str] = Field(default_factory=list, description="AI-generated tags for transaction")
    
    @field_validator('amount', mode='before')
    @classmethod
    def convert_amount(cls, v):
        """Convert amount to Decimal for precise financial calculations."""
        if v is None:
            return Decimal('0.00')
        return Decimal(str(v))
    
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Keep date as string for LLM compatibility."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if hasattr(v, 'isoformat'):  # date or datetime object
            return v.isoformat()
        return str(v) if v else None
    
    @field_validator('name')
    @classmethod
    def clean_name(cls, v):
        """Clean and normalize transaction name."""
        if not v:
            return "Unknown Transaction"
        return v.strip()
    
    @field_validator('category', mode='before')
    @classmethod
    def ensure_category_list(cls, v):
        """Ensure category is always a list."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v) if v else []


class PlaidAccountBalance(BaseModel):
    """
    Pydantic model for Plaid account balance information.
    """
    
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    current: Optional[Decimal] = Field(None, description="Current balance")
    available: Optional[Decimal] = Field(None, description="Available balance")
    limit: Optional[Decimal] = Field(None, description="Credit limit (for credit accounts)")
    currency: str = Field(default="USD", description="Currency code")
    
    @field_validator('current', 'available', 'limit', mode='before')
    @classmethod
    def convert_balance(cls, v):
        """Convert balance to Decimal for precise calculations."""
        if v is None:
            return None
        return Decimal(str(v))


class PlaidAccount(BaseModel):
    """
    Pydantic model representing a sanitized Plaid account.
    
    This model matches the structure returned by PlaidService._sanitize_account_data()
    """
    
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    account_id: str = Field(..., description="Unique account identifier from Plaid")
    name: str = Field(..., description="Account name (e.g., 'Chase Checking')")
    type: str = Field(..., description="Account type (e.g., 'depository', 'credit')")
    subtype: Optional[str] = Field(None, description="Account subtype (e.g., 'checking', 'savings')")
    mask: Optional[str] = Field(None, description="Last 4 digits of account number")
    balances: PlaidAccountBalance = Field(..., description="Account balance information")
    
    @field_validator('name')
    @classmethod
    def clean_name(cls, v):
        """Clean account name."""
        if not v:
            return "Unknown Account"
        return v.strip()


class TransactionBatch(BaseModel):
    """
    Pydantic model for a batch of transactions with metadata.
    
    This represents the structure returned by MCP tools and used for AI analysis.
    """
    
    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=True,
        validate_assignment=False,  # Avoid recursion with model_validator
        arbitrary_types_allowed=True
    )
    
    transactions: List[PlaidTransaction] = Field(default_factory=list, description="List of transactions")
    total_count: int = Field(default=0, description="Total number of transactions")
    date_range_start: Optional[str] = Field(None, description="Start date of transaction range as string")
    date_range_end: Optional[str] = Field(None, description="End date of transaction range as string")
    accounts_included: List[str] = Field(default_factory=list, description="Account IDs included in batch")
    
    @model_validator(mode='after')
    def calculate_metadata(self):
        """Automatically calculate metadata from transactions."""
        transactions = self.transactions
        
        # Set total count
        self.total_count = len(transactions)
        
        # Set accounts included
        account_ids = list(set(t.account_id for t in transactions))
        self.accounts_included = account_ids
        
        # Set date range
        if transactions:
            dates = [t.date for t in transactions if t.date is not None]
            if dates:
                sorted_dates = sorted(dates)
                self.date_range_start = sorted_dates[0]
                self.date_range_end = sorted_dates[-1]
        
        return self


class TransactionCategorization(BaseModel):
    """
    Pydantic model specifically for LLM structured output in transaction categorization.
    
    This model is optimized for use with LLM structured generation and focuses
    on the AI categorization results that will be applied to PlaidTransaction objects.
    """
    
    def __init_subclass__(cls, **kwargs):
        """Configure model based on LLM provider."""
        super().__init_subclass__(**kwargs)
        try:
            from app.config import Settings
            settings = Settings()
            
            # Only use extra="forbid" for OpenAI structured output
            if settings.default_llm_provider == "openai":
                cls.model_config = ConfigDict(
                    extra="forbid",
                    use_enum_values=True,
                    arbitrary_types_allowed=False
                )
            else:
                cls.model_config = ConfigDict(
                    extra="ignore",
                    use_enum_values=True,
                    arbitrary_types_allowed=False
                )
        except ImportError:
            # Fallback configuration if settings unavailable
            cls.model_config = ConfigDict(
                extra="ignore",
                use_enum_values=True,
                arbitrary_types_allowed=False
            )
    
    transaction_id: str = Field(..., description="Transaction ID being categorized")
    ai_category: str = Field(..., description="Primary AI-generated category")
    ai_subcategory: str = Field(..., description="AI-generated subcategory")
    ai_confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    ai_tags: List[str] = Field(default_factory=list, description="List of relevant tags")
    reasoning: str = Field(..., description="Brief explanation of the categorization decision")
    
    @field_validator('ai_confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is a float between 0 and 1."""
        return max(0.0, min(1.0, float(v)))
    
    @field_validator('ai_category', 'ai_subcategory', 'reasoning')
    @classmethod
    def validate_strings(cls, v):
        """Ensure string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('ai_tags')
    @classmethod
    def validate_tags(cls, v):
        """Clean and validate tags list."""
        if not v:
            return []
        # Remove empty tags and clean whitespace
        return [tag.strip() for tag in v if tag and tag.strip()]


class TransactionCategorizationBatch(BaseModel):
    """
    Pydantic model for batch transaction categorization results from LLM.
    
    This model is designed for structured LLM output when categorizing multiple transactions.
    """
    
    def __init_subclass__(cls, **kwargs):
        """Configure model based on LLM provider."""
        super().__init_subclass__(**kwargs)
        try:
            from app.config import Settings
            settings = Settings()
            
            # Only use extra="forbid" for OpenAI structured output
            if settings.default_llm_provider == "openai":
                cls.model_config = ConfigDict(
                    extra="forbid",
                    use_enum_values=True,
                    arbitrary_types_allowed=False
                )
            else:
                cls.model_config = ConfigDict(
                    extra="ignore",
                    use_enum_values=True,
                    arbitrary_types_allowed=False
                )
        except ImportError:
            # Fallback configuration if settings unavailable
            cls.model_config = ConfigDict(
                extra="ignore",
                use_enum_values=True,
                arbitrary_types_allowed=False
            )
    
    categorizations: List[TransactionCategorization] = Field(
        default_factory=list, 
        description="List of transaction categorizations"
    )
    processing_summary: str = Field(
        ..., 
        description="Summary of the categorization process"
    )
    
    @field_validator('categorizations', mode='before')
    @classmethod
    def parse_categorizations(cls, v):
        """Parse categorizations if needed, handle various input formats."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v) if v.strip() else []
            except json.JSONDecodeError:
                return []
        return v if isinstance(v, list) else []
    
    @field_validator('processing_summary')
    @classmethod
    def validate_summary(cls, v):
        """Ensure summary is provided."""
        if not v or not v.strip():
            return "Categorization completed"
        return v.strip()