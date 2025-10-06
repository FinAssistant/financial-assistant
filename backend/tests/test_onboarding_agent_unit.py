"""
Unit tests for OnboardingAgent.
All external dependencies are mocked for fast, reliable testing.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from app.ai.onboarding import OnboardingAgent, OnboardingState, ProfileDataExtraction, ExtractedProfileData


@pytest.fixture
def complete_demographic_mock():
    """Create reusable mock for complete demographic data from database."""
    return {
        "user_id": "test_user_123",
        "age_range": "26_35",
        "life_stage": "early_career",
        "occupation_type": "engineer",
        "location_context": "California",
        "family_structure": "single_no_dependents",
        "marital_status": "single",
        "total_dependents_count": 0,
        "children_count": 0,
        "caregiving_responsibilities": "none",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }


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

        # extracted_data is now an ExtractedProfileData object with all fields None
        assert extraction.extracted_data.age_range is None
        assert extraction.extracted_data.occupation_type is None
        assert extraction.extracted_data.marital_status is None
        assert extraction.completion_status == "incomplete"
        assert extraction.user_response == "Hello! I'd like to help you."
    
    def test_profile_data_extraction_complete(self):
        """Test ProfileDataExtraction with full data."""
        extracted_data = ExtractedProfileData(
            age_range="26_35",
            occupation_type="engineer"
        )

        extraction = ProfileDataExtraction(
            extracted_data=extracted_data,
            completion_status="partial",
            user_response="Great! I've noted your age and occupation."
        )

        assert extraction.extracted_data.age_range == "26_35"
        assert extraction.extracted_data.occupation_type == "engineer"
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
    async def test_call_llm_basic(self, mock_llm_factory, agent, sample_state, sample_config):
        """Test _call_llm with mocked LLM response."""
        # Mock account checking to return True (has accounts)
        with patch.object(agent, '_has_connected_accounts', return_value=True):
            # Mock LLM response
            mock_llm = Mock()
            mock_structured_llm = Mock()
            mock_response = ProfileDataExtraction(
                extracted_data=ExtractedProfileData(
                    age_range="26_35",
                    occupation_type="engineer"
                ),
                completion_status="partial",
                user_response="Great! I've noted that you're 28 and work as a software engineer."
            )

            mock_llm_factory.create_llm.return_value = mock_llm
            mock_llm.with_structured_output.return_value = mock_structured_llm
            mock_structured_llm.invoke.return_value = mock_response

            result = await agent._call_llm(sample_state, sample_config)
        
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
            # onboarding_complete moved to _check_completion node
            assert "onboarding_complete" not in result

            # Verify LLM was called correctly
            mock_llm_factory.create_llm.assert_called_once()
        mock_llm.with_structured_output.assert_called_once()
        mock_structured_llm.invoke.assert_called_once()
    
    @patch('app.ai.onboarding.llm_factory')
    async def test_call_llm_completion_complete(self, mock_llm_factory, agent, sample_state, sample_config):
        """Test _call_llm when profile is marked complete."""
        # Mock account checking to return True (has accounts) - needed for true completion
        with patch.object(agent, '_has_connected_accounts', return_value=True):
            # Mock LLM response indicating completion
            mock_llm = Mock()
            mock_structured_llm = Mock()
            mock_response = ProfileDataExtraction(
                extracted_data=ExtractedProfileData(
                    marital_status="single"
                ),
                completion_status="complete",
                user_response="Perfect! Your profile is now complete."
            )

            mock_llm_factory.create_llm.return_value = mock_llm
            mock_llm.with_structured_output.return_value = mock_structured_llm
            mock_structured_llm.invoke.return_value = mock_response

            result = await agent._call_llm(sample_state, sample_config)

            # onboarding_complete moved to _check_completion node
            assert "onboarding_complete" not in result
            assert result["needs_database_update"] is True

            ai_message = result["messages"][0]
            assert ai_message.content == "Perfect! Your profile is now complete."

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
        
        # Verify database was called twice: once for profile data, once for completion status
        assert mock_user_storage.create_or_update_personal_context.call_count == 2

        # Check the calls were made with correct data
        calls = mock_user_storage.create_or_update_personal_context.call_args_list
        expected_data = {
            "age_range": "26_35",
            "occupation_type": "engineer",
            "marital_status": "single"
        }
        assert calls[0] == call("test_user_123", expected_data)
        assert calls[1] == call("test_user_123", {"is_complete": False})

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
        
        # Verify database was called twice: once for profile data, once for completion status
        assert mock_user_storage.create_or_update_personal_context.call_count == 2

        # Check the calls were made with correct data
        calls = mock_user_storage.create_or_update_personal_context.call_args_list
        assert calls[0] == call("test_user_123", collected_data)
        assert calls[1] == call("test_user_123", {"is_complete": True})

        # Verify deprecated User table was also updated for backward compatibility
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
    
    def test_route_completion_not_complete(self, agent):
        """Test _route_completion when profile is not complete."""
        state = OnboardingState(onboarding_complete=False)

        result = agent._route_completion(state)

        assert result == "end"

    def test_route_completion_complete(self, agent):
        """Test _route_completion when profile is complete."""
        state = OnboardingState(onboarding_complete=True)

        result = agent._route_completion(state)

        assert result == "update_global_state"

    @patch('app.ai.onboarding.user_storage')
    def test_check_completion_not_complete_missing_demographics(self, mock_user_storage, agent, sample_config):
        """Test _check_completion when demographics are incomplete."""
        # Mock database to return incomplete demographic data
        mock_user_storage.get_personal_context.return_value = {
            "user_id": "test_user_123",
            "age_range": "26_35",
            # Missing other required fields: life_stage, occupation_type, etc.
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        state = OnboardingState(
            collected_data={"age_range": "26_35"}  # Missing other required fields
        )

        with patch.object(agent, '_has_connected_accounts', return_value=True):
            result = agent._check_completion(state, sample_config)

            assert result["onboarding_complete"] is False
            # Verify database was queried
            mock_user_storage.get_personal_context.assert_called_once_with("test_user_123")

    @patch('app.ai.onboarding.user_storage')
    def test_check_completion_complete(self, mock_user_storage, agent, sample_config, complete_demographic_mock):
        """Test _check_completion when both demographics and accounts are complete."""
        # Mock database to return complete demographic data
        mock_user_storage.get_personal_context.return_value = complete_demographic_mock

        complete_demographics = {
            "age_range": "26_35",
            "life_stage": "early_career",
            "occupation_type": "engineer",
            "location_context": "California",
            "family_structure": "single_no_dependents",
            "marital_status": "single",
            "total_dependents_count": 0,
            "children_count": 0,
            "caregiving_responsibilities": "none"
        }
        state = OnboardingState(collected_data=complete_demographics)

        with patch.object(agent, '_has_connected_accounts', return_value=True):
            result = agent._check_completion(state, sample_config)

            assert result["onboarding_complete"] is True
            # Verify database was queried
            mock_user_storage.get_personal_context.assert_called_once_with("test_user_123")

    def test_route_message_type_normal_message(self, agent):
        """Test _route_message_type with normal user message."""
        state = OnboardingState(
            messages=[HumanMessage(content="I'm 28 and work as an engineer")]
        )

        result = agent._route_message_type(state)

        assert result == "read_database"

    def test_route_message_type_system_message(self, agent):
        """Test _route_message_type with system message about accounts."""
        state = OnboardingState(
            messages=[HumanMessage(content="SYSTEM: User successfully connected 2 bank accounts")]
        )

        result = agent._route_message_type(state)

        assert result == "handle_account_connection"

    def test_handle_account_connection_success(self, agent, sample_config):
        """Test _handle_account_connection when accounts are connected."""
        state = OnboardingState(
            messages=[HumanMessage(content="SYSTEM: User connected accounts")]
        )

        with patch.object(agent, '_has_connected_accounts', return_value=True), \
             patch.object(agent, '_get_account_summary', return_value="2 checking accounts, 1 savings account"):

            result = agent._handle_account_connection(state, sample_config)

            assert "messages" in result
            ai_message = result["messages"][0]
            assert isinstance(ai_message, AIMessage)
            assert "Congratulations" in ai_message.content
            assert "2 checking accounts, 1 savings account" in ai_message.content


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


@patch('app.ai.onboarding.OnboardingAgent._has_connected_accounts', return_value=False)
class TestOnboardingAgentIntegration:
    """Integration tests for OnboardingAgent with mocked external dependencies."""
    
    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.llm_factory')
    async def test_full_onboarding_flow_new_user(self, mock_llm_factory, mock_user_storage, mock_has_accounts):
        """Test complete onboarding flow for a new user."""
        # Setup mocks
        mock_user_storage.get_user_by_id.return_value = None
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data=ExtractedProfileData(
                age_range="26_35",
                occupation_type="engineer"
            ),
            completion_status="partial",
            user_response="Great! I've noted your age and occupation. What is your marital status?"
        )

        mock_llm_factory.create_llm.return_value = mock_llm

        # Mock both regular and tool-bound LLM chains
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_llm.bind_tools.return_value = mock_llm  # Tool binding returns the same LLM
        mock_structured_llm.invoke.return_value = mock_response

        # Create agent and test data
        agent = OnboardingAgent()

        # Mock the Plaid MCP client tool retrieval
        mock_plaid_tool = Mock()
        mock_plaid_tool.name = "create_link_token"
        agent._plaid_client.get_tool_by_name = AsyncMock(return_value=mock_plaid_tool)

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
        llm_result = await agent._call_llm(updated_state, config)
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
        # Expect 2 calls: profile data + completion status
        assert mock_user_storage.create_or_update_personal_context.call_count == 2
    
    @patch('app.ai.onboarding.user_storage')
    @patch('app.ai.onboarding.llm_factory')
    async def test_onboarding_completion_flow(self, mock_llm_factory, mock_user_storage, mock_has_accounts, complete_demographic_mock):
        # Override the class-level mock to return True for this completion test
        mock_has_accounts.return_value = True
        """Test onboarding flow when user completes their profile."""
        # Setup mocks for existing user with some data
        mock_user_storage.get_user_by_id.return_value = {"id": "test_user_123"}

        # Start with incomplete data that will be completed during the flow
        initial_incomplete_data = {
            "age_range": "26_35",
            "occupation_type": "engineer",
            "life_stage": "early_career",
            "location_context": "California",
            "total_dependents_count": 0,
            "children_count": 0,
            "caregiving_responsibilities": "none"
            # Missing marital_status and family_structure initially
        }

        # Mock the database to return complete data after the LLM adds missing fields
        complete_data = complete_demographic_mock.copy()
        complete_data.update({
            "marital_status": "single",
            "family_structure": "single_no_dependents"
        })

        # Set up side_effect to return incomplete first, then complete data
        mock_user_storage.get_personal_context.side_effect = [
            initial_incomplete_data,  # First call during _read_db
            complete_data,  # Subsequent calls during _check_completion
            complete_data,
            complete_data
        ]
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data=ExtractedProfileData(
                marital_status="single",
                family_structure="single_no_dependents"
            ),
            completion_status="complete",
            user_response="Perfect! Your profile is now complete and I can provide personalized financial advice."
        )

        mock_llm_factory.create_llm.return_value = mock_llm

        # Mock both regular and tool-bound LLM chains
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_llm.bind_tools.return_value = mock_llm  # Tool binding returns the same LLM
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
        
        llm_result = await agent._call_llm(updated_state, config)
        updated_state = OnboardingState(
            **{**updated_state.model_dump(), **llm_result}
        )
        
        db_update_result = agent._update_db(updated_state, config)
        updated_state = OnboardingState(
            **{**updated_state.model_dump(), **db_update_result}
        )
        
        # Check completion status first (new step in workflow)
        completion_result = agent._check_completion(updated_state, config)
        updated_state = OnboardingState(
            **{**updated_state.model_dump(), **completion_result}
        )

        # Since completion status changed, need to update database again
        agent._update_db(updated_state, config)

        # Check completion routing
        route = agent._route_completion(updated_state)
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


class TestOnboardingAgentGraphitiIntegration:
    """Test OnboardingAgent Graphiti integration with mocked GraphitiMCPClient."""

    @pytest.fixture
    def agent(self):
        """Create OnboardingAgent instance for testing."""
        agent = OnboardingAgent()
        # Mock the _has_connected_accounts method for this instance
        agent._has_connected_accounts = AsyncMock(return_value=False)
        return agent
    
    @pytest.fixture
    def sample_state_with_messages(self):
        """Create sample OnboardingState with conversation messages."""
        return OnboardingState(
            messages=[
                HumanMessage(content="I have left my job in mid July, my wife is taking a leave of absence starting in October"),
                AIMessage(content="Thank you for updating me on these important changes. Being between jobs and having your wife take leave will significantly impact your financial planning.")
            ],
            current_step="continue",
            collected_data={"age_range": "36_45", "occupation_type": "unemployed"},
            needs_database_update=True,
            onboarding_complete=False
        )
    
    @pytest.fixture
    def sample_config(self):
        """Create sample config for testing."""
        return {
            "configurable": {
                "user_id": "test_user_456",
                "thread_id": "test_thread_789"
            }
        }

    @pytest.fixture
    def sample_successful_storage(self):
        """Create sample content for testing."""
        human_message = "I have left my job in mid July, my wife is taking a leave of absence starting in October"
        ai_response = "Thank you for updating me on these important changes. Being between jobs and having your wife take leave will significantly impact your financial planning."

        lines = [
            "FINANCIAL CONVERSATION CONTEXT:",
            f"User Message: {human_message}",
            "",
            "EXTRACTION PRIORITIES:",
            "- Financial goals (saving, investing, debt payoff, retirement)",
            "- Risk tolerance and concerns",
            "- Dollar amounts and timeframes",
            "- Family situation affecting finances",
            "- Values and priorities expressed",
            "- Constraints or limitations mentioned",
            "- Personal info: income range, net worth, major assets/liabilities",
            "- Geographic context: city/state, cost of living",
            "- Demographic context: age range, life stage, occupation type",
            "- Any other details relevant to financial planning",
            "",
            "ADDITIONAL CONTEXT:",
            f"{ {'assistant_response': ai_response} }"
        ]

        enhanced_content = "\n".join(lines)
        return enhanced_content
    
    @patch('app.ai.onboarding.get_graphiti_client')
    @pytest.mark.asyncio
    async def test_store_memory_successful_storage(self, mock_get_graphiti_client, agent, sample_state_with_messages, sample_config, sample_successful_storage):
        """Test _store_memory successfully stores conversation in Graphiti."""
        # Mock Graphiti client
        mock_graphiti_client = AsyncMock()
        mock_get_graphiti_client.return_value = mock_graphiti_client
        
        result = await agent._store_memory(sample_state_with_messages, sample_config)
        
        # Should return empty dict (no state changes needed)
        assert result == {}
        
        # Verify Graphiti client was called correctly
        mock_get_graphiti_client.assert_called_once()
        mock_graphiti_client.add_episode.assert_called_once_with(
            user_id="test_user_456",
            content=sample_successful_storage,
            name="Onboarding Conversation",
            source_description="onboarding_agent"
        )
    
    @patch('app.ai.onboarding.get_graphiti_client')
    @pytest.mark.asyncio
    async def test_store_memory_handles_graphiti_error(self, mock_get_graphiti_client, agent, sample_state_with_messages, sample_config):
        """Test _store_memory handles Graphiti errors gracefully."""
        # Mock Graphiti client to raise exception
        mock_graphiti_client = AsyncMock()
        mock_graphiti_client.add_episode.side_effect = Exception("Graphiti connection failed")
        mock_get_graphiti_client.return_value = mock_graphiti_client
        
        # Should not raise exception, but handle gracefully
        result = await agent._store_memory(sample_state_with_messages, sample_config)
        
        # Should still return empty dict
        assert result == {}
        
        # Verify attempt was made but error was handled
        mock_graphiti_client.add_episode.assert_called_once()
    
    @patch('app.ai.onboarding.get_graphiti_client')
    @pytest.mark.asyncio
    async def test_store_memory_insufficient_messages(self, mock_get_graphiti_client, agent, sample_config):
        """Test _store_memory when there are insufficient messages to store."""
        # State with no messages or only one type
        insufficient_state = OnboardingState(
            messages=[AIMessage(content="Only an AI message")],  # Missing HumanMessage
            current_step="welcome"
        )
        
        mock_graphiti_client = AsyncMock()
        mock_get_graphiti_client.return_value = mock_graphiti_client
        
        result = await agent._store_memory(insufficient_state, sample_config)
        
        # Should return empty dict
        assert result == {}
        
        # Should not attempt to store in Graphiti
        mock_graphiti_client.add_episode.assert_not_called()
    
    @pytest.fixture
    def sample_extracts_latest_messages(self):
        """Create sample content for testing."""
        human_message = "Second user message"
        ai_response = "Latest AI response"

        lines = [
            "FINANCIAL CONVERSATION CONTEXT:",
            f"User Message: {human_message}",
            "",
            "EXTRACTION PRIORITIES:",
            "- Financial goals (saving, investing, debt payoff, retirement)",
            "- Risk tolerance and concerns",
            "- Dollar amounts and timeframes",
            "- Family situation affecting finances",
            "- Values and priorities expressed",
            "- Constraints or limitations mentioned",
            "- Personal info: income range, net worth, major assets/liabilities",
            "- Geographic context: city/state, cost of living",
            "- Demographic context: age range, life stage, occupation type",
            "- Any other details relevant to financial planning",
            "",
            "ADDITIONAL CONTEXT:",
            f"{ {'assistant_response': ai_response} }"
        ]

        enhanced_content = "\n".join(lines)
        return enhanced_content

    @patch('app.ai.onboarding.get_graphiti_client')  
    @pytest.mark.asyncio
    async def test_store_memory_extracts_latest_messages(self, mock_get_graphiti_client, agent, sample_config, sample_extracts_latest_messages):
        """Test _store_memory correctly extracts latest human and AI messages."""
        # State with multiple messages - should get the latest pair
        multi_message_state = OnboardingState(
            messages=[
                HumanMessage(content="First user message"),
                AIMessage(content="First AI response"),
                HumanMessage(content="Second user message"),  # This should be extracted
                AIMessage(content="Latest AI response")       # This should be extracted
            ],
            current_step="continue"
        )
        
        mock_graphiti_client = AsyncMock()
        mock_get_graphiti_client.return_value = mock_graphiti_client

        await agent._store_memory(multi_message_state, sample_config)

        # Should extract the latest human and AI messages
        mock_graphiti_client.add_episode.assert_called_once_with(
            user_id="test_user_456",
            content=sample_extracts_latest_messages,
            name="Onboarding Conversation", 
            source_description="onboarding_agent"
        )
    
    async def test_enhanced_profile_change_detection_prompts(self, agent):
        """Test that the system prompt includes enhanced change detection."""
        # This test verifies the prompt includes the new life change detection capabilities
        sample_state = OnboardingState(
            messages=[HumanMessage(content="I left my job")],
            current_step="continue",
            collected_data={"age_range": "36_45", "occupation_type": "engineer"}
        )
        
        config = {
            "configurable": {
                "user_id": "test_user_456", 
                "thread_id": "test_thread_789"
            }
        }
        
        # We can't easily test the private _call_llm method's prompt directly,
        # but we can verify the prompt structure through the LLM call
        with patch('app.ai.onboarding.llm_factory') as mock_llm_factory:
            mock_llm = Mock()
            mock_structured_llm = Mock()
            mock_response = ProfileDataExtraction(
                extracted_data=ExtractedProfileData(
                    occupation_type="unemployed",
                    life_stage="between_jobs"
                ),
                completion_status="partial",
                user_response="I've updated your employment status."
            )
            
            mock_llm_factory.create_llm.return_value = mock_llm
            mock_llm.with_structured_output.return_value = mock_structured_llm
            mock_structured_llm.invoke.return_value = mock_response
            
            result = await agent._call_llm(sample_state, config)
            
            # Verify the structured LLM was called (which means prompt was built)
            mock_structured_llm.invoke.assert_called_once()
            
            # Verify the call captured life changes
            assert result["collected_data"]["occupation_type"] == "unemployed"
            assert result["collected_data"]["life_stage"] == "between_jobs"
            assert result["needs_database_update"] is True
    
    @patch('app.ai.onboarding.user_storage')
    def test_database_update_logic_always_attempts_save(self, mock_user_storage, agent, sample_config):
        """Test that database update logic always attempts to save when there's data."""
        # This test verifies the fix to the database update logic
        state_with_data = OnboardingState(
            needs_database_update=False,  # Even when this is False
            onboarding_complete=False,    # And this is False  
            collected_data={"age_range": "36_45", "occupation_type": "unemployed"}  # Should still save
        )
        
        result = agent._update_db(state_with_data, sample_config)
        
        # Should attempt to save because there's collected data - expect 2 calls
        assert mock_user_storage.create_or_update_personal_context.call_count == 2

        # Check the calls were made with correct data
        calls = mock_user_storage.create_or_update_personal_context.call_args_list
        assert calls[0] == call("test_user_456", {"age_range": "36_45", "occupation_type": "unemployed"})
        assert calls[1] == call("test_user_456", {"is_complete": False})
        assert result == {"needs_database_update": False}
    
    def test_expanded_vocabulary_in_profile_fields(self):
        """Test that expanded vocabulary (unemployed, between_jobs, etc.) is supported."""
        # This test verifies that the new field values work with the data model
        expanded_data = {
            "age_range": "36_45",
            "life_stage": "between_jobs",  # New value
            "occupation_type": "unemployed",  # New value  
            "family_structure": "married_no_income",  # New value
            "marital_status": "married",
            "total_dependents_count": 1,
            "children_count": 1,
            "caregiving_responsibilities": "none"
        }
        
        # Should be able to create state with expanded vocabulary
        state = OnboardingState(
            collected_data=expanded_data,
            onboarding_complete=True
        )
        
        agent = OnboardingAgent()
        config = {
            "configurable": {
                "user_id": "test_user_456",
                "thread_id": "test_thread_789"
            }
        }
        
        # Should be able to generate profile context with new values
        result = agent._update_main_graph(state, config) 
        
        profile_context = result["profile_context"]
        assert "Life stage: between_jobs" in profile_context
        assert "Occupation: unemployed" in profile_context
        assert "Family structure: married_no_income" in profile_context


