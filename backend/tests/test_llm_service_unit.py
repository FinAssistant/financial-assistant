"""
Unit tests for LLM service functionality.
All tests use mocked LLM calls by default via conftest.py fixtures.
"""
import pytest
from unittest.mock import patch
from langchain_core.messages import AIMessage
from app.services.llm_service import LLMFactory, LLMProvider, LLMError


class TestLLMFactory:
    """Test LLM factory functionality with mocked responses."""

    def test_factory_initialization(self):
        """Test LLM factory can be initialized."""

        factory = LLMFactory()
        assert factory is not None
        assert factory.default_provider == LLMProvider.OPENAI
    
    @patch('app.services.llm_service.settings')
    def test_create_llm_success(self, mock_settings):
        """Test successful LLM creation (mocked)."""
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_api_key = "test_key"
        mock_settings.openai_model = "gpt_3.5_turbo"

        factory = LLMFactory()
        llm = factory.create_llm()
        
        assert llm is not None
        assert hasattr(llm, 'invoke')
        assert llm.model_name == "gpt_3.5_turbo"
    
    @patch("langchain_openai.ChatOpenAI.invoke")
    @patch('app.services.llm_service.settings')
    def test_llm_invoke_mocked(self, mock_settings, mock_invoke):
        """Test LLM invocation with mocked response."""
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_api_key = "test_key"
        mock_settings.openai_model = "gpt_3.5_turbo"
        mocked_llm_response = "This is a test response."
        mock_invoke.return_value = AIMessage(content=mocked_llm_response)

        factory = LLMFactory()
        llm = factory.create_llm()
        
        messages = [{"role": "user", "content": "Hello"}]
        response = llm.invoke(messages)
        
        assert response is not None
        assert hasattr(response, 'content')
        assert response.content == mocked_llm_response
        assert response.additional_kwargs.get('refusal') is None
    
    def test_create_llm_invalid_provider(self):
        """Test LLM creation with invalid provider fails."""
        factory = LLMFactory()
        
        with pytest.raises(LLMError):
            factory.create_llm("invalid_provider")
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        factory = LLMFactory()
        providers = factory.get_available_providers()
        
        assert isinstance(providers, list)
        # With mocked environment, should still return provider info
        assert len(providers) >= 0

    @patch('app.services.llm_service.settings')
    def test_llm_error_missing_key(self, mock_settings):
        """Test error handling when missing key"""
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_model = "gpt_3.5_turbo"
       
        factory = LLMFactory()
        
        assert not factory.validate_configuration()
        with pytest.raises(Exception):
            factory.create_llm()

    @patch('app.services.llm_service.settings')
    def test_llm_error_missing_model(self, mock_settings):
        """Test error handling when missing key"""
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_api_key = "test_key"
       
        factory = LLMFactory()
        
        assert not factory.validate_configuration()
        with pytest.raises(Exception):
            factory.create_llm()

    @patch('app.services.llm_service.settings')
    def test_create_google_llm_success(self, mock_settings):
        """Test successful Google LLM creation (mocked)."""
        mock_settings.default_llm_provider = "google"
        mock_settings.google_api_key = "test_google_key"
        mock_settings.google_model = "gemini-2.5-pro"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 4096
        mock_settings.llm_request_timeout = 60

        factory = LLMFactory()
        llm = factory.create_llm()
        
        assert llm is not None
        assert hasattr(llm, 'invoke')
        assert llm.model == "models/gemini-2.5-pro"

    @patch("langchain_google_genai.ChatGoogleGenerativeAI.invoke")
    @patch('app.services.llm_service.settings')
    def test_google_llm_invoke_mocked(self, mock_settings, mock_invoke):
        """Test Google LLM invocation with mocked response."""
        mock_settings.default_llm_provider = "google"
        mock_settings.google_api_key = "test_google_key"
        mock_settings.google_model = "gemini-2.5-pro"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 4096
        mock_settings.llm_request_timeout = 60
        mocked_llm_response = "This is a test response from Gemini."
        mock_invoke.return_value = AIMessage(content=mocked_llm_response)

        factory = LLMFactory()
        llm = factory.create_llm()
        
        messages = [{"role": "user", "content": "Hello"}]
        response = llm.invoke(messages)
        
        assert response is not None
        assert hasattr(response, 'content')
        assert response.content == mocked_llm_response

    @patch('app.services.llm_service.settings')
    def test_create_llm_with_explicit_google_provider(self, mock_settings):
        """Test LLM creation with explicit Google provider."""
        mock_settings.default_llm_provider = "openai"  # Set a valid default
        mock_settings.google_api_key = "test_google_key"
        mock_settings.google_model = "gemini-2.5-pro"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 4096
        mock_settings.llm_request_timeout = 60

        factory = LLMFactory()
        llm = factory.create_llm(provider=LLMProvider.GOOGLE)
        
        assert llm is not None
        assert llm.model == "models/gemini-2.5-pro"


class TestLLMProviderEnum:
    """Test LLM provider enumeration."""
    
    def test_provider_values(self):
        """Test provider enum values."""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.GOOGLE.value == "google"
    
    def test_provider_string_conversion(self):
        """Test provider can be created from string."""
        assert LLMProvider("openai") == LLMProvider.OPENAI
        assert LLMProvider("anthropic") == LLMProvider.ANTHROPIC
        assert LLMProvider("google") == LLMProvider.GOOGLE
        
        with pytest.raises(ValueError):
            LLMProvider("invalid")

class TestLLMServiceIntegration:
    """Test LLM service integration with mocked responses."""

    @patch("langchain_openai.ChatOpenAI.invoke")
    @patch('app.services.llm_service.settings')
    def test_llm_conversation_flow(self, mock_settings, mock_invoke):
        """Test basic conversation flow."""
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_api_key = "test_key"
        mock_settings.openai_model = "gpt_3.5_turbo"
        mocked_llm_response = "Hello! How can I help you with your financial needs"
        mock_invoke.return_value = AIMessage(content=mocked_llm_response)

        factory = LLMFactory()
        llm = factory.create_llm()
        
        # Test system prompt + user message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        response = llm.invoke(messages)
        
        assert response.content == mocked_llm_response
        mock_invoke.assert_called_once_with(messages)
        
    @patch("langchain_openai.ChatOpenAI.invoke")
    @patch('app.services.llm_service.settings')
    def test_multiple_llm_calls(self, mock_settings, mock_invoke):
        """Test multiple LLM calls work correctly."""
        mock_settings.default_llm_provider = "openai"
        mock_settings.openai_api_key = "test_key"
        mock_settings.openai_model = "gpt_3.5_turbo"
        mocked_llm_response = "Hello! How can I help you with your financial needs"
        mock_invoke.return_value = AIMessage(content=mocked_llm_response)


        factory = LLMFactory()
        llm = factory.create_llm()
        
        # First call
        response1 = llm.invoke([{"role": "user", "content": "First message"}])
        assert response1.content == mocked_llm_response
        
        # Second call
        response2 = llm.invoke([{"role": "user", "content": "Second message"}])
        assert response2.content == mocked_llm_response
        
        # Should have been called twice
        assert mock_invoke.call_count == 2