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
    """Age ranges for demographic categorization and app routing logic"""
    UNDER_18 = "under_18"
    RANGE_18_25 = "18_25"
    RANGE_26_35 = "26_35"
    RANGE_36_45 = "36_45"
    RANGE_46_55 = "46_55"
    RANGE_56_65 = "56_65"
    OVER_65 = "over_65"

class LifeStage(str, Enum):
    """Life stages that affect financial planning approach and app features"""
    STUDENT = "student"
    YOUNG_PROFESSIONAL = "young_professional"
    EARLY_CAREER = "early_career"
    ESTABLISHED_CAREER = "established_career"
    FAMILY_BUILDING = "family_building"
    PEAK_EARNING = "peak_earning"
    PRE_RETIREMENT = "pre_retirement"
    RETIREMENT = "retirement"

class MaritalStatus(str, Enum):
    """Legal marital status - affects tax planning and joint account handling"""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    DOMESTIC_PARTNERSHIP = "domestic_partnership"

class FamilyStructure(str, Enum):
    """Family structure affects emergency fund needs and financial planning complexity"""
    SINGLE_NO_DEPENDENTS = "single_no_dependents"
    SINGLE_WITH_DEPENDENTS = "single_with_dependents"
    MARRIED_DUAL_INCOME = "married_dual_income"
    MARRIED_SINGLE_INCOME = "married_single_income"
    MARRIED_NO_INCOME = "married_no_income"
    DOMESTIC_PARTNERSHIP = "domestic_partnership"
    DIVORCED_SHARED_CUSTODY = "divorced_shared_custody"
    DIVORCED_SOLE_CUSTODY = "divorced_sole_custody"

class EducationLevel(str, Enum):
    """Education levels for dependents - affects education cost calculations"""
    PRESCHOOL = "preschool"        # 3-5 years
    ELEMENTARY = "elementary"      # 6-10 years  
    MIDDLE_SCHOOL = "middle_school" # 11-13 years
    HIGH_SCHOOL = "high_school"    # 14-18 years
    COLLEGE_BOUND = "college_bound" # Planning for college
    COLLEGE_CURRENT = "college_current" # Currently in college
    POST_GRADUATE = "post_graduate"

