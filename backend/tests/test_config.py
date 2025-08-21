import pytest
from app.core.config import Settings


def test_default_settings():
    """Test default configuration values."""
    settings = Settings()
    
    assert settings.app_name == "AI Financial Assistant"
    assert settings.app_version == "0.1.0"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.debug is False
    assert settings.environment == "development"
    assert settings.static_dir == "app/static"


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