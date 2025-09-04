import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from fastapi import Depends

from app.main import create_app
from app.services.auth_service import auth_service
from app.routers.auth import get_current_user


# Mock function for auth dependency
def mock_get_current_user():
    """Mock authentication dependency."""
    return "test_user_123"


@pytest.fixture
def app():
    """Create FastAPI test application with mocked auth."""
    app = create_app()
    # Override the auth dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def unauthenticated_app():
    """Create FastAPI test application without mocked auth."""
    return create_app()


@pytest.fixture
def unauthenticated_client(unauthenticated_app):
    """Create test client without auth override."""
    return TestClient(unauthenticated_app)


class TestConversationEndpoints:
    """Test cases for conversation API endpoints."""
    
    def test_send_message_success(self, client):
        """Test successful message sending with AI SDK format."""
        response = client.post(
            "/conversation/message",
            json={
                "messages": [
                    {
                        "id": "test-msg-1",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": "Hello, I need help with budgeting"
                            }
                        ]
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "content" in data
        assert "role" in data
        assert "agent" in data
        assert "session_id" in data
        assert "user_id" in data
        assert "created_at" in data
        
        assert data["role"] == "assistant"
        assert data["agent"] == "orchestrator"
        assert data["user_id"] == "test_user_123"
        assert data["session_id"] == "session_test_user_123"
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0
    
    def test_send_message_with_custom_session_id(self, client):
        """Test message sending with custom session ID."""
        custom_session_id = "custom_session_456"
        
        response = client.post(
            "/conversation/message",
            json={
                "messages": [
                    {
                        "id": "test-msg-2",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": "Test message"
                            }
                        ]
                    }
                ], 
                "session_id": custom_session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == custom_session_id
    
    def test_send_message_empty_messages_array(self, client):
        """Test sending empty messages array."""
        response = client.post(
            "/conversation/message",
            json={"messages": []}
        )
        
        # Pydantic validation happens first, so we get 422 not 400  
        assert response.status_code == 422
        error_details = response.json()["detail"]
        # Check that validation error mentions messages length
        assert any("at least 1 item" in str(error) for error in error_details)
    
    def test_send_message_whitespace_only(self, client):
        """Test sending message with only whitespace."""
        response = client.post(
            "/conversation/message",
            json={
                "messages": [
                    {"role": "user", "content": "   \n\t  "}
                ]
            }
        )
        
        # This passes Pydantic validation but fails our custom validation
        assert response.status_code == 400
        assert "No valid user message found" in response.json()["detail"]
    
    def test_send_message_unauthorized(self, unauthenticated_client):
        """Test sending message without authentication."""
        response = unauthenticated_client.post(
            "/conversation/message",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )
        
        assert response.status_code == 403  # Missing authorization header
    
    def test_send_message_invalid_token(self, unauthenticated_client):
        """Test sending message with invalid token."""
        response = unauthenticated_client.post(
            "/conversation/message",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            },
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_streaming_endpoint_success(self, client):
        """Test streaming conversation endpoint with AI SDK format."""
        response = client.post(
            "/conversation/send",
            json={
                "messages": [
                    {"role": "user", "content": "Test streaming message"}
                ]
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert response.headers["x-vercel-ai-data-stream"] == "v1"
        
        # Check that we get AI SDK streaming data format
        content = response.content.decode()
        assert "data:" in content
        assert '"type": "start"' in content
        assert '"type": "text-start"' in content  
        assert '"type": "text-delta"' in content
        assert '"type": "text-end"' in content
        assert "[DONE]" in content
    
    def test_streaming_endpoint_empty_messages(self, client):
        """Test streaming endpoint with empty messages array."""
        response = client.post(
            "/conversation/send",
            json={"messages": []}
        )
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_health_check_success(self, client):
        """Test conversation health check endpoint."""
        response = client.get("/conversation/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "graph_initialized" in data
        assert "test_response_received" in data
        assert "error" in data
        
        assert data["status"] == "healthy"
        assert data["graph_initialized"] is True
        assert data["test_response_received"] is True
    
    def test_health_check_unauthorized(self, unauthenticated_client):
        """Test health check without authentication."""
        response = unauthenticated_client.get("/conversation/health")
        
        assert response.status_code == 403  # Missing authorization header
    
    @patch('app.routers.conversation.orchestrator')
    def test_send_message_orchestrator_error(self, mock_orchestrator, client):
        """Test handling of orchestrator errors."""
        # Mock orchestrator to return error
        mock_orchestrator.process_message.return_value = {
            "content": "Error occurred",
            "error": "Test error",
            "agent": "orchestrator"
        }
        
        response = client.post(
            "/conversation/message",
            json={
                "messages": [
                    {"role": "user", "content": "Test message"}
                ]
            }
        )
        
        assert response.status_code == 500
        assert "AI processing error" in response.json()["detail"] or "Conversation processing failed" in response.json()["detail"]
    
    @patch('app.routers.conversation.orchestrator')
    def test_health_check_orchestrator_exception(self, mock_orchestrator, client):
        """Test health check when orchestrator raises exception."""
        # Mock orchestrator to raise exception
        mock_orchestrator.health_check.side_effect = Exception("Test exception")
        
        response = client.get("/conversation/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["error"] is not None
    
    def test_no_user_message_in_array(self, client):
        """Test messages array with no user messages."""
        response = client.post(
            "/conversation/message",
            json={
                "messages": [
                    {"role": "assistant", "content": "I'm an assistant"}
                ]
            }
        )
        
        assert response.status_code == 400
        assert "No valid user message found" in response.json()["detail"]


@pytest.mark.asyncio
class TestConversationEndpointsAsync:
    """Async test cases for conversation endpoints."""
    
    async def test_async_send_message(self):
        """Test async message sending with AI SDK format."""
        app = create_app()
        # Mock auth for async client too
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/conversation/message",
                json={
                    "messages": [
                        {"role": "user", "content": "Async test message"}
                    ]
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "assistant"
        assert data["agent"] == "orchestrator"
    
    async def test_async_streaming_send(self):
        """Test async streaming endpoint with AI SDK format."""
        app = create_app()
        # Mock auth for async client too
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/conversation/send",
                json={
                    "messages": [
                        {"role": "user", "content": "Async streaming test"}
                    ]
                }
            )
        
        assert response.status_code == 200
        content = response.content.decode()
        assert "data:" in content
        assert '"type": "start"' in content
        assert '"type": "text-start"' in content
        assert "[DONE]" in content