"""
Unit tests for orchestrator and agent routing functionality.
All tests use mocked LLM calls by default.
"""
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.ai.langgraph_config import LangGraphConfig, GlobalState


class TestGlobalState:
    """Test GlobalState model functionality."""
    
    def test_global_state_creation(self):
        """Test GlobalState can be created with defaults."""
        state = GlobalState()
        
        assert state.messages == []
        assert state.connected_accounts is None
        assert state.profile_context is None
        assert state.profile_complete is False
    
    def test_global_state_with_messages(self):
        """Test GlobalState with messages."""
        state = GlobalState()
        
        state.messages.append(HumanMessage(content="Hello"))
        state.messages.append(AIMessage(content="Hi there!"))
        
        assert len(state.messages) == 2
        assert isinstance(state.messages[0], HumanMessage)
        assert isinstance(state.messages[1], AIMessage)
    
    def test_profile_complete_flag(self):
        """Test profile completion flag."""
        state = GlobalState()
        
        assert state.profile_complete is False
        
        state.profile_complete = True
        assert state.profile_complete is True


class TestLangGraphConfig:
    """Test LangGraph configuration and setup."""
    
    def test_langgraph_initialization(self, mock_llm_factory):
        """Test LangGraph config can be initialized."""
        config = LangGraphConfig()
        
        assert config is not None
        assert config.graph is not None
        assert config.llm is not None
        assert config.llm == mock_llm_factory
    
    def test_checkpointer_initialization(self, mock_llm_factory):
        """Test SQLite checkpointer setup."""
        config = LangGraphConfig()
        
        # Should have checkpointer (SQLite is default)
        assert config.checkpointer is not None


class TestOrchestratorRouting:
    """Test orchestrator routing logic."""
    
    def test_find_route_basic(self, mock_llm_factory):
        """Test find_route extracts routing decision."""
        config = LangGraphConfig()
        
        state = GlobalState()
        state.messages = [AIMessage(content="SMALLTALK")]
        
        route = config.find_route(state)
        assert route == "SMALLTALK"
    
    def test_find_route_all_destinations(self, mock_llm_factory):
        """Test routing to all possible destinations."""
        config = LangGraphConfig()
        
        test_routes = ["SMALLTALK", "SPENDING", "INVESTMENT", "ONBOARDING"]
        
        for expected_route in test_routes:
            state = GlobalState()
            state.messages = [AIMessage(content=expected_route)]
            
            actual_route = config.find_route(state)
            assert actual_route == expected_route


class TestSmallTalkAgent:
    """Test small talk agent functionality."""
    
    def test_small_talk_node_direct(self, mock_llm_factory):
        """Test small talk node directly."""
        config = LangGraphConfig()
        
        state = GlobalState()
        state.messages = [HumanMessage(content="Hello!")]
        
        test_config = {
            "configurable": {
                "user_id": "test_user",
                "thread_id": "test_thread"
            }
        }
        
        result = config._small_talk_node(state, test_config)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        
        response_message = result["messages"][0]
        assert isinstance(response_message, AIMessage)
        assert response_message.content == "SMALLTALK"
        assert response_message.additional_kwargs.get("agent") == "small_talk"
    
    def test_small_talk_system_prompt_usage(self, mock_llm_factory):
        """Test small talk agent uses correct system prompt."""
        config = LangGraphConfig()
        
        state = GlobalState()
        state.messages = [HumanMessage(content="How's the weather?")]
        
        test_config = {
            "configurable": {
                "user_id": "test_user", 
                "thread_id": "test_thread"
            }
        }
        
        config._small_talk_node(state, test_config)
        
        # Verify LLM was called with system message
        mock_llm_factory.invoke.assert_called_once()
        call_args = mock_llm_factory.invoke.call_args[0][0]
        
        assert len(call_args) >= 2  # System prompt + user messages
        assert isinstance(call_args[0], SystemMessage)
        assert "financial assistant" in call_args[0].content.lower()


class TestConversationFlow:
    """Test end-to-end conversation processing with mocked responses."""
    
    def test_invoke_conversation_basic(self, mock_llm_factory, test_user_id, test_session_id):
        """Test basic conversation invocation."""
        # Set up mock to return routing decision first, then small talk response
        mock_responses = [
            AIMessage(content="SMALLTALK", additional_kwargs={'refusal': None}),  # Orchestrator
            AIMessage(content="Hello! How are you?", additional_kwargs={'refusal': None})  # Small talk
        ]
        mock_llm_factory.invoke.side_effect = mock_responses
        
        config = LangGraphConfig()
        
        result = config.invoke_conversation(
            user_message="Hello there!",
            user_id=test_user_id,
            session_id=test_session_id
        )
        
        assert result is not None
        assert "content" in result
        assert "agent" in result
        assert "session_id" in result
        assert "user_id" in result
        
        assert result["session_id"] == test_session_id
        assert result["user_id"] == test_user_id
        assert len(result["content"]) > 0
    
    def test_invoke_conversation_smalltalk_routing(self, mock_llm_factory, test_user_id, test_session_id):
        """Test conversation routes to small talk correctly."""
        # Mock orchestrator to return SMALLTALK, then small talk response
        mock_responses = [
            AIMessage(content="SMALLTALK", additional_kwargs={'refusal': None}),
            AIMessage(content="Hi there! Great day!", additional_kwargs={'refusal': None})
        ]
        mock_llm_factory.invoke.side_effect = mock_responses
        
        config = LangGraphConfig()
        
        result = config.invoke_conversation(
            user_message="Hi there!",
            user_id=test_user_id,
            session_id=test_session_id
        )
        
        # Should route to small_talk agent and get mocked response
        assert "Hi there! Great day!" in result["content"]
    
    def test_stream_conversation(self, mock_llm_factory, test_user_id, test_session_id):
        """Test streaming conversation."""
        # Mock responses for streaming
        mock_responses = [
            AIMessage(content="SMALLTALK", additional_kwargs={'refusal': None}),
            AIMessage(content="Hello from stream!", additional_kwargs={'refusal': None})
        ]
        mock_llm_factory.invoke.side_effect = mock_responses
        
        config = LangGraphConfig()
        
        chunks = []
        for chunk in config.stream_conversation(
            user_message="Hello!",
            user_id=test_user_id,
            session_id=test_session_id
        ):
            chunks.append(chunk)
            
        assert len(chunks) > 0
        # Should have orchestrator and agent chunks
        assert any("orchestrator" in str(chunk) for chunk in chunks)


class TestDummyAgents:
    """Test dummy agent responses."""
    
    def test_dummy_investment_agent(self, mock_llm_factory):
        """Test dummy investment agent."""
        config = LangGraphConfig()
        
        state = GlobalState()
        test_config = {"configurable": {"user_id": "test_user", "thread_id": "test_thread"}}
        
        result = config._dummy_inv_agent(state, test_config)
        
        assert "messages" in result
        response = result["messages"][0]
        assert isinstance(response, AIMessage)
        assert "investment" in response.content.lower()
        assert response.additional_kwargs.get("agent") == "investment"
    
    def test_dummy_spending_agent(self, mock_llm_factory):
        """Test dummy spending agent."""
        config = LangGraphConfig()
        
        state = GlobalState()
        test_config = {"configurable": {"user_id": "test_user", "thread_id": "test_thread"}}
        
        result = config._dummy_spend_agent(state, test_config)
        
        assert "messages" in result
        response = result["messages"][0]
        assert isinstance(response, AIMessage)
        assert "spending" in response.content.lower()
        assert response.additional_kwargs.get("agent") == "spending"
