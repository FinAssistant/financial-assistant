"""
SQLAlchemy database models for SQLite persistence.
Maintains compatibility with existing in-memory interface.
"""

from datetime import datetime, timezone
from typing import Any, Dict
import json

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, TEXT

Base = declarative_base()


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a JSON-encoded string."""
    
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str:
        """Convert dict to JSON string for storage."""
        if value is not None:
            return json.dumps(value, default=str)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Dict[str, Any]:
        """Convert JSON string back to dict."""
        if value is not None:
            return json.loads(value)
        return {}


class UserModel(Base):
    """
    SQLAlchemy User model that maintains compatibility with existing User interface.
    Maps directly to the current in-memory user dictionary structure.
    """
    __tablename__ = "users"
    
    # Primary fields - match current in-memory structure
    id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), default="")
    
    # Profile completion tracking
    profile_complete = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Extended profile data as JSON (for future expansion)
    profile_data = Column(JSONEncodedDict, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert SQLAlchemy model to dictionary format.
        Maintains exact compatibility with existing in-memory format.
        """
        base_dict = {
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'name': self.name,
            'profile_complete': self.profile_complete,
            'created_at': self.created_at,
        }
        
        # Add any profile data fields
        if self.profile_data:
            base_dict.update(self.profile_data)
            
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserModel':
        """
        Create UserModel from dictionary data.
        Separates core fields from extended profile data.
        """
        core_fields = {'id', 'email', 'password_hash', 'name', 'profile_complete', 'created_at'}
        
        # Extract core fields
        core_data = {k: v for k, v in data.items() if k in core_fields}
        
        # Everything else goes in profile_data
        profile_data = {k: v for k, v in data.items() if k not in core_fields}
        
        return cls(
            **core_data,
            profile_data=profile_data
        )
    
    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        Update model from dictionary updates.
        Maintains separation between core fields and profile data.
        """
        core_fields = {'name', 'profile_complete'}  # Updatable core fields
        
        # Update core fields
        for field in core_fields:
            if field in updates:
                setattr(self, field, updates[field])
        
        # Update profile data
        profile_updates = {k: v for k, v in updates.items() if k not in core_fields}
        if profile_updates:
            current_profile = self.profile_data or {}
            current_profile.update(profile_updates)
            self.profile_data = current_profile
        
        self.updated_at = datetime.now(timezone.utc)


