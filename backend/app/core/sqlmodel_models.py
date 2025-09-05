"""
SQLModel-based database models for structured user data.
Provides Pydantic integration while maintaining SQLAlchemy ORM functionality.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from enum import Enum

from sqlmodel import SQLModel, Field, Column, DateTime
from pydantic import EmailStr, field_validator

class AgeRange(str, Enum):
    """Age range categories for demographic analysis."""
    UNDER_25 = "under_25"
    RANGE_25_34 = "25_34"
    RANGE_35_44 = "35_44" 
    RANGE_45_54 = "45_54"
    RANGE_55_64 = "55_64"
    OVER_65 = "over_65"

class LifeStage(str, Enum):
    """Life stage categories that affect financial priorities."""
    STUDENT = "student"
    EARLY_CAREER = "early_career"
    FAMILY_BUILDING = "family_building"
    PEAK_CAREER = "peak_career"
    PRE_RETIREMENT = "pre_retirement"
    RETIREMENT = "retirement"

class MaritalStatus(str, Enum):
    """Marital status options."""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"

# Base model for shared fields and methods
class UserBase(SQLModel):
    """Base user model with common fields and validation."""
    email: EmailStr = Field(unique=True, index=True)
    name: str = Field(default="", max_length=255)
    profile_complete: bool = Field(default=False)
    
    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower()

# Database model (table=True)
class UserModel(UserBase, table=True):
    """
    SQLModel User model that combines Pydantic validation with SQLAlchemy ORM.
    Maintains backward compatibility with existing User dataclass interface.
    """
    __tablename__ = "users"
    
    # Primary fields
    id: str = Field(primary_key=True, max_length=255)
    password_hash: str = Field(max_length=255)
    
    # Timestamps with timezone-aware defaults
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), 
                        onupdate=lambda: datetime.now(timezone.utc))
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format for backward compatibility.
        Matches the interface expected by existing code.
        """

        return {
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'name': self.name,
            'profile_complete': self.profile_complete,
            'created_at': self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserModel':
        """
        Create UserModel from dictionary data.
        Maintains compatibility with existing code.
        """
        core_fields = {'id', 'email', 'password_hash', 'name', 'profile_complete', 'created_at'}
        
        # Extract core fields
        core_data = {k: v for k, v in data.items() if k in core_fields}
        
        return cls(**core_data)
    
    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        Update model from dictionary updates.
        Maintains backward compatibility.
        """
        core_fields = {'name', 'profile_complete'}
        
        # Update core fields
        for field in core_fields:
            if field in updates:
                setattr(self, field, updates[field])
        
        self.updated_at = datetime.now(timezone.utc)
    
    def to_public_dict(self) -> Dict[str, Any]:
        """
        Convert to public dictionary (without sensitive data).
        Maintains compatibility with existing User dataclass.
        """

        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_complete': self.profile_complete,
            'created_at': self.created_at
        }

# API response models (table=False - these are just Pydantic models)
class UserRead(UserBase):
    """User model for API responses (read operations)."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserPublic(SQLModel):
    """Public user model without sensitive data."""
    id: str
    email: EmailStr
    name: str
    profile_complete: bool
    created_at: datetime

class UserCreate(SQLModel):
    """User model for creation requests."""
    id: str
    email: EmailStr
    password_hash: str
    name: str = ""

class UserUpdate(SQLModel):
    """User model for update requests."""
    name: Optional[str] = None
    profile_complete: Optional[bool] = None

# Future: PersonalContext model for structured demographic data
class PersonalContextModel(SQLModel, table=True):
    """
    Structured demographic data for the dual-storage architecture.
    Stores PersonalContext information in SQLite for fast queries.
    """
    __tablename__ = "personal_context"
    
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    
    # Core demographic fields
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    marital_status: Optional[MaritalStatus] = None
    
    # Family structure
    has_dependents: bool = Field(default=False)
    dependent_count: int = Field(default=0, ge=0)
    spouse_income: Optional[float] = Field(default=None, ge=0)
    
    # Location context
    state: Optional[str] = Field(default=None, max_length=2)  # US state code
    cost_of_living_index: Optional[float] = Field(default=None, ge=0)
    
    # Financial context flags
    has_emergency_fund: bool = Field(default=False)
    has_retirement_savings: bool = Field(default=False)
    has_investment_experience: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), 
                        onupdate=lambda: datetime.now(timezone.utc))
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for agent consumption."""
        return {
            'user_id': self.user_id,
            'age_range': self.age_range.value if self.age_range else None,
            'life_stage': self.life_stage.value if self.life_stage else None,
            'marital_status': self.marital_status.value if self.marital_status else None,
            'has_dependents': self.has_dependents,
            'dependent_count': self.dependent_count,
            'spouse_income': self.spouse_income,
            'state': self.state,
            'cost_of_living_index': self.cost_of_living_index,
            'has_emergency_fund': self.has_emergency_fund,
            'has_retirement_savings': self.has_retirement_savings,
            'has_investment_experience': self.has_investment_experience,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

# API models for PersonalContext
class PersonalContextRead(SQLModel):
    """PersonalContext for API responses."""
    user_id: str
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    marital_status: Optional[MaritalStatus] = None
    has_dependents: bool
    dependent_count: int
    spouse_income: Optional[float] = None
    state: Optional[str] = None
    cost_of_living_index: Optional[float] = None
    has_emergency_fund: bool
    has_retirement_savings: bool
    has_investment_experience: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class PersonalContextCreate(SQLModel):
    """PersonalContext for creation requests."""
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    marital_status: Optional[MaritalStatus] = None
    has_dependents: bool = False
    dependent_count: int = Field(default=0, ge=0)
    spouse_income: Optional[float] = Field(default=None, ge=0)
    state: Optional[str] = Field(default=None, max_length=2)
    cost_of_living_index: Optional[float] = Field(default=None, ge=0)
    has_emergency_fund: bool = False
    has_retirement_savings: bool = False
    has_investment_experience: bool = False

class PersonalContextUpdate(SQLModel):
    """PersonalContext for update requests."""
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    marital_status: Optional[MaritalStatus] = None
    has_dependents: Optional[bool] = None
    dependent_count: Optional[int] = Field(default=None, ge=0)
    spouse_income: Optional[float] = Field(default=None, ge=0)
    state: Optional[str] = Field(default=None, max_length=2)
    cost_of_living_index: Optional[float] = Field(default=None, ge=0)
    has_emergency_fund: Optional[bool] = None
    has_retirement_savings: Optional[bool] = None
    has_investment_experience: Optional[bool] = None
