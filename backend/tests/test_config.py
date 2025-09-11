import pytest
from app.core.config import Settings


def test_default_settings():
    """Test default configuration values."""
    settings = Settings(_env_file=None)
    
    assert settings.app_name == "AI Financial Assistant"
    assert settings.app_version == "0.1.0"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.debug is False
    assert settings.environment == "development"
    assert settings.static_dir == "app/static"
    # Test new Plaid defaults
    assert settings.plaid_client_id is None
    assert settings.plaid_secret is None
    assert settings.plaid_env == "sandbox"
    assert settings.plaid_products == ["identity", "transactions", "liabilities", "investments"]


def test_cors_origins_default():
    """Test default CORS origins."""
    settings = Settings()
    
    expected_origins = ["http://localhost:3000", "http://localhost:5173"]
    assert settings.cors_origins == expected_origins


def test_settings_with_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    
    settings = Settings()
    
    assert settings.app_name == "Test App"
    assert settings.debug is True
    assert settings.port == 9000


def test_llm_provider_defaults():
    """Test default LLM provider configuration."""
    settings = Settings(_env_file=None)
    
    assert settings.openai_api_key is None
    assert settings.anthropic_api_key is None
    assert settings.google_api_key is None
    assert settings.default_llm_provider == "openai"
    assert settings.openai_model == "gpt-4o"
    assert settings.anthropic_model == "claude-sonnet-4-20250514"
    assert settings.google_model == "gemini-2.5-flash"
    assert settings.llm_max_tokens == 4096
    assert settings.llm_temperature == 0.7
    assert settings.llm_request_timeout == 60


def test_llm_provider_validation():
    """Test LLM provider validation."""
    # Test valid providers
    for provider in ["openai", "anthropic", "google"]:
        settings = Settings(default_llm_provider=provider)
        assert settings.default_llm_provider == provider
    
    # Test invalid provider
    with pytest.raises(ValueError, match="default_llm_provider must be one of"):
        Settings(default_llm_provider="invalid_provider")


def test_llm_credential_validation_openai(monkeypatch):
    """Test OpenAI credential validation."""
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    
    settings = Settings()
    assert settings.validate_llm_credentials() is True


def test_llm_credential_validation_anthropic(monkeypatch):
    """Test Anthropic credential validation."""
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
    
    settings = Settings()
    assert settings.validate_llm_credentials() is True


def test_llm_credential_validation_google(monkeypatch):
    """Test Google credential validation."""
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyTest123456789012345")
    
    settings = Settings()
    assert settings.validate_llm_credentials() is True


def test_llm_credential_validation_failures(monkeypatch):
    """Test LLM credential validation failures."""
    # Missing OpenAI key
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    settings = Settings()
    assert settings.validate_llm_credentials() is False
    
    # Invalid OpenAI key format
    monkeypatch.setenv("OPENAI_API_KEY", "invalid-key")
    settings = Settings()
    assert settings.validate_llm_credentials() is False
    
    # Missing Anthropic key
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    settings = Settings()
    assert settings.validate_llm_credentials() is False
    
    # Invalid Anthropic key format
    monkeypatch.setenv("ANTHROPIC_API_KEY", "invalid-key")
    settings = Settings()
    assert settings.validate_llm_credentials() is False
    
    # Missing Google key
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    settings = Settings()
    assert settings.validate_llm_credentials() is False
    
    # Invalid Google key (too short)
    monkeypatch.setenv("GOOGLE_API_KEY", "short")
    settings = Settings()
    assert settings.validate_llm_credentials() is False
