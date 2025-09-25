import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.ai.conversation_handler import ConversationHandler
from app.ai.orchestrator_agent import OrchestratorAgent


@pytest.fixture
def conversation_handler():
    """Create a ConversationHandler instance for testing."""
    return ConversationHandler()


@pytest.fixture
def mock_orchestrator_agent():
    """Create a mock OrchestratorAgent for testing."""
    mock_agent = MagicMock(spec=OrchestratorAgent)
    mock_agent.graph = MagicMock()
    return mock_agent


class TestConversationHandler:
    """Test cases for the ConversationHandler."""

    @pytest.mark.asyncio
    async def test_process_message_valid_input(self, conversation_handler):
        """Test processing a valid message."""
        result = await conversation_handler.process_message(
            user_message="Hello, I need help with budgeting",
            user_id="test_user_123",
            session_id="test_session_456"
        )

        assert "messages" in result
        assert "session_id" in result
        assert "user_id" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) > 0

        # Check first message
        first_message = result["messages"][0]
        assert first_message["agent"] == "small_talk"
        assert result["session_id"] == "test_session_456"
        assert result["user_id"] == "test_user_123"
        assert first_message["message_type"] == "ai_response"
        assert isinstance(first_message["content"], str)
        assert len(first_message["content"]) > 0

    @pytest.mark.asyncio
    async def test_process_message_empty_input(self, conversation_handler):
        """Test processing an empty message."""
        result = await conversation_handler.process_message(
            user_message="",
            user_id="test_user_123"
        )

        assert "messages" in result
        assert len(result["messages"]) == 1

        first_message = result["messages"][0]
        assert first_message["content"] == "I'm here to help! Please let me know what you'd like to discuss about your finances."
        assert first_message["agent"] == "orchestrator"
        assert result["user_id"] == "test_user_123"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_process_message_whitespace_only(self, conversation_handler):
        """Test processing a message with only whitespace."""
        result = await conversation_handler.process_message(
            user_message="   \n\t  ",
            user_id="test_user_123"
        )

        assert "messages" in result
        assert len(result["messages"]) == 1

        first_message = result["messages"][0]
        assert first_message["content"] == "I'm here to help! Please let me know what you'd like to discuss about your finances."
        assert first_message["agent"] == "orchestrator"

    @pytest.mark.asyncio
    async def test_process_message_no_session_id(self, conversation_handler):
        """Test processing a message without session_id."""
        result = await conversation_handler.process_message(
            user_message="Test message",
            user_id="test_user_123"
        )

        # Should generate a session_id automatically
        assert "session_id" in result
        assert result["session_id"] is not None

    @patch('app.ai.conversation_handler.get_orchestrator_agent')
    @pytest.mark.asyncio
    async def test_process_message_orchestrator_exception(self, mock_get_agent, conversation_handler):
        """Test handling of OrchestratorAgent exceptions."""
        # Mock OrchestratorAgent to raise an exception
        mock_agent = MagicMock()
        mock_agent.invoke_conversation.side_effect = Exception("OrchestratorAgent error")
        mock_get_agent.return_value = mock_agent

        # Create a new conversation handler with the mocked agent
        conversation_handler = ConversationHandler()

        result = await conversation_handler.process_message(
            user_message="Test message",
            user_id="test_user_123"
        )

        assert "messages" in result
        assert len(result["messages"]) == 1

        first_message = result["messages"][0]
        assert "I apologize, but I'm having trouble processing your message right now" in first_message["content"]
        assert first_message["agent"] == "orchestrator"
        assert result["error"] is not None
        assert "OrchestratorAgent error" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, conversation_handler):
        """Test health check when system is healthy."""
        result = await conversation_handler.health_check()

        assert "status" in result
        assert "graph_initialized" in result
        assert "test_response_received" in result
        assert "error" in result

        # Should be healthy since we have a working conversation handler
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
        # Create conversation handler with broken config
        conversation_handler = ConversationHandler()

        # Break the graph reference to simulate unhealthy state
        conversation_handler.orchestrator_agent.graph = None

        result = await conversation_handler.health_check()

        assert result["status"] == "unhealthy"
        assert result["graph_initialized"] is False
        assert result["test_response_received"] is False
        assert result["error"] is not None

    @patch('app.ai.conversation_handler.get_orchestrator_agent')
    @pytest.mark.asyncio
    async def test_process_message_multiple_messages(self, mock_get_agent):
        """Test handling of multiple AI messages from orchestrator (e.g., onboarding account connection)."""
        # Mock orchestrator to return multiple messages like the onboarding agent does
        mock_agent = AsyncMock()
        mock_agent.invoke_conversation.return_value = {
            "messages": [
                {
                    "content": "Perfect! Now that we have your demographic information, let's connect your bank accounts for personalized financial insights. I'll generate a secure link for you.",
                    "agent": "onboarding",
                    "message_type": "ai_response"
                },
                {
                    "content": "Here's your secure Plaid link: https://cdn.plaid.com/link/v2/stable/link.html?isWebview=false&token=link-sandbox-12345",
                    "agent": "onboarding",
                    "message_type": "ai_response"
                }
            ],
            "session_id": "test_session",
            "user_id": "test_user"
        }
        mock_get_agent.return_value = mock_agent

        conversation_handler = ConversationHandler()

        result = await conversation_handler.process_message(
            user_message="I am 35 years old and want to connect my accounts",
            user_id="test_user",
            session_id="test_session"
        )

        # Verify the multi-message structure is preserved
        assert "messages" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) == 2

        # Verify first message (guidance)
        first_msg = result["messages"][0]
        assert "demographic information" in first_msg["content"]
        assert first_msg["agent"] == "onboarding"
        assert first_msg["message_type"] == "ai_response"

        # Verify second message (Plaid link)
        second_msg = result["messages"][1]
        assert "Plaid link" in second_msg["content"]
        assert "link-sandbox" in second_msg["content"]
        assert second_msg["agent"] == "onboarding"
        assert second_msg["message_type"] == "ai_response"

        # Verify session metadata
        assert result["session_id"] == "test_session"
        assert result["user_id"] == "test_user"



class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent configuration."""

    def test_orchestrator_agent_initialization(self):
        """Test that OrchestratorAgent initializes correctly."""
        config = OrchestratorAgent()

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

        config = OrchestratorAgent()

        result = await config.invoke_conversation(
            user_message="Hello",
            user_id="test_user",
            session_id="test_session"
        )

        assert "messages" in result
        assert "session_id" in result
        assert "user_id" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) == 2

        # Check first message has expected structure
        first_message = result["messages"][0]
        assert "content" in first_message
        assert "agent" in first_message
        assert "message_type" in first_message

        assert first_message["agent"] == "orchestrator"  # Should be the orchestrator routing message
        assert result["session_id"] == "test_session"
        assert result["user_id"] == "test_user"
        assert first_message["content"] == "SMALLTALK"  # Orchestrator routing message

        # Check first message has expected structure
        second_message = result["messages"][1]
        assert "content" in second_message
        assert "agent" in second_message
        assert "message_type" in second_message

        assert second_message["agent"] == "small_talk"  # Should be the final agent that responded
        assert result["session_id"] == "test_session"
        assert result["user_id"] == "test_user"
        assert isinstance(second_message["content"], str)

    @pytest.mark.asyncio
    async def test_invoke_conversation_onboarding_route(self, mock_llm_factory):
        """Test that the orchestrator routes to ONBOARDING for users without complete profiles."""
        from langchain_core.messages import AIMessage
        from unittest.mock import Mock

        # Create a mock structured output response for onboarding agent
        mock_structured_response = Mock()
        mock_structured_response.user_response = "Welcome! I'd be happy to help you with your budget. First, let's complete your financial profile so I can provide personalized advice."
        mock_structured_response.extracted_data.model_dump.return_value = {}
        mock_structured_response.completion_status = "incomplete"

        # Create a mock structured LLM
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_structured_response

        # Mock the regular LLM invoke for orchestrator routing
        mock_llm_factory.invoke.return_value = AIMessage(content="ONBOARDING", additional_kwargs={'refusal': None})
        # Mock the with_structured_output method for onboarding agent
        mock_llm_factory.with_structured_output.return_value = mock_structured_llm

        config = OrchestratorAgent()

        test_message = "I need help with my budget"
        result = await config.invoke_conversation(
            user_message=test_message,
            user_id="test_user",
            session_id="test_session"
        )

        # Should route to onboarding agent since profile is not complete
        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert last_message["agent"] == "onboarding"
        assert "profile" in last_message["content"].lower() or "onboard" in last_message["content"].lower() or "welcome" in last_message["content"].lower()