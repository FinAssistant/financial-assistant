from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
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

    # AI/LangGraph settings
    ai_model_name: str = Field(default="gpt-3.5-turbo", description="AI model to use")
    ai_temperature: float = Field(default=0.7, description="AI response temperature")
    ai_max_tokens: int = Field(default=500, description="Maximum tokens for AI responses")
    langgraph_memory_type: str = Field(default="in_memory", description="LangGraph memory backend")
    conversation_timeout: int = Field(default=300, description="Conversation timeout in seconds")


# Global settings instance
settings = Settings()