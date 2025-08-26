from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class User:
    """
    User data model for in-memory storage.
    Represents a user in the financial assistant system.
    """
    id: str
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=datetime.now)
    profile_complete: bool = False
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'profile_complete': self.profile_complete,
            'name': self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user instance from dictionary."""
        return cls(
            id=data['id'],
            email=data['email'],
            password_hash=data['password_hash'],
            created_at=data.get('created_at', datetime.now()),
            profile_complete=data.get('profile_complete', False),
            name=data.get('name')
        )
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert user to public dictionary (without sensitive data)."""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at,
            'profile_complete': self.profile_complete,
            'name': self.name
        }