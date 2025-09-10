"""
Tests for UserContextDAO - SQLite context retrieval for agents.
Includes both unit tests (mocked) and integration tests (real database).
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.services.user_context_dao import UserContextDAO, UserContextDAOSync
from app.core.sqlmodel_models import UserModel, PersonalContextModel, AgeRange, LifeStage, MaritalStatus
from sqlmodel import SQLModel

class TestUserContextDAO:
    """Test the async UserContextDAO class."""
    
    @pytest.fixture
    def dao(self):
        """Create a UserContextDAO instance for testing."""
        return UserContextDAO()
    
    @pytest.fixture
    def mock_user_model(self):
        """Mock UserModel for testing."""
        user = Mock(spec=UserModel)
        user.id = "user-123"
        user.name = "John Doe"
        user.email = "john@example.com"
        user.profile_complete = True
        user.created_at = datetime.now(timezone.utc)
        return user
    
    @pytest.fixture
    def mock_personal_context_model(self):
        """Mock PersonalContextModel for testing."""
        context = Mock(spec=PersonalContextModel)
        context.user_id = "user-123"
        context.age_range = AgeRange.RANGE_25_34
        context.life_stage = LifeStage.EARLY_CAREER
        context.marital_status = MaritalStatus.SINGLE
        context.has_dependents = False
        context.dependent_count = 0
        context.spouse_income = None
        context.state = "CA"
        context.cost_of_living_index = 120.5
        context.has_emergency_fund = True
        context.has_retirement_savings = False
        context.has_investment_experience = True
        context.created_at = datetime.now(timezone.utc)
        context.updated_at = None
        
        # Mock the to_dict method
        context.to_dict.return_value = {
            'user_id': 'user-123',
            'age_range': '25_34',
            'life_stage': 'early_career',
            'marital_status': 'single',
            'has_dependents': False,
            'dependent_count': 0,
            'spouse_income': None,
            'state': 'CA',
            'cost_of_living_index': 120.5,
            'has_emergency_fund': True,
            'has_retirement_savings': False,
            'has_investment_experience': True,
            'created_at': context.created_at,
            'updated_at': None
        }
        
        return context
    
    @pytest.mark.asyncio
    async def test_get_user_context_with_complete_data(self, dao, mock_user_model, mock_personal_context_model):
        """Test getting user context with both user and personal context data."""
        # Mock the database session and query result
        with patch.object(dao._storage, '_ensure_initialized', new_callable=AsyncMock), \
             patch.object(dao._storage, 'session_factory') as mock_session_factory:
            
            # Setup mock session context manager
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            # Mock the query result - first() should return actual values, not coroutines
            mock_result = Mock()
            mock_result.first.return_value = (mock_user_model, mock_personal_context_model)
            mock_session.execute.return_value = mock_result
            
            # Call the method
            result = await dao.get_user_context("user-123")
            
            # Verify the result
            assert result["user_id"] == "user-123"
            assert result["name"] == "John Doe"
            assert result["email"] == "john@example.com"
            assert result["profile_complete"] == True
            
            # Check demographics mapping
            assert result["demographics"]["age_range"] == "25_34"
            assert result["demographics"]["life_stage"] == "early_career"
            assert result["demographics"]["marital_status"] == "single"
            assert result["demographics"]["location"] == "CA"
            assert result["demographics"]["cost_of_living_index"] == 120.5
            
            # Check financial context mapping
            assert result["financial_context"]["has_emergency_fund"] == True
            assert result["financial_context"]["has_retirement_savings"] == False
            assert result["financial_context"]["has_investment_experience"] == True
            assert result["financial_context"]["has_dependents"] == False
            assert result["financial_context"]["dependent_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_user_context_user_only(self, dao, mock_user_model):
        """Test getting user context with only user data, no personal context."""
        with patch.object(dao._storage, '_ensure_initialized', new_callable=AsyncMock), \
             patch.object(dao._storage, 'session_factory') as mock_session_factory:
            
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            # Return user but no personal context (None)
            mock_result = Mock()
            mock_result.first.return_value = (mock_user_model, None)
            mock_session.execute.return_value = mock_result
            
            result = await dao.get_user_context("user-123")
            
            # Verify basic user data is present
            assert result["user_id"] == "user-123"
            assert result["name"] == "John Doe"
            assert result["email"] == "john@example.com"
            assert result["profile_complete"] == True
            
            # Verify empty context sections
            assert result["demographics"] == {}
            assert result["financial_context"] == {}
    
    @pytest.mark.asyncio
    async def test_get_user_context_user_not_found(self, dao):
        """Test getting user context when user doesn't exist."""
        with patch.object(dao._storage, '_ensure_initialized', new_callable=AsyncMock), \
             patch.object(dao._storage, 'session_factory') as mock_session_factory:
            
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            # Return None for user not found
            mock_result = Mock()
            mock_result.first.return_value = None
            mock_session.execute.return_value = mock_result
            
            result = await dao.get_user_context("nonexistent-user")
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_basic_user_info(self, dao):
        """Test getting basic user info only."""
        mock_user_data = {
            "id": "user-123",
            "email": "john@example.com",
            "name": "John Doe",
            "profile_complete": True
        }
        
        with patch.object(dao._storage, 'get_user_by_id', new_callable=AsyncMock, return_value=mock_user_data):
            result = await dao.get_basic_user_info("user-123")
            assert result == mock_user_data
    
    @pytest.mark.asyncio
    async def test_get_personal_context(self, dao, mock_personal_context_model):
        """Test getting personal context only."""
        with patch.object(dao._storage, '_ensure_initialized', new_callable=AsyncMock), \
             patch.object(dao._storage, 'session_factory') as mock_session_factory:
            
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session_factory.return_value.__aexit__.return_value = None
            
            mock_result = Mock()
            mock_result.first.return_value = (mock_personal_context_model,)
            mock_session.execute.return_value = mock_result
            
            result = await dao.get_personal_context("user-123")
            
            # Should return the to_dict() result
            expected = mock_personal_context_model.to_dict.return_value
            assert result == expected

