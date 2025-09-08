from typing import Optional, Union
from enum import Enum
import logging

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

from app.core.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMError(Exception):
    """Base exception for LLM service errors."""
    pass


class LLMFactory:
    """
    Factory for creating LangGraph-compatible LLM instances.
    
    Creates ChatOpenAI or ChatAnthropic instances based on configuration
    with proper error handling and validation.
    """
    
    def __init__(self):
        """Initialize LLM factory."""
        self.logger = logging.getLogger(__name__)
        self.default_provider = LLMProvider(settings.default_llm_provider)
    
    def create_llm(self, provider: Optional[LLMProvider] = None) -> Union[ChatOpenAI, ChatAnthropic]:
        """
        Create LangGraph-compatible LLM instance.
        
        Args:
            provider: Specific provider to use (defaults to configured default)
            
        Returns:
            LangGraph LLM instance (ChatOpenAI or ChatAnthropic)
            
        Raises:
            LLMError: If provider not available or credentials invalid
        """
        target_provider = provider or self.default_provider
        
        if target_provider == LLMProvider.OPENAI:
            return self._create_openai_llm()
        elif target_provider == LLMProvider.ANTHROPIC:
            return self._create_anthropic_llm()
        else:
            raise LLMError(f"Unsupported provider: {target_provider}")
    
    def _create_openai_llm(self) -> ChatOpenAI:
        """Create ChatOpenAI instance."""
        if not ChatOpenAI:
            raise LLMError("langchain_openai not installed")
        
        if not settings.openai_api_key:
            raise LLMError("OpenAI API key not configured")
        
        try:
            llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout=settings.llm_request_timeout
            )
            self.logger.info(f"Created OpenAI LLM with model: {settings.openai_model}")
            return llm
        except Exception as e:
            raise LLMError(f"Failed to create OpenAI LLM: {e}")
    
    def _create_anthropic_llm(self) -> ChatAnthropic:
        """Create ChatAnthropic instance."""
        if not ChatAnthropic:
            raise LLMError("langchain_anthropic not installed")
        
        if not settings.anthropic_api_key:
            raise LLMError("Anthropic API key not configured")
        
        try:
            llm = ChatAnthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout=settings.llm_request_timeout
            )
            self.logger.info(f"Created Anthropic LLM with model: {settings.anthropic_model}")
            return llm
        except Exception as e:
            raise LLMError(f"Failed to create Anthropic LLM: {e}")
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of available providers based on configuration and dependencies."""
        available = []
        
        if settings.openai_api_key and ChatOpenAI:
            available.append(LLMProvider.OPENAI)
        
        if settings.anthropic_api_key and ChatAnthropic:
            available.append(LLMProvider.ANTHROPIC)
        
        return available
    
    def validate_configuration(self) -> bool:
        """Validate LLM configuration and credentials."""
        try:
            # Validate credentials using the settings method
            if not settings.validate_llm_credentials():
                return False
            
            # Ensure we can create the default LLM
            self.create_llm()
            self.logger.info("LLM configuration validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"LLM configuration validation failed: {e}")
            return False


# Global factory instance
llm_factory = LLMFactory()