class TestOnboardingAgentLifeChangeScenarios:
    """Test specific life change scenarios that the enhanced agent should handle."""
    
    @pytest.fixture
    def agent(self):
        agent = OnboardingAgent()
        # Mock the _has_connected_accounts method for this instance
        agent._has_connected_accounts = AsyncMock(return_value=False)
        return agent
    
    @pytest.fixture  
    def config(self):
        return {
            "configurable": {
                "user_id": "test_user_789",
                "thread_id": "test_thread_123" 
            }
        }
    
    @patch('app.ai.onboarding.llm_factory')
    async def test_job_loss_scenario(self, mock_llm_factory, agent, config):
        """Test handling of job loss scenario."""
        # User with existing job data reports job loss
        state = OnboardingState(
            messages=[HumanMessage(content="I have left my job in mid July")],
            current_step="continue",
            collected_data={"age_range": "36_45", "occupation_type": "engineer"}
        )
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data=ExtractedProfileData(
                occupation_type="unemployed",
                life_stage="between_jobs"
            ),
            completion_status="partial",
            user_response="I've updated your employment status. This change will affect your financial planning."
        )

        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response

        result = await agent._call_llm(state, config)
        
        # Should detect the job loss and update employment status
        assert result["collected_data"]["occupation_type"] == "unemployed"
        assert result["collected_data"]["life_stage"] == "between_jobs"
        assert result["needs_database_update"] is True
        
        ai_message = result["messages"][0]
        assert "employment status" in ai_message.content
    
    @patch('app.ai.onboarding.llm_factory')
    async def test_family_income_change_scenario(self, mock_llm_factory, agent, config):
        """Test handling of family income change scenario."""
        state = OnboardingState(
            messages=[HumanMessage(content="My wife is taking a leave of absence starting in October")],
            current_step="continue",
            collected_data={
                "age_range": "36_45", 
                "family_structure": "married_dual_income",
                "marital_status": "married"
            }
        )
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data=ExtractedProfileData(
                family_structure="married_single_income"  # Updated from dual to single income
            ),
            completion_status="partial",
            user_response="I've noted that your family will transition to single income. This is an important change for your financial planning."
        )

        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response

        result = await agent._call_llm(state, config)
        
        # Should detect family income structure change
        expected_data = {
            "age_range": "36_45",
            "family_structure": "married_single_income",  # Updated
            "marital_status": "married"
        }
        assert result["collected_data"] == expected_data
        assert result["needs_database_update"] is True
    
    @patch('app.ai.onboarding.llm_factory') 
    async def test_no_life_changes_scenario(self, mock_llm_factory, agent, config):
        """Test that casual conversation doesn't trigger unnecessary updates."""
        state = OnboardingState(
            messages=[HumanMessage(content="How should I invest my savings?")],
            current_step="continue",
            collected_data={"age_range": "36_45", "occupation_type": "engineer"}
        )
        
        mock_llm = Mock()
        mock_structured_llm = Mock()
        mock_response = ProfileDataExtraction(
            extracted_data=ExtractedProfileData(),  # No new data extracted (all fields None)
            completion_status="partial",
            user_response="I'd be happy to help with investment advice based on your current situation."
        )

        mock_llm_factory.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_response

        result = await agent._call_llm(state, config)
        
        # Should not extract new data or trigger update for general questions
        assert result["collected_data"] == {"age_range": "36_45", "occupation_type": "engineer"}
        assert result["needs_database_update"] is False