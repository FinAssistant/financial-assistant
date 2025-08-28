import pytest
from unittest.mock import patch, MagicMock
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
    
    def test_process_message_valid_input(self, orchestrator):
        """Test processing a valid message."""
        result = orchestrator.process_message(
            user_message="Hello, I need help with budgeting",
            user_id="test_user_123",
            session_id="test_session_456"
        )
        
        assert "content" in result
        assert "agent" in result
        assert "session_id" in result
        assert "user_id" in result
        assert "message_type" in result
        
        assert result["agent"] == "orchestrator"
        assert result["session_id"] == "test_session_456"
        assert result["user_id"] == "test_user_123"
        assert result["message_type"] == "ai_response"
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
    
    def test_process_message_empty_input(self, orchestrator):
        """Test processing an empty message."""
        result = orchestrator.process_message(
            user_message="",
            user_id="test_user_123"
        )
        
        assert result["content"] == "I'm here to help! Please let me know what you'd like to discuss about your finances."
        assert result["agent"] == "orchestrator"
        assert result["user_id"] == "test_user_123"
        assert result["error"] is None
    
    def test_process_message_whitespace_only(self, orchestrator):
        """Test processing a message with only whitespace."""
        result = orchestrator.process_message(
            user_message="   \n\t  ",
            user_id="test_user_123"
        )
        
        assert result["content"] == "I'm here to help! Please let me know what you'd like to discuss about your finances."
        assert result["agent"] == "orchestrator"
    
    def test_process_message_no_session_id(self, orchestrator):
        """Test processing a message without session_id."""
        result = orchestrator.process_message(
            user_message="Test message",
            user_id="test_user_123"
        )
        
        # Should generate a session_id automatically
        assert "session_id" in result
        assert result["session_id"] is not None
    
    @patch('app.ai.orchestrator.get_langgraph_config')
    def test_process_message_langgraph_exception(self, mock_get_config, orchestrator):
        """Test handling of LangGraph exceptions."""
        # Mock LangGraph to raise an exception
        mock_config = MagicMock()
        mock_config.invoke_conversation.side_effect = Exception("LangGraph error")
        mock_get_config.return_value = mock_config
        
        # Create a new orchestrator with the mocked config
        orchestrator = OrchestratorAgent()
        
        result = orchestrator.process_message(
            user_message="Test message",
            user_id="test_user_123"
        )
        
        assert "I apologize, but I'm having trouble processing your message right now" in result["content"]
        assert result["agent"] == "orchestrator"
        assert result["error"] is not None
        assert "LangGraph error" in result["error"]
    
    def test_health_check_healthy(self, orchestrator):
        """Test health check when system is healthy."""
        result = orchestrator.health_check()
        
        assert "status" in result
        assert "graph_initialized" in result
        assert "test_response_received" in result
        assert "error" in result
        
        # Should be healthy since we have a working orchestrator
        assert result["status"] == "healthy"
        assert result["graph_initialized"] is True
        assert result["test_response_received"] is True
        assert result["error"] is None
    
    def test_health_check_unhealthy(self):
        """Test health check when system is unhealthy."""
        # Create orchestrator with broken config
        orchestrator = OrchestratorAgent()
        
        # Break the graph reference to simulate unhealthy state
        orchestrator.langgraph_config.graph = None
        
        result = orchestrator.health_check()
        
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
    
    def test_invoke_conversation_basic(self):
        """Test basic conversation invocation."""
        config = LangGraphConfig()
        
        result = config.invoke_conversation(
            user_message="Hello",
            user_id="test_user",
            session_id="test_session"
        )
        
        assert "content" in result
        assert "agent" in result
        assert "session_id" in result
        assert "user_id" in result
        assert "message_type" in result
        
        assert result["agent"] == "orchestrator"
        assert result["session_id"] == "test_session"
        assert result["user_id"] == "test_user"
        assert isinstance(result["content"], str)
    
    def test_invoke_conversation_echo_response(self):
        """Test that the orchestrator provides an appropriate response."""
        config = LangGraphConfig()
        
        test_message = "I need help with my budget"
        result = config.invoke_conversation(
            user_message=test_message,
            user_id="test_user",
            session_id="test_session"
        )
        
        # Should acknowledge the user's message
        assert test_message in result["content"] or "help" in result["content"].lower()
        assert "financial" in result["content"].lower() or "help" in result["content"].lower()