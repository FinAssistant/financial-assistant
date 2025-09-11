"""
Unit tests for OnboardingAgent.
All external dependencies are mocked for fast, reliable testing.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from app.ai.onboarding import OnboardingAgent, OnboardingState, ProfileDataExtraction


class TestOnboardingState:
    """Test OnboardingState model functionality."""
    
    def test_onboarding_state_creation(self):
        """Test OnboardingState can be created with defaults."""
        state = OnboardingState()
        
        assert state.messages == []
        assert state.profile_context is None
        assert state.profile_context_timestamp is None
        assert state.current_step == "welcome"
        assert state.collected_data == {}
        assert state.needs_database_update is False
        assert state.onboarding_complete is False
    
    def test_onboarding_state_with_data(self):
        """Test OnboardingState with custom data."""
        collected_data = {"age_range": "26_35", "occupation_type": "engineer"}
        
        state = OnboardingState(
            current_step="continue",
            collected_data=collected_data,
            needs_database_update=True,
            onboarding_complete=False
        )
        
        assert state.current_step == "continue"
        assert state.collected_data == collected_data
        assert state.needs_database_update is True
        assert state.onboarding_complete is False


class TestProfileDataExtraction:
    """Test ProfileDataExtraction model functionality."""
    
    def test_profile_data_extraction_defaults(self):
        """Test ProfileDataExtraction with minimal data."""
        extraction = ProfileDataExtraction(
            user_response="Hello! I'd like to help you."
        )
        
        assert extraction.extracted_data == {}
        assert extraction.next_questions == []
        assert extraction.completion_status == "incomplete"
        assert extraction.user_response == "Hello! I'd like to help you."
    
    def test_profile_data_extraction_complete(self):
        """Test ProfileDataExtraction with full data."""
        extracted_data = {"age_range": "26_35", "occupation_type": "engineer"}
        next_questions = ["What is your marital status?", "Do you have dependents?"]
        
        extraction = ProfileDataExtraction(
            extracted_data=extracted_data,
            next_questions=next_questions,
            completion_status="partial",
            user_response="Great! I've noted your age and occupation."
        )
        
        assert extraction.extracted_data == extracted_data
        assert extraction.next_questions == next_questions
        assert extraction.completion_status == "partial"
        assert extraction.user_response == "Great! I've noted your age and occupation."


class TestOnboardingAgentMethods:
    """Test OnboardingAgent individual methods with mocking."""
    
    @pytest.fixture
    def agent(self):
        """Create OnboardingAgent instance for testing."""
        return OnboardingAgent()
    
    @pytest.fixture
    def sample_state(self):
        """Create sample OnboardingState for testing."""
        return OnboardingState(
            messages=[HumanMessage(content="I'm 28 and work as a software engineer")],
            current_step="welcome",
            collected_data={},
            needs_database_update=False,
            onboarding_complete=False
        )
    
    @pytest.fixture
    def sample_config(self):
        """Create sample config for testing."""
        return {
            "configurable": {
                "user_id": "test_user_123",
                "thread_id": "test_thread_456"
            }
        }
    
    @patch('app.ai.onboarding.user_storage')
    def test_read_db_new_user(self, mock_user_storage, agent, sample_state, sample_config):
        """Test _read_db with new user (no existing data)."""
        # Mock database responses
        mock_user_storage.get_user_by_id.return_value = None
        
        result = agent._read_db(sample_state, sample_config)
        
        assert result["collected_data"] == {}
        assert result["current_step"] == "welcome"
        mock_user_storage.get_user_by_id.assert_called_once_with("test_user_123")
    
    @patch('app.ai.onboarding.user_storage')
    def test_read_db_existing_user_with_profile(self, mock_user_storage, agent, sample_state, sample_config):
        """Test _read_db with existing user that has profile data."""
        # Mock database responses
        mock_user_storage.get_user_by_id.return_value = {"id": "test_user_123"}
        mock_user_storage.get_personal_context.return_value = {
            "user_id": "test_user_123",
            "age_range": "26_35",
            "occupation_type": "engineer",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = agent._read_db(sample_state, sample_config)
        
        expected_data = {"age_range": "26_35", "occupation_type": "engineer"}
        assert result["collected_data"] == expected_data
        assert result["current_step"] == "continue"
        mock_user_storage.get_user_by_id.assert_called_once_with("test_user_123")
        mock_user_storage.get_personal_context.assert_called_once_with("test_user_123")
    
    @patch('app.ai.onboarding.user_storage')
    def test_read_db_database_error(self, mock_user_storage, agent, sample_state, sample_config):
        """Test _read_db handles database errors gracefully."""
        # Mock database to raise exception
        mock_user_storage.get_user_by_id.side_effect = Exception("Database error")
        
        result = agent._read_db(sample_state, sample_config)
        
        assert result["collected_data"] == {}
        assert result["current_step"] == "welcome"
    
    @patch('app.ai.onboarding.llm_factory')
    def test_call_llm_basic(self, mock_llm_factory, agent, sample_state, sample_config):
        """Test _call_llm with mocked LLM response."""
        # Mock LLM response
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data={"age_range": "26_35", "occupation_type": "engineer"},
            next_questions=["What is your marital status?"],
            completion_status="partial",
            user_response="Great! I've noted that you're 28 and work as a software engineer."
        )
        
        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response
        
        result = agent._call_llm(sample_state, sample_config)
        
        # Check that AI message was created correctly
        assert "messages" in result
        assert len(result["messages"]) == 1
        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert ai_message.content == "Great! I've noted that you're 28 and work as a software engineer."
        assert ai_message.additional_kwargs["agent"] == "onboarding"
        
        # Check state updates
        expected_collected = {"age_range": "26_35", "occupation_type": "engineer"}
        assert result["collected_data"] == expected_collected
        assert result["needs_database_update"] is True
        assert result["onboarding_complete"] is False
        
        # Verify LLM was called correctly
        mock_llm_factory.create_llm.assert_called_once()
        mock_llm.with_structured_output.assert_called_once()
        mock_structured_llm.invoke.assert_called_once()
    
    @patch('app.ai.onboarding.llm_factory')
    def test_call_llm_completion_complete(self, mock_llm_factory, agent, sample_state, sample_config):
        """Test _call_llm when profile is marked complete."""
        # Mock LLM response indicating completion
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data={"marital_status": "single"},
            next_questions=[],
            completion_status="complete",
            user_response="Perfect! Your profile is now complete."
        )
        
        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response
        
        result = agent._call_llm(sample_state, sample_config)
        
        assert result["onboarding_complete"] is True
        assert result["needs_database_update"] is True
        
        ai_message = result["messages"][0]
        assert ai_message.content == "Perfect! Your profile is now complete."
    
    @patch('app.ai.onboarding.user_storage')
    def test_update_db_no_update_needed(self, mock_user_storage, agent, sample_config):
        """Test _update_db when no database update is needed."""
        state = OnboardingState(needs_database_update=False)
        
        result = agent._update_db(state, sample_config)
        
        assert result == {"needs_database_update": False}
        # Verify no database calls were made
        mock_user_storage.create_or_update_personal_context.assert_not_called()
        mock_user_storage.update_user.assert_not_called()
    
    @patch('app.ai.onboarding.user_storage')
    def test_update_db_with_data(self, mock_user_storage, agent, sample_config):
        """Test _update_db with profile data to save."""
        collected_data = {
            "age_range": "26_35",
            "occupation_type": "engineer",
            "marital_status": "single",
            "invalid_field": "should_be_filtered"  # This should be filtered out
        }
        
        state = OnboardingState(
            needs_database_update=True,
            collected_data=collected_data,
            onboarding_complete=False
        )
        
        result = agent._update_db(state, sample_config)
        
        assert result == {"needs_database_update": False}
        
        # Check that only valid fields were saved
        expected_data = {
            "age_range": "26_35",
            "occupation_type": "engineer",
            "marital_status": "single"
        }
        mock_user_storage.create_or_update_personal_context.assert_called_once_with(
            "test_user_123", expected_data
        )
        # User profile_complete should not be updated since onboarding_complete is False
        mock_user_storage.update_user.assert_not_called()
    
    @patch('app.ai.onboarding.user_storage')
    def test_update_db_onboarding_complete(self, mock_user_storage, agent, sample_config):
        """Test _update_db when onboarding is complete."""
        collected_data = {"age_range": "26_35", "occupation_type": "engineer"}
        
        state = OnboardingState(
            needs_database_update=True,
            collected_data=collected_data,
            onboarding_complete=True
        )
        
        result = agent._update_db(state, sample_config)
        
        assert result == {"needs_database_update": False}
        
        # Both personal context and user profile_complete should be updated
        mock_user_storage.create_or_update_personal_context.assert_called_once_with(
            "test_user_123", collected_data
        )
        mock_user_storage.update_user.assert_called_once_with(
            "test_user_123", {"profile_complete": True}
        )
    
    @patch('app.ai.onboarding.user_storage')
    def test_update_db_database_error(self, mock_user_storage, agent, sample_config):
        """Test _update_db handles database errors gracefully."""
        state = OnboardingState(
            needs_database_update=True,
            collected_data={"age_range": "26_35"},
            onboarding_complete=False
        )
        
        # Mock database to raise exception
        mock_user_storage.create_or_update_personal_context.side_effect = Exception("Database error")
        
        result = agent._update_db(state, sample_config)
        
        # Should handle error gracefully and return False
        assert result == {"needs_database_update": False}
    
    def test_update_main_graph_not_complete(self, agent, sample_config):
        """Test _update_main_graph when onboarding is not complete."""
        state = OnboardingState(onboarding_complete=False)
        
        result = agent._update_main_graph(state, sample_config)
        
        assert result == {"onboarding_complete": False}
    
    def test_update_main_graph_complete(self, agent, sample_config):
        """Test _update_main_graph when onboarding is complete."""
        collected_data = {
            "age_range": "26_35",
            "life_stage": "early_career",
            "occupation_type": "engineer",
            "location_context": "California, high cost of living area",
            "family_structure": "single_no_dependents",
            "marital_status": "single",
            "total_dependents_count": 0,
            "caregiving_responsibilities": "none"
        }
        
        state = OnboardingState(
            onboarding_complete=True,
            collected_data=collected_data
        )
        
        result = agent._update_main_graph(state, sample_config)
        
        assert "profile_context" in result
        assert "profile_context_timestamp" in result
        
        profile_context = result["profile_context"]
        assert "Age range: 26_35" in profile_context
        assert "Life stage: early_career" in profile_context
        assert "Occupation: engineer" in profile_context
        assert "Location: California, high cost of living area" in profile_context
        assert "Family structure: single_no_dependents" in profile_context
        assert "Marital status: single" in profile_context
        # Caregiving "none" is not included in profile context (only non-none values)
        assert "Caregiving:" not in profile_context
        
        assert isinstance(result["profile_context_timestamp"], datetime)
    
    def test_check_profile_complete_not_complete(self, agent):
        """Test _check_profile_complete when profile is not complete."""
        state = OnboardingState(onboarding_complete=False)
        
        result = agent._check_profile_complete(state)
        
        assert result == "end"
    
    def test_check_profile_complete_complete(self, agent):
        """Test _check_profile_complete when profile is complete."""
        state = OnboardingState(onboarding_complete=True)
        
        result = agent._check_profile_complete(state)
        
        assert result == "update_global_state"


class TestOnboardingAgentGraph:
    """Test OnboardingAgent graph compilation and structure."""
    
    def test_graph_compile_creates_graph(self):
        """Test that graph_compile creates and returns a compiled graph."""
        agent = OnboardingAgent()
        
        graph = agent.graph_compile()
        
        assert graph is not None
        # Graph should be cached
        assert agent._graph is not None
        assert agent._graph == graph
        
        # Calling again should return the same cached graph
        graph2 = agent.graph_compile()
        assert graph2 is graph
    
    def test_graph_compile_has_correct_structure(self):
        """Test that compiled graph has correct structure."""
        agent = OnboardingAgent()
        graph = agent.graph_compile()
        
        # Check that graph was compiled successfully
        # CompiledStateGraph has different attributes than uncompiled graph
        assert hasattr(graph, 'invoke')
        assert hasattr(graph, 'stream')
        assert hasattr(graph, 'get_graph')
        
        # We can't easily inspect the internal structure of compiled LangGraph,
        # but we can verify it compiles without errors and has expected methods
        assert graph is not None
        assert callable(graph.invoke)
        assert callable(graph.stream)


class TestOnboardingAgentIntegration:
    """Integration tests for OnboardingAgent with mocked external dependencies."""
    
    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.llm_factory')
    def test_full_onboarding_flow_new_user(self, mock_llm_factory, mock_user_storage):
        """Test complete onboarding flow for a new user."""
        # Setup mocks
        mock_user_storage.get_user_by_id.return_value = None
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data={"age_range": "26_35", "occupation_type": "engineer"},
            next_questions=["What is your marital status?"],
            completion_status="partial",
            user_response="Great! I've noted your age and occupation. What is your marital status?"
        )
        
        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response
        
        # Create agent and test data
        agent = OnboardingAgent()
        initial_state = OnboardingState(
            messages=[HumanMessage(content="I'm 28 and work as a software engineer")]
        )
        config = {
            "configurable": {
                "user_id": "test_user_123",
                "thread_id": "test_thread_456"
            }
        }
        
        # Test the flow manually by calling each method
        # 1. Read database
        db_result = agent._read_db(initial_state, config)
        # Update state fields manually to preserve messages correctly
        updated_state = OnboardingState(
            messages=initial_state.messages,  # Keep original messages
            collected_data=db_result.get("collected_data", {}),
            current_step=db_result.get("current_step", "welcome")
        )
        
        # 2. Call LLM
        llm_result = agent._call_llm(updated_state, config)
        # Merge messages properly - original + new AI message
        all_messages = updated_state.messages + llm_result.get("messages", [])
        updated_state = OnboardingState(
            messages=all_messages,
            collected_data=llm_result.get("collected_data", {}),
            current_step=updated_state.current_step,
            needs_database_update=llm_result.get("needs_database_update", False),
            onboarding_complete=llm_result.get("onboarding_complete", False)
        )
        
        # 3. Update database
        db_update_result = agent._update_db(updated_state, config)
        final_state = OnboardingState(
            messages=updated_state.messages,  # Keep all messages
            collected_data=updated_state.collected_data,
            current_step=updated_state.current_step,
            needs_database_update=db_update_result.get("needs_database_update", False),
            onboarding_complete=updated_state.onboarding_complete
        )
        
        # Verify the final state
        assert final_state.collected_data == {"age_range": "26_35", "occupation_type": "engineer"}
        assert final_state.needs_database_update is False
        assert final_state.onboarding_complete is False
        assert len(final_state.messages) == 2  # Original + AI response
        
        # Verify AI message
        ai_message = final_state.messages[-1]
        assert isinstance(ai_message, AIMessage)
        assert "marital status" in ai_message.content
        assert ai_message.additional_kwargs["agent"] == "onboarding"
        
        # Verify database calls
        mock_user_storage.get_user_by_id.assert_called_once_with("test_user_123")
        mock_user_storage.create_or_update_personal_context.assert_called_once()
    
    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.llm_factory')
    def test_onboarding_completion_flow(self, mock_llm_factory, mock_user_storage):
        """Test onboarding flow when user completes their profile."""
        # Setup mocks for existing user with some data
        mock_user_storage.get_user_by_id.return_value = {"id": "test_user_123"}
        mock_user_storage.get_personal_context.return_value = {
            "age_range": "26_35",
            "occupation_type": "engineer"
        }
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data={"marital_status": "single", "family_structure": "single_no_dependents"},
            next_questions=[],
            completion_status="complete",
            user_response="Perfect! Your profile is now complete and I can provide personalized financial advice."
        )
        
        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response
        
        agent = OnboardingAgent()
        initial_state = OnboardingState(
            messages=[HumanMessage(content="I'm single with no dependents")]
        )
        config = {
            "configurable": {
                "user_id": "test_user_123",
                "thread_id": "test_thread_456"
            }
        }
        
        # Simulate the flow
        db_result = agent._read_db(initial_state, config)
        updated_state = OnboardingState(
            **{**initial_state.model_dump(), **db_result}
        )
        
        llm_result = agent._call_llm(updated_state, config)
        updated_state = OnboardingState(
            **{**updated_state.model_dump(), **llm_result}
        )
        
        db_update_result = agent._update_db(updated_state, config)
        updated_state = OnboardingState(
            **{**updated_state.model_dump(), **db_update_result}
        )
        
        # Check completion routing
        route = agent._check_profile_complete(updated_state)
        assert route == "update_global_state"
        
        # Update global state
        global_update_result = agent._update_main_graph(updated_state, config)
        
        # Verify completion
        assert updated_state.onboarding_complete is True
        assert "profile_context" in global_update_result
        assert "Age range: 26_35" in global_update_result["profile_context"]
        
        # Verify database updates for completion
        mock_user_storage.update_user.assert_called_once_with(
            "test_user_123", {"profile_complete": True}
        )