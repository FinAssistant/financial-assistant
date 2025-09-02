from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    
    # AI/LangGraph settings
    ai_model_name: str = Field(default="gpt-3.5-turbo", description="AI model to use")
    ai_temperature: float = Field(default=0.7, description="AI response temperature")
    ai_max_tokens: int = Field(default=500, description="Maximum tokens for AI responses")
    langgraph_memory_type: str = Field(default="in_memory", description="LangGraph memory backend")
    conversation_timeout: int = Field(default=300, description="Conversation timeout in seconds")
    
    # Plaid API settings
    plaid_client_id: Optional[str] = Field(default=None, description="Plaid client ID")
    plaid_secret: Optional[str] = Field(default=None, description="Plaid secret key")
    plaid_env: str = Field(default="sandbox", description="Plaid environment (sandbox|production)")
    plaid_products: List[str] = Field(
        default_factory=lambda: ["identity", "transactions", "liabilities", "investments"],
        description="Plaid products to use"
    )

# Global settings instance
settings = Settings()