class TestUserContextDAOSync:
    """Test the synchronous UserContextDAOSync wrapper."""
    
    @pytest.fixture
    def dao_sync(self):
        """Create a UserContextDAOSync instance for testing."""
        return UserContextDAOSync()
    
    def test_get_user_context_sync(self, dao_sync):
        """Test synchronous user context retrieval."""
        mock_context = {
            "user_id": "user-123",
            "name": "John Doe",
            "email": "john@example.com",
            "profile_complete": True,
            "demographics": {"age_range": "25_34"},
            "financial_context": {"has_emergency_fund": True}
        }
        
        with patch.object(dao_sync._async_dao, 'get_user_context', new_callable=AsyncMock, return_value=mock_context):
            result = dao_sync.get_user_context("user-123")
            assert result == mock_context
    
    def test_get_basic_user_info_sync(self, dao_sync):
        """Test synchronous basic user info retrieval."""
        mock_user_data = {
            "id": "user-123",
            "email": "john@example.com",
            "name": "John Doe"
        }
        
        with patch.object(dao_sync._async_dao, 'get_basic_user_info', new_callable=AsyncMock, return_value=mock_user_data):
            result = dao_sync.get_basic_user_info("user-123")
            assert result == mock_user_data
    
    def test_get_personal_context_sync(self, dao_sync):
        """Test synchronous personal context retrieval."""
        mock_personal_data = {
            "user_id": "user-123",
            "age_range": "25_34",
            "has_emergency_fund": True
        }
        
        with patch.object(dao_sync._async_dao, 'get_personal_context', new_callable=AsyncMock, return_value=mock_personal_data):
            result = dao_sync.get_personal_context("user-123")
            assert result == mock_personal_data
    
    def test_run_async_no_event_loop(self, dao_sync):
        """Test _run_async when no event loop exists."""
        async def dummy_coro():
            return "test_result"
        
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No event loop")), \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop:
            
            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            mock_loop.run_until_complete.return_value = "test_result"
            
            result = dao_sync._run_async(dummy_coro())
            
            assert result == "test_result"
            mock_new_loop.assert_called_once()
            mock_set_loop.assert_called()
            mock_loop.close.assert_called_once()

