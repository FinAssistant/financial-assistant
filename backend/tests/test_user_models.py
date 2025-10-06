import pytest
import threading
import tempfile
import os

from app.core.database import AsyncUserStorageWrapper
from app.core.sqlmodel_models import PersonalContextCreate, AgeRange, LifeStage, MaritalStatus
# For testing, we'll use the new SQLite storage


class TestSQLiteUserStorage:
    """Test cases for SQLite UserStorage (formerly InMemoryUserStorage)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use test database to avoid conflicts
        import os
        self.test_db_path = os.path.join(tempfile.gettempdir(), "test_financial_assistant.db")
        self.storage = AsyncUserStorageWrapper()
        # Override database URL for testing
        self.storage._async_storage.database_url = f"sqlite+aiosqlite:///{self.test_db_path}"
        
        # Clean database before each test
        self.storage.clear_all_users()
        
        # Test data setup
        self.test_user_data = {
            'id': 'user123',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'name': 'Test User'
        }
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
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

    def test_get_user_context(self):
        """Test getting complete user context including demographics."""
        # Create user
        self.storage.create_user(self.test_user_data)

        # Get user context
        context = self.storage.get_user_context('user123')

        # Verify basic structure
        assert context['user_id'] == 'user123'
        assert context['name'] == 'Test User'
        assert context['email'] == 'test@example.com'
        assert context['profile_complete'] is False
        assert 'demographics' in context
        assert 'financial_context' in context

        # Without personal context, these should be empty
        assert context['demographics'] == {}
        assert context['financial_context'] == {}

    def test_get_user_context_nonexistent(self):
        """Test getting context for non-existent user."""
        context = self.storage.get_user_context('nonexistent')
        assert context == {}

    def test_get_user_context_with_personal_demographics(self):
        """Test getting user context including personal demographics."""
        # Create user
        self.storage.create_user(self.test_user_data)

        # Create personal context
        personal_data = PersonalContextCreate(
            age_range=AgeRange.RANGE_26_35,
            life_stage=LifeStage.EARLY_CAREER,
            marital_status=MaritalStatus.SINGLE,
            total_dependents_count=0,
            children_count=0,
            occupation_type="Software Engineer",
            location_context="California, USA"
        )
        self.storage.create_personal_context("user123", personal_data)

        # Get user context
        context = self.storage.get_user_context('user123')

        # Verify complete context
        assert context['user_id'] == 'user123'
        assert context['name'] == 'Test User'
        assert context['demographics']['age_range'] == '26_35'
        assert context['demographics']['life_stage'] == 'early_career'
        assert context['demographics']['marital_status'] == 'single'
        assert context['demographics']['occupation_type'] == 'Software Engineer'
        assert context['demographics']['location'] == 'California, USA'
        assert not context['financial_context']['has_dependents']
        assert context['financial_context']['dependent_count'] == 0
        assert context['financial_context']['children_count'] == 0

    def test_get_personal_context_only(self):
        """Test getting personal context without full user context."""
        # Create user
        self.storage.create_user(self.test_user_data)

        # Create personal context
        personal_data = PersonalContextCreate(
            age_range=AgeRange.RANGE_26_35,
            life_stage=LifeStage.EARLY_CAREER,
            marital_status=MaritalStatus.SINGLE
        )
        self.storage.create_personal_context("user123", personal_data)

        # Get personal context only
        context = self.storage.get_personal_context('user123')

        assert context is not None
        assert context['user_id'] == 'user123'
        assert context['age_range'] == '26_35'
        assert context['life_stage'] == 'early_career'
        assert context['marital_status'] == 'single'