class CaregivingResponsibility(str, Enum):
    """Caregiving responsibilities affect available financial resources"""
    NONE = "none"
    AGING_PARENTS = "aging_parents"
    DISABLED_FAMILY_MEMBER = "disabled_family_member"
    BOTH_CHILDREN_AND_PARENTS = "sandwich_generation"

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
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserModel':
        """
        Create UserModel from dictionary data.
        Maintains compatibility with existing code.
        """
        core_fields = {'id', 'email', 'password_hash', 'name', 'profile_complete', 'created_at', 'updated_at'}
        
        # Extract only core fields that exist in the UserModel
        core_data = {k: v for k, v in data.items() if k in core_fields}
        
        return cls(**core_data)
    
    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        Update model from dictionary updates.
        Maintains backward compatibility.
        """
        # Only update core fields that exist in UserModel
        allowed_fields = {'name', 'profile_complete'}
        
        for field in allowed_fields:
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

# Spouse and Dependent models for structured family data
class SpouseBasicInfoModel(SQLModel, table=True):
    """Minimal spouse information - financial details live in Graphiti relationships"""
    __tablename__ = "spouse_basic_info"
    
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    name: Optional[str] = Field(default=None, max_length=255)
    age_range: Optional[AgeRange] = None
    employment_status: Optional[str] = Field(default=None, max_length=100)
    
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

class DependentModel(SQLModel, table=True):
    """Minimal dependent info - financial details live in Graphiti"""
    __tablename__ = "dependents"
    
    id: str = Field(primary_key=True, max_length=255)
    user_id: str = Field(foreign_key="users.id")
    relationship: str = Field(max_length=50)  # "child", "stepchild", "parent", "sibling", etc.
    age: Optional[int] = Field(default=None, ge=0, le=120)
    age_range: Optional[AgeRange] = None  # If exact age not disclosed
    education_level: Optional[EducationLevel] = None  # Drives cost calculations
    special_needs: bool = Field(default=False)  # Boolean flag affects planning complexity
    
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

# PersonalContext model for structured demographic data
class PersonalContextModel(SQLModel, table=True):
    """
    Core demographic and family structure - financial details in Graphiti.
    Matches the architecture defined in data-models.md.
    """
    __tablename__ = "personal_context"
    
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    
    # Basic Demographics (affect app routing and cost-of-living calculations)
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    occupation_type: Optional[str] = Field(default=None, max_length=100)  # Basic categorization for context
    location_context: Optional[str] = Field(default=None, max_length=500)  # Affects cost of living calculations
    
    # Family Structure (affects planning complexity and emergency fund needs)
    family_structure: Optional[FamilyStructure] = None
    marital_status: Optional[MaritalStatus] = None
    
    # Dependents (basic info for app logic) - relationships to other tables
    total_dependents_count: int = Field(default=0, ge=0)  # Quick reference for calculations
    children_count: int = Field(default=0, ge=0)  # Quick reference for calculations
    
    # Caregiving responsibilities (affects available resources) - stored as JSON array
    caregiving_responsibilities: Optional[str] = Field(default=None, max_length=500)  # JSON array of CaregivingResponsibility values
    
    # Completion tracking - single source of truth for profile completion
    is_complete: bool = Field(default=False, description="True only after demographic data + Plaid account linking")

    # NOTE: Detailed financial info lives in Graphiti:
    # - Housing costs and moving plans
    # - Joint vs separate finances
    # - Life event planning and timelines
    # - Dependent support amounts and education costs

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
            'occupation_type': self.occupation_type,
            'location_context': self.location_context,
            'family_structure': self.family_structure.value if self.family_structure else None,
            'marital_status': self.marital_status.value if self.marital_status else None,
            'total_dependents_count': self.total_dependents_count,
            'children_count': self.children_count,
            'caregiving_responsibilities': self.caregiving_responsibilities,
            'is_complete': self.is_complete,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

# API models for PersonalContext
class PersonalContextRead(SQLModel):
    """PersonalContext for API responses."""
    user_id: str
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    occupation_type: Optional[str] = None
    location_context: Optional[str] = None
    family_structure: Optional[FamilyStructure] = None
    marital_status: Optional[MaritalStatus] = None
    total_dependents_count: int
    children_count: int
    caregiving_responsibilities: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class PersonalContextCreate(SQLModel):
    """PersonalContext for creation requests."""
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    occupation_type: Optional[str] = Field(default=None, max_length=100)
    location_context: Optional[str] = Field(default=None, max_length=500)
    family_structure: Optional[FamilyStructure] = None
    marital_status: Optional[MaritalStatus] = None
    total_dependents_count: int = Field(default=0, ge=0)
    children_count: int = Field(default=0, ge=0)
    caregiving_responsibilities: Optional[str] = Field(default=None, max_length=500)

class PersonalContextUpdate(SQLModel):
    """PersonalContext for update requests."""
    age_range: Optional[AgeRange] = None
    life_stage: Optional[LifeStage] = None
    occupation_type: Optional[str] = Field(default=None, max_length=100)
    location_context: Optional[str] = Field(default=None, max_length=500)
    family_structure: Optional[FamilyStructure] = None
    marital_status: Optional[MaritalStatus] = None
    total_dependents_count: Optional[int] = Field(default=None, ge=0)
    children_count: Optional[int] = Field(default=None, ge=0)
    caregiving_responsibilities: Optional[str] = Field(default=None, max_length=500)

# Connected Account models for Plaid integration
class ConnectedAccountModel(SQLModel, table=True):
    """
    Connected bank account information with encrypted Plaid tokens.
    Stores essential account data for conversation context and secure token management.
    """
    __tablename__ = "connected_accounts"

    id: str = Field(primary_key=True, max_length=255)  # Unique account identifier
    user_id: str = Field(foreign_key="users.id", index=True)
    plaid_account_id: str = Field(max_length=255, index=True)  # Plaid's account identifier
    plaid_item_id: str = Field(max_length=255, index=True)  # Plaid's item identifier
    encrypted_access_token: str = Field(max_length=1000)  # Encrypted Plaid access token

    # Account display information
    account_name: str = Field(max_length=255)  # Account nickname/name
    account_type: str = Field(max_length=100)  # checking, savings, credit, etc.
    account_subtype: Optional[str] = Field(default=None, max_length=100)  # More specific type
    institution_name: str = Field(max_length=255)  # Bank/institution name
    institution_id: str = Field(max_length=255)  # Plaid institution identifier

    # Account status and metadata
    is_active: bool = Field(default=True)  # Whether account is still connected
    last_sync_at: Optional[datetime] = Field(default=None)  # Last successful data sync

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
        """Convert to dictionary for agent consumption (excludes sensitive data)."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plaid_account_id': self.plaid_account_id,
            'plaid_item_id': self.plaid_item_id,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'account_subtype': self.account_subtype,
            'institution_name': self.institution_name,
            'institution_id': self.institution_id,
            'is_active': self.is_active,
            'last_sync_at': self.last_sync_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def to_conversation_context(self) -> Dict[str, Any]:
        """Convert to lightweight format for conversation context."""
        return {
            'id': self.id,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'institution_name': self.institution_name,
            'is_active': self.is_active
        }

# API models for ConnectedAccount
class ConnectedAccountRead(SQLModel):
    """ConnectedAccount for API responses."""
    id: str
    user_id: str
    plaid_account_id: str
    plaid_item_id: str
    account_name: str
    account_type: str
    account_subtype: Optional[str] = None
    institution_name: str
    institution_id: str
    is_active: bool
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ConnectedAccountCreate(SQLModel):
    """ConnectedAccount for creation requests."""
    plaid_account_id: str = Field(max_length=255)
    plaid_item_id: str = Field(max_length=255)
    encrypted_access_token: str = Field(max_length=1000)
    account_name: str = Field(max_length=255)
    account_type: str = Field(max_length=100)
    account_subtype: Optional[str] = Field(default=None, max_length=100)
    institution_name: str = Field(max_length=255)
    institution_id: str = Field(max_length=255)

class ConnectedAccountUpdate(SQLModel):
    """ConnectedAccount for update requests."""
    account_name: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
    last_sync_at: Optional[datetime] = None