class TestIntegration:
    """Integration tests for UserContextDAO with real database interactions."""
    
    @pytest.fixture
    async def temp_database(self):
        """Create a temporary SQLite database for testing."""
        # Create temporary file
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        # Create engine with the temp database
        database_url = f"sqlite+aiosqlite:///{temp_db.name}"
        engine = create_async_engine(database_url, echo=False)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        yield engine, database_url
        
        # Cleanup
        await engine.dispose()
        os.unlink(temp_db.name)
    
    @pytest.fixture
    async def populated_database(self, temp_database):
        """Create and populate test database with sample data."""
        engine, database_url = temp_database
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        async with session_factory() as session:
            # Create test user
            user = UserModel(
                id="test-user-123",
                email="testuser@example.com",
                name="John Doe",
                password_hash="hashed_password",
                profile_complete=True,
                created_at=datetime.now(timezone.utc)
            )
            session.add(user)
            
            # Create personal context
            personal_context = PersonalContextModel(
                user_id="test-user-123",
                age_range=AgeRange.RANGE_25_34,
                life_stage=LifeStage.EARLY_CAREER,
                marital_status=MaritalStatus.SINGLE,
                has_dependents=False,
                dependent_count=0,
                spouse_income=None,
                state="CA",
                cost_of_living_index=120.5,
                has_emergency_fund=True,
                has_retirement_savings=False,
                has_investment_experience=True
            )
            session.add(personal_context)
            
            # Create user without personal context
            user_no_context = UserModel(
                id="user-no-context",
                email="nocontext@example.com",
                name="Jane Smith",
                password_hash="hashed_password",
                profile_complete=False,
                created_at=datetime.now(timezone.utc)
            )
            session.add(user_no_context)
            
            await session.commit()
        
        yield engine, database_url
    
    @pytest.fixture
    async def edge_case_database(self):
        """Create database with edge case data."""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        database_url = f"sqlite+aiosqlite:///{temp_db.name}"
        engine = create_async_engine(database_url, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        async with session_factory() as session:
            # User with minimal data
            minimal_user = UserModel(
                id="minimal-user",
                email="minimal@example.com",
                name="",  # Empty name
                password_hash="hash",
                profile_complete=False
            )
            session.add(minimal_user)
            
            # Personal context with null values
            minimal_context = PersonalContextModel(
                user_id="minimal-user",
                age_range=None,
                life_stage=None,
                marital_status=None,
                has_dependents=False,
                dependent_count=0,
                state=None,
                cost_of_living_index=None,
                has_emergency_fund=False,
                has_retirement_savings=False,
                has_investment_experience=False
            )
            session.add(minimal_context)
            
            await session.commit()
        
        yield engine, database_url
        
        await engine.dispose()
        os.unlink(temp_db.name)
    
    def test_context_structure_matches_agent_expectations(self):
        """Test that the context structure matches what the SpendingAgent expects."""
        # This test verifies the contract between DAO and Agent
        expected_structure = {
            "user_id": str,
            "name": str,
            "email": str,
            "profile_complete": bool,
            "demographics": dict,
            "financial_context": dict
        }
        
        # Test with mock data to verify structure
        mock_context = {
            "user_id": "test-user",
            "name": "Test User",
            "email": "test@example.com", 
            "profile_complete": True,
            "demographics": {
                "age_range": "25_34",
                "life_stage": "early_career",
                "marital_status": "single",
                "location": "CA",
                "cost_of_living_index": 120.5
            },
            "financial_context": {
                "has_emergency_fund": True,
                "has_retirement_savings": False,
                "has_investment_experience": True,
                "has_dependents": False,
                "dependent_count": 0
            }
        }
        
        # Verify all expected keys exist with correct types
        for key, expected_type in expected_structure.items():
            assert key in mock_context
            assert isinstance(mock_context[key], expected_type)
        
        # Verify nested structure for demographics
        demographics_keys = ["age_range", "life_stage", "marital_status", "location", "cost_of_living_index"]
        for key in demographics_keys:
            assert key in mock_context["demographics"]
        
        # Verify nested structure for financial_context
        financial_keys = ["has_emergency_fund", "has_retirement_savings", "has_investment_experience", 
                         "has_dependents", "dependent_count"]
        for key in financial_keys:
            assert key in mock_context["financial_context"]
    
    @pytest.mark.asyncio
    async def test_get_user_context_with_real_database(self, populated_database):
        """Test getting complete user context with real database."""
        engine, database_url = populated_database
        
        # Create DAO with custom storage pointing to our test database
        dao = UserContextDAO()
        dao._storage.database_url = database_url
        dao._storage.engine = engine
        dao._storage.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        dao._storage._initialized = True  # Skip initialization
        
        # Test getting user with complete context
        result = await dao.get_user_context("test-user-123")
        
        # Verify user data
        assert result["user_id"] == "test-user-123"
        assert result["name"] == "John Doe"
        assert result["email"] == "testuser@example.com"
        assert result["profile_complete"] == True
        
        # Verify demographics
        assert result["demographics"]["age_range"] == "25_34"
        assert result["demographics"]["life_stage"] == "early_career"
        assert result["demographics"]["marital_status"] == "single"
        assert result["demographics"]["location"] == "CA"
        assert result["demographics"]["cost_of_living_index"] == 120.5
        
        # Verify financial context
        assert result["financial_context"]["has_emergency_fund"] == True
        assert result["financial_context"]["has_retirement_savings"] == False
        assert result["financial_context"]["has_investment_experience"] == True
        assert result["financial_context"]["has_dependents"] == False
        assert result["financial_context"]["dependent_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_user_context_without_personal_context(self, populated_database):
        """Test getting user context when personal context doesn't exist."""
        engine, database_url = populated_database
        
        dao = UserContextDAO()
        dao._storage.database_url = database_url
        dao._storage.engine = engine
        dao._storage.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        dao._storage._initialized = True
        
        # Test getting user without personal context
        result = await dao.get_user_context("user-no-context")
        
        # Verify user data
        assert result["user_id"] == "user-no-context"
        assert result["name"] == "Jane Smith"
        assert result["email"] == "nocontext@example.com"
        assert result["profile_complete"] == False
        
        # Verify empty context sections
        assert result["demographics"] == {}
        assert result["financial_context"] == {}
    
    @pytest.mark.asyncio
    async def test_get_user_context_nonexistent_user(self, populated_database):
        """Test getting context for user that doesn't exist."""
        engine, database_url = populated_database
        
        dao = UserContextDAO()
        dao._storage.database_url = database_url
        dao._storage.engine = engine
        dao._storage.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        dao._storage._initialized = True
        
        result = await dao.get_user_context("nonexistent-user")
        assert result == {}
    
    def test_sync_wrapper_with_real_database(self, populated_database):
        """Test synchronous wrapper with real database."""
        engine, database_url = populated_database
        
        dao_sync = UserContextDAOSync()
        dao_sync._async_dao._storage.database_url = database_url
        dao_sync._async_dao._storage.engine = engine
        dao_sync._async_dao._storage.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        dao_sync._async_dao._storage._initialized = True
        
        # Test synchronous call
        result = dao_sync.get_user_context("test-user-123")
        
        # Should get same result as async version
        assert result["user_id"] == "test-user-123"
        assert result["name"] == "John Doe"
        assert result["email"] == "testuser@example.com"
        assert result["demographics"]["age_range"] == "25_34"
        assert result["financial_context"]["has_emergency_fund"] == True
    
    @pytest.mark.asyncio
    async def test_minimal_data_handling(self, edge_case_database):
        """Test handling of minimal/null data."""
        engine, database_url = edge_case_database
        
        dao = UserContextDAO()
        dao._storage.database_url = database_url
        dao._storage.engine = engine
        dao._storage.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        dao._storage._initialized = True
        
        result = await dao.get_user_context("minimal-user")
        
        # Should handle empty name gracefully
        assert result["user_id"] == "minimal-user"
        assert result["name"] == "User"  # Default fallback
        assert result["email"] == "minimal@example.com"
        assert result["profile_complete"] == False
        
        # Demographics should be empty for null values
        assert result["demographics"] == {}
        
        # Financial context should still include boolean fields
        assert result["financial_context"]["has_emergency_fund"] == False
        assert result["financial_context"]["has_retirement_savings"] == False
        assert result["financial_context"]["has_investment_experience"] == False
        assert result["financial_context"]["has_dependents"] == False
        assert result["financial_context"]["dependent_count"] == 0
    
    @pytest.mark.asyncio 
    async def test_database_schema_validation(self, edge_case_database):
        """Test that our DAO works with the actual database schema."""
        engine, _ = edge_case_database
        
        # Verify tables were created correctly
        async with engine.connect() as conn:
            # Check users table exists
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
            assert result.fetchone() is not None
            
            # Check personal_context table exists  
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='personal_context'"))
            assert result.fetchone() is not None
            
            # Check foreign key constraint
            result = await conn.execute(text("PRAGMA foreign_key_list(personal_context)"))
            fk_info = result.fetchall()
            assert len(fk_info) > 0  # Should have foreign key to users table
