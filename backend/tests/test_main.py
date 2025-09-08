import pytest
from app.main import app, health_check, api_health_check


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    response = await health_check()
    assert response["status"] == "healthy"
    assert "app" in response
    assert "version" in response
    assert "environment" in response


@pytest.mark.asyncio
async def test_api_health_check():
    """Test the API health check endpoint."""
    response = await api_health_check()
    assert response["status"] == "healthy"
    assert response["api"] == "running"
    assert "app" in response
    assert "version" in response


def test_app_creation():
    """Test that the FastAPI app is created correctly."""
    assert app.title == "AI Financial Assistant"
    assert app.version == "0.1.0"