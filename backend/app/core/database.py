from typing import Dict, Optional, List, Any
from datetime import datetime
import threading

from app.models.user import User


class InMemoryUserStorage:
    """
    In-memory user storage for POC.
    Thread-safe implementation using locks.
    """
    
    def __init__(self):
        self._users_by_id: Dict[str, Dict[str, Any]] = {}
        self._users_by_email: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def user_exists(self, email: str) -> bool:
        """Check if user with given email exists."""
        with self._lock:
            return email.lower() in self._users_by_email
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID. Returns user dict or None if not found."""
        with self._lock:
            return self._users_by_id.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email. Returns user dict or None if not found."""
        with self._lock:
            return self._users_by_email.get(email.lower())
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in storage.
        Returns the created user data.
        Raises ValueError if user with email already exists.
        """
        with self._lock:
            # Ensure required fields
            if 'id' not in user_data:
                raise ValueError("User data must include 'id' field")
            if 'email' not in user_data:
                raise ValueError("User data must include 'email' field")
            if 'password_hash' not in user_data:
                raise ValueError("User data must include 'password_hash' field")
            
            email_lower = user_data['email'].lower()
            
            # Check if user already exists
            if email_lower in self._users_by_email:
                raise ValueError(f"User with email {user_data['email']} already exists")
            
            # Set defaults for optional fields
            user_data_copy = user_data.copy()
            user_data_copy.setdefault('created_at', datetime.now())
            user_data_copy.setdefault('profile_complete', False)
            user_data_copy.setdefault('name', '')
            
            # Store user by both ID and email
            self._users_by_id[user_data_copy['id']] = user_data_copy
            self._users_by_email[email_lower] = user_data_copy
            
            return user_data_copy.copy()
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user data.
        Returns updated user data or None if user not found.
        Cannot update id, email, or password_hash through this method.
        """
        with self._lock:
            if user_id not in self._users_by_id:
                return None
            
            # Prevent updating immutable fields
            forbidden_fields = {'id', 'email', 'password_hash'}
            if any(field in updates for field in forbidden_fields):
                raise ValueError(f"Cannot update fields: {', '.join(forbidden_fields)}")
            
            # Update user data
            user_data = self._users_by_id[user_id]
            user_data.update(updates)
            
            # Update the email index as well
            email_lower = user_data['email'].lower()
            self._users_by_email[email_lower] = user_data
            
            return user_data.copy()
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user by ID.
        Returns True if user was deleted, False if user not found.
        """
        with self._lock:
            if user_id not in self._users_by_id:
                return False
            
            user_data = self._users_by_id[user_id]
            email_lower = user_data['email'].lower()
            
            # Remove from both indexes
            del self._users_by_id[user_id]
            del self._users_by_email[email_lower]
            
            return True
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """Get all users. Returns list of user dictionaries."""
        with self._lock:
            return [user_data.copy() for user_data in self._users_by_id.values()]
    
    def get_user_count(self) -> int:
        """Get total number of users."""
        with self._lock:
            return len(self._users_by_id)
    
    def clear_all_users(self) -> None:
        """Clear all users from storage. Use with caution."""
        with self._lock:
            self._users_by_id.clear()
            self._users_by_email.clear()
    
    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create or update user profile information.
        Marks profile as complete.
        Returns updated user data or None if user not found.
        """
        profile_updates = profile_data.copy()
        profile_updates['profile_complete'] = True
        
        return self.update_user(user_id, profile_updates)
    
    def search_users_by_name(self, name_query: str) -> List[Dict[str, Any]]:
        """
        Search users by name (case-insensitive partial match).
        Returns list of matching user dictionaries.
        """
        with self._lock:
            name_lower = name_query.lower()
            matching_users = []
            
            for user_data in self._users_by_id.values():
                user_name = (user_data.get('name') or '').lower()
                # Skip empty names when searching, unless query is also empty
                if not name_query and not user_name:
                    continue
                if name_lower in user_name:
                    matching_users.append(user_data.copy())
            
            return matching_users


# Global user storage instance
user_storage = InMemoryUserStorage()