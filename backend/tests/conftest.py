"""
Test configuration and fixtures.
Always mocks LLM calls by default for reliable CI testing.
"""
import os
import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage


@pytest.fixture(autouse=True)
def mock_llm_factory():
    """
    Auto-applied fixture that mocks all LLM calls by default.
    This ensures tests run reliably without API keys.
    """
    with patch('app.services.llm_service.llm_factory.create_llm') as mock_factory:
        mock_llm = Mock()
        mock_llm.invoke.return_value = AIMessage(
            content="SMALLTALK",  # Valid routing response for orchestrator
            additional_kwargs={'refusal': None}
        )
        mock_factory.return_value = mock_llm
        yield mock_llm


@pytest.fixture
def mock_orchestrator_routing():
    """
    Fixture for orchestrator routing tests.
    Returns different routing responses based on test needs.
    """
    def _create_routing_response(route: str):
        with patch('app.services.llm_service.llm_factory.create_llm') as mock_factory:
            mock_llm = Mock()
            mock_llm.invoke.return_value = AIMessage(
                content=route,
                additional_kwargs={'refusal': None}
            )
            mock_factory.return_value = mock_llm
            return mock_llm
    return _create_routing_response


@pytest.fixture
def mock_small_talk_response():
    """Fixture for small talk agent tests."""
    with patch('app.services.llm_service.llm_factory.create_llm') as mock_factory:
        mock_llm = Mock()
        mock_llm.invoke.return_value = AIMessage(
            content="Hi there! How can I help you today?",
            additional_kwargs={'refusal': None, 'agent': 'small_talk'}
        )
        mock_factory.return_value = mock_llm
        yield mock_llm


@pytest.fixture
def test_user_id():
    """Standard test user ID."""
    return "test_user_123"


@pytest.fixture  
def test_session_id():
    """Standard test session ID."""
    return "test_session_123"


# Print test environment info
def pytest_configure(config):
    """Print test configuration on startup."""
    has_key = bool(os.getenv('OPENAI_API_KEY'))
    real_tests = os.getenv('RUN_REAL_TESTS') == 'true'
    
    print("\n=== Test Environment ===")
    print(f"Has OpenAI Key: {has_key}")
    print(f"Real API Tests: {real_tests}")
    print(f"LLM Mocking: {'DISABLED' if real_tests else 'ENABLED'}")
    print("========================\n")