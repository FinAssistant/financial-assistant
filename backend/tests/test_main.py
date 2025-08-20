import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "environment" in data


def test_api_health_check():
    """Test the API health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api"] == "running"
    assert "app" in data
    assert "version" in data


def test_nonexistent_api_endpoint():
    """Test that non-existent API endpoints return 404."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


def test_app_creation():
    """Test that the FastAPI app is created correctly."""
    assert app.title == "AI Financial Assistant"
    assert app.version == "0.1.0"