from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging


class Settings(BaseSettings):
    """Application configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],  # Check both current dir and parent dir
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="AI Financial Assistant", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    # Static files
    static_dir: str = Field(default="app/static", description="Static files directory")
    
    # Security
    secret_key: Optional[str] = Field(default=None, description="Secret key for JWT")
    
    # Environment
    environment: str = Field(default="development", description="Environment (development|production)")
    
    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./financial_assistant.db",
        description="Database URL for SQLite persistence"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries for debugging")

    # LLM Provider settings
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    default_llm_provider: str = Field(default="openai", description="Default LLM provider (openai|anthropic)")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", description="Anthropic model to use")
    llm_max_tokens: int = Field(default=4096, description="Maximum tokens for LLM responses")
    llm_temperature: float = Field(default=0.7, description="LLM response temperature")
    llm_request_timeout: int = Field(default=60, description="LLM request timeout in seconds")
    
    # LangGraph settings
    langgraph_memory_type: str = Field(default="sqlite", description="LangGraph memory backend")
    langgraph_db_path: str = Field(default="./langgraph_checkpoints.db", description="Path to LangGraph checkpoint database")
    conversation_timeout: int = Field(default=300, description="Conversation timeout in seconds")
    
    # Plaid API settings
    plaid_client_id: Optional[str] = Field(default=None, description="Plaid client ID")
    plaid_secret: Optional[str] = Field(default=None, description="Plaid secret key")
    plaid_env: str = Field(default="sandbox", description="Plaid environment (sandbox|production)")
    plaid_products: List[str] = Field(
        default_factory=lambda: ["identity", "transactions", "liabilities", "investments"],
        description="Plaid products to use"
    )

    @field_validator('default_llm_provider')
    @classmethod
    def validate_llm_provider(cls, v):
        """Validate that the default LLM provider is supported."""
        allowed_providers = ["openai", "anthropic"]
        if v not in allowed_providers:
            raise ValueError(f"default_llm_provider must be one of {allowed_providers}")
        return v

    def validate_llm_credentials(self) -> bool:
        """Validate LLM credentials are available for the configured provider."""
        logger = logging.getLogger(__name__)
        
        if self.default_llm_provider == "openai":
            if not self.openai_api_key:
                logger.error("OpenAI API key is required when using OpenAI as the default provider")
                return False
            if not self.openai_api_key.startswith("sk-"):
                logger.error("OpenAI API key appears to be invalid (should start with 'sk-')")
                return False
                
        elif self.default_llm_provider == "anthropic":
            if not self.anthropic_api_key:
                logger.error("Anthropic API key is required when using Anthropic as the default provider")
                return False
            if not self.anthropic_api_key.startswith("sk-ant-"):
                logger.error("Anthropic API key appears to be invalid (should start with 'sk-ant-')")
                return False
        
        logger.info(f"LLM credentials validated for provider: {self.default_llm_provider}")
        return True

# Global settings instance
settings = Settings()