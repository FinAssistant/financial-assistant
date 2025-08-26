import pytest
from datetime import datetime
import threading
import time

from app.models.user import User
from app.core.database import InMemoryUserStorage


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            id="user123",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.profile_complete is False
        assert user.name is None
        assert isinstance(user.created_at, datetime)
    
    def test_user_with_optional_fields(self):
        """Test user creation with optional fields."""
        created_at = datetime(2024, 1, 1)
        
        user = User(
            id="user123",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            profile_complete=True,
            created_at=created_at
        )
        
        assert user.name == "Test User"
        assert user.profile_complete is True
        assert user.created_at == created_at
    
    def test_to_dict(self):
        """Test converting user to dictionary."""
        created_at = datetime(2024, 1, 1)
        
        user = User(
            id="user123",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            created_at=created_at
        )
        
        user_dict = user.to_dict()
        
        assert user_dict == {
            'id': "user123",
            'email': "test@example.com",
            'password_hash': "hashed_password",
            'name': "Test User",
            'profile_complete': False,
            'created_at': created_at
        }
    
    def test_from_dict(self):
        """Test creating user from dictionary."""
        created_at = datetime(2024, 1, 1)
        
        user_data = {
            'id': "user123",
            'email': "test@example.com",
            'password_hash': "hashed_password",
            'name': "Test User",
            'profile_complete': True,
            'created_at': created_at
        }
        
        user = User.from_dict(user_data)
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.name == "Test User"
        assert user.profile_complete is True
        assert user.created_at == created_at
    
    def test_from_dict_missing_optional_fields(self):
        """Test creating user from dictionary with missing optional fields."""
        user_data = {
            'id': "user123",
            'email': "test@example.com",
            'password_hash': "hashed_password"
        }
        
        user = User.from_dict(user_data)
        
        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.name is None
        assert user.profile_complete is False
        assert isinstance(user.created_at, datetime)
    
    def test_to_public_dict(self):
        """Test converting user to public dictionary (no sensitive data)."""
        created_at = datetime(2024, 1, 1)
        
        user = User(
            id="user123",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            created_at=created_at
        )
        
        public_dict = user.to_public_dict()
        
        assert public_dict == {
            'id': "user123",
            'email': "test@example.com",
            'name': "Test User",
            'profile_complete': False,
            'created_at': created_at
        }
        
        # Ensure password_hash is not included
        assert 'password_hash' not in public_dict


class TestInMemoryUserStorage:
    """Test cases for InMemoryUserStorage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.storage = InMemoryUserStorage()
        self.test_user_data = {
            'id': 'user123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'name': 'Test User'
        }
    
    def test_create_user_success(self):
        """Test successful user creation."""
        user = self.storage.create_user(self.test_user_data)
        
        assert user['id'] == 'user123'
        assert user['email'] == 'test@example.com'
        assert user['password_hash'] == 'hashed_password'
        assert user['name'] == 'Test User'
        assert user['profile_complete'] is False
        assert 'created_at' in user
    
    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email."""
        self.storage.create_user(self.test_user_data)
        
        duplicate_user = {
            'id': 'user456',
            'email': 'test@example.com',  # Same email
            'password_hash': 'different_hash'
        }
        
        with pytest.raises(ValueError, match="already exists"):
            self.storage.create_user(duplicate_user)
    
    def test_create_user_missing_required_fields(self):
        """Test creating user with missing required fields."""
        # Missing id
        with pytest.raises(ValueError, match="must include 'id'"):
            self.storage.create_user({
                'email': 'test@example.com',
                'password_hash': 'hashed_password'
            })
        
        # Missing email
        with pytest.raises(ValueError, match="must include 'email'"):
            self.storage.create_user({
                'id': 'user123',
                'password_hash': 'hashed_password'
            })
        
        # Missing password_hash
        with pytest.raises(ValueError, match="must include 'password_hash'"):
            self.storage.create_user({
                'id': 'user123',
                'email': 'test@example.com'
            })
    
    def test_user_exists(self):
        """Test checking if user exists."""
        assert self.storage.user_exists('test@example.com') is False
        
        self.storage.create_user(self.test_user_data)
        
        assert self.storage.user_exists('test@example.com') is True
        assert self.storage.user_exists('TEST@EXAMPLE.COM') is True  # Case insensitive
        assert self.storage.user_exists('nonexistent@example.com') is False
    
    def test_get_user_by_id(self):
        """Test getting user by ID."""
        assert self.storage.get_user_by_id('user123') is None
        
        self.storage.create_user(self.test_user_data)
        
        user = self.storage.get_user_by_id('user123')
        assert user is not None
        assert user['email'] == 'test@example.com'
        
        assert self.storage.get_user_by_id('nonexistent') is None
    
    def test_get_user_by_email(self):
        """Test getting user by email."""
        assert self.storage.get_user_by_email('test@example.com') is None
        
        self.storage.create_user(self.test_user_data)
        
        user = self.storage.get_user_by_email('test@example.com')
        assert user is not None
        assert user['id'] == 'user123'
        
        # Test case insensitive
        user = self.storage.get_user_by_email('TEST@EXAMPLE.COM')
        assert user is not None
        assert user['id'] == 'user123'
        
        assert self.storage.get_user_by_email('nonexistent@example.com') is None
    
    def test_update_user_success(self):
        """Test successful user update."""
        self.storage.create_user(self.test_user_data)
        
        updates = {
            'name': 'Updated Name',
            'profile_complete': True
        }
        
        updated_user = self.storage.update_user('user123', updates)
        
        assert updated_user is not None
        assert updated_user['name'] == 'Updated Name'
        assert updated_user['profile_complete'] is True
        assert updated_user['email'] == 'test@example.com'  # Unchanged
    
    def test_update_user_not_found(self):
        """Test updating non-existent user."""
        result = self.storage.update_user('nonexistent', {'name': 'New Name'})
        assert result is None
    
    def test_update_user_forbidden_fields(self):
        """Test updating forbidden fields."""
        self.storage.create_user(self.test_user_data)
        
        forbidden_updates = [
            {'id': 'new_id'},
            {'email': 'new@example.com'},
            {'password_hash': 'new_hash'}
        ]
        
        for update in forbidden_updates:
            with pytest.raises(ValueError, match="Cannot update fields"):
                self.storage.update_user('user123', update)
    
    def test_delete_user_success(self):
        """Test successful user deletion."""
        self.storage.create_user(self.test_user_data)
        
        assert self.storage.user_exists('test@example.com') is True
        
        result = self.storage.delete_user('user123')
        assert result is True
        
        assert self.storage.user_exists('test@example.com') is False
        assert self.storage.get_user_by_id('user123') is None
    
    def test_delete_user_not_found(self):
        """Test deleting non-existent user."""
        result = self.storage.delete_user('nonexistent')
        assert result is False
    
    def test_list_all_users(self):
        """Test listing all users."""
        assert self.storage.list_all_users() == []
        
        # Create multiple users
        self.storage.create_user(self.test_user_data)
        
        user2_data = {
            'id': 'user456',
            'email': 'user2@example.com',
            'password_hash': 'hash2'
        }
        self.storage.create_user(user2_data)
        
        all_users = self.storage.list_all_users()
        assert len(all_users) == 2
        
        emails = [user['email'] for user in all_users]
        assert 'test@example.com' in emails
        assert 'user2@example.com' in emails
    
    def test_get_user_count(self):
        """Test getting user count."""
        assert self.storage.get_user_count() == 0
        
        self.storage.create_user(self.test_user_data)
        assert self.storage.get_user_count() == 1
        
        user2_data = {
            'id': 'user456',
            'email': 'user2@example.com',
            'password_hash': 'hash2'
        }
        self.storage.create_user(user2_data)
        assert self.storage.get_user_count() == 2
        
        self.storage.delete_user('user123')
        assert self.storage.get_user_count() == 1
    
    def test_clear_all_users(self):
        """Test clearing all users."""
        self.storage.create_user(self.test_user_data)
        assert self.storage.get_user_count() == 1
        
        self.storage.clear_all_users()
        assert self.storage.get_user_count() == 0
        assert self.storage.list_all_users() == []
    
    def test_create_user_profile(self):
        """Test creating user profile."""
        self.storage.create_user(self.test_user_data)
        
        profile_data = {
            'name': 'Updated Profile Name',
            'bio': 'User biography'
        }
        
        updated_user = self.storage.create_user_profile('user123', profile_data)
        
        assert updated_user is not None
        assert updated_user['name'] == 'Updated Profile Name'
        assert updated_user['bio'] == 'User biography'
        assert updated_user['profile_complete'] is True
    
    def test_create_user_profile_not_found(self):
        """Test creating profile for non-existent user."""
        result = self.storage.create_user_profile('nonexistent', {'name': 'Test'})
        assert result is None
    
    def test_search_users_by_name(self):
        """Test searching users by name."""
        # Create test users
        users = [
            {'id': 'user1', 'email': 'user1@example.com', 'password_hash': 'hash1', 'name': 'John Smith'},
            {'id': 'user2', 'email': 'user2@example.com', 'password_hash': 'hash2', 'name': 'Jane Doe'},
            {'id': 'user3', 'email': 'user3@example.com', 'password_hash': 'hash3', 'name': 'John Johnson'},
            {'id': 'user4', 'email': 'user4@example.com', 'password_hash': 'hash4'}  # No name
        ]
        
        for user_data in users:
            self.storage.create_user(user_data)
        
        # Search for "John"
        results = self.storage.search_users_by_name('John')
        assert len(results) == 2
        names = [user['name'] for user in results]
        assert 'John Smith' in names
        assert 'John Johnson' in names
        
        # Case insensitive search
        results = self.storage.search_users_by_name('jane')
        assert len(results) == 1
        assert results[0]['name'] == 'Jane Doe'
        
        # No matches
        results = self.storage.search_users_by_name('NonExistent')
        assert len(results) == 0
        
        # Empty query
        results = self.storage.search_users_by_name('')
        assert len(results) == 3  # All users with names
    
    def test_thread_safety(self):
        """Test thread safety of storage operations."""
        num_threads = 10
        users_per_thread = 5
        threads = []
        
        def create_users(thread_id):
            for i in range(users_per_thread):
                user_data = {
                    'id': f'user_{thread_id}_{i}',
                    'email': f'user_{thread_id}_{i}@example.com',
                    'password_hash': f'hash_{thread_id}_{i}'
                }
                try:
                    self.storage.create_user(user_data)
                except ValueError:
                    # Expected for duplicate emails in concurrent scenarios
                    pass
        
        # Start threads
        for thread_id in range(num_threads):
            thread = threading.Thread(target=create_users, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify data integrity
        total_users = self.storage.get_user_count()
        assert total_users == num_threads * users_per_thread
        
        all_users = self.storage.list_all_users()
        assert len(all_users) == total_users
        
        # Verify no duplicate emails
        emails = [user['email'] for user in all_users]
        assert len(emails) == len(set(emails))  # All emails should be unique