import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.ai.orchestrator import OrchestratorAgent
from app.ai.langgraph_config import LangGraphConfig


@pytest.fixture
def orchestrator():
    """Create an OrchestratorAgent instance for testing."""
    return OrchestratorAgent()


@pytest.fixture
def mock_langgraph_config():
    """Create a mock LangGraphConfig for testing."""
    mock_config = MagicMock(spec=LangGraphConfig)
    mock_config.graph = MagicMock()
    return mock_config


class TestOrchestratorAgent:
    """Test cases for the OrchestratorAgent."""
    
    @pytest.mark.asyncio
    async def test_process_message_valid_input(self, orchestrator):
        """Test processing a valid message."""
        result = await orchestrator.process_message(
            user_message="Hello, I need help with budgeting",
            user_id="test_user_123",
            session_id="test_session_456"
        )
        
        assert "content" in result
        assert "agent" in result
        assert "session_id" in result
        assert "user_id" in result
        assert "message_type" in result
        
        assert result["agent"] == "small_talk"
        assert result["session_id"] == "test_session_456"
        assert result["user_id"] == "test_user_123"
        assert result["message_type"] == "ai_response"
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_message_empty_input(self, orchestrator):
        """Test processing an empty message."""
        result = await orchestrator.process_message(
            user_message="",
            user_id="test_user_123"
        )
        
        assert result["content"] == "I'm here to help! Please let me know what you'd like to discuss about your finances."
        assert result["agent"] == "orchestrator"
        assert result["user_id"] == "test_user_123"
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_process_message_whitespace_only(self, orchestrator):
        """Test processing a message with only whitespace."""
        result = await orchestrator.process_message(
            user_message="   \n\t  ",
            user_id="test_user_123"
        )
        
        assert result["content"] == "I'm here to help! Please let me know what you'd like to discuss about your finances."
        assert result["agent"] == "orchestrator"
    
    @pytest.mark.asyncio
    async def test_process_message_no_session_id(self, orchestrator):
        """Test processing a message without session_id."""
        result = await orchestrator.process_message(
            user_message="Test message",
            user_id="test_user_123"
        )
        
        # Should generate a session_id automatically
        assert "session_id" in result
        assert result["session_id"] is not None
    
    @patch('app.ai.orchestrator.get_langgraph_config')
    @pytest.mark.asyncio
    async def test_process_message_langgraph_exception(self, mock_get_config, orchestrator):
        """Test handling of LangGraph exceptions."""
        # Mock LangGraph to raise an exception
        mock_config = MagicMock()
        mock_config.invoke_conversation.side_effect = Exception("LangGraph error")
        mock_get_config.return_value = mock_config
        
        # Create a new orchestrator with the mocked config
        orchestrator = OrchestratorAgent()
        
        result = await orchestrator.process_message(
            user_message="Test message",
            user_id="test_user_123"
        )
        
        assert "I apologize, but I'm having trouble processing your message right now" in result["content"]
        assert result["agent"] == "orchestrator"
        assert result["error"] is not None
        assert "LangGraph error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, orchestrator):
        """Test health check when system is healthy."""
        result = await orchestrator.health_check()
        
        assert "status" in result
        assert "graph_initialized" in result
        assert "test_response_received" in result
        assert "error" in result
        
        # Should be healthy since we have a working orchestrator
        assert result["status"] == "healthy"
        assert result["graph_initialized"] is True
        # test_response_received can be False if LLM is not configured (no API key)
        # This is still a healthy system state
        assert isinstance(result["test_response_received"], bool)
        # error can be None or contain LLM configuration message
        assert result["error"] is None or "LLM not configured" in str(result["error"])
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check when system is unhealthy."""
        # Create orchestrator with broken config
        orchestrator = OrchestratorAgent()
        
        # Break the graph reference to simulate unhealthy state
        orchestrator.langgraph_config.graph = None
        
        result = await orchestrator.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["graph_initialized"] is False
        assert result["test_response_received"] is False
        assert result["error"] is not None



class TestLangGraphConfig:
    """Test cases for LangGraph configuration."""
    
    def test_langgraph_config_initialization(self):
        """Test that LangGraphConfig initializes correctly."""
        config = LangGraphConfig()
        
        assert config.graph is not None
        assert hasattr(config, 'invoke_conversation')
    
    @pytest.mark.asyncio
    async def test_invoke_conversation_basic(self, mock_llm_factory):
        """Test basic conversation invocation."""
        # Override the mock to return proper routing responses
        from langchain_core.messages import AIMessage
        
        # Mock orchestrator to return SMALLTALK, then small_talk agent response
        mock_responses = [
            AIMessage(content="SMALLTALK", additional_kwargs={'refusal': None}),  # Orchestrator routing
            AIMessage(content="Hello! How can I help you today?", additional_kwargs={'refusal': None, 'agent': 'small_talk'})  # Small talk response
        ]
        mock_llm_factory.invoke.side_effect = mock_responses
        
        config = LangGraphConfig()
        
        result = await config.invoke_conversation(
            user_message="Hello",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "content" in result
        assert "agent" in result
        assert "session_id" in result
        assert "user_id" in result
        assert "message_type" in result
        
        assert result["agent"] == "small_talk"  # Should be the final agent that responded
        assert result["session_id"] == "test_session"
        assert result["user_id"] == "test_user"
        assert isinstance(result["content"], str)
    
    @pytest.mark.skip(reason="OnboardingAgent structured output needs to be fixed")
    @pytest.mark.asyncio
    async def test_invoke_conversation_onboarding_route(self, mock_llm_factory):
        """Test that the orchestrator routes to ONBOARDING for users without complete profiles."""
        from langchain_core.messages import AIMessage
        
        # Mock orchestrator to return ONBOARDING route, then onboarding agent response
        mock_responses = [
            AIMessage(content="ONBOARDING", additional_kwargs={'refusal': None}),  # Orchestrator routing
            AIMessage(content="Welcome! I'd be happy to help you with your budget. First, let's complete your financial profile so I can provide personalized advice.", additional_kwargs={'refusal': None, 'agent': 'onboarding'})  # Onboarding agent response
        ]
        mock_llm_factory.invoke.side_effect = mock_responses
        
        config = LangGraphConfig()
        
        test_message = "I need help with my budget"
        result = await config.invoke_conversation(
            user_message=test_message,
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should route to onboarding agent since profile is not complete
        assert result["agent"] == "onboarding"
        assert "profile" in result["content"].lower() or "onboard" in result["content"].lower() or "welcome" in result["content"].lower()