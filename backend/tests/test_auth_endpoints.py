from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.auth import router as auth_router
from app.core.database import user_storage
from app.services.auth_service import auth_service


class TestAuthEndpoints:
    """Test cases for authentication API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create test app
        self.app = create_app()
        self.app.include_router(auth_router)
        self.client = TestClient(self.app)
        
        # Clear user storage before each test
        user_storage.clear_all_users()
        
        # Clear rate limiting storage before each test
        from app.routers.auth import rate_limit_storage
        rate_limit_storage.clear()
        
        # Test data
        self.valid_user_data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "name": "Test User"
        }
        
        self.valid_login_data = {
            "email": "test@example.com",
            "password": "StrongPass123!"
        }
    
    def test_register_success(self):
        """Test successful user registration."""
        response = self.client.post("/auth/register", json=self.valid_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == self.valid_user_data["email"]
        assert data["user"]["name"] == self.valid_user_data["name"]
        assert data["user"]["profile_complete"] is False
        assert "id" in data["user"]
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Register first user
        self.client.post("/auth/register", json=self.valid_user_data)
        
        # Try to register again with same email
        response = self.client.post("/auth/register", json=self.valid_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"]
    
    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        invalid_data = self.valid_user_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = self.client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_register_weak_password(self):
        """Test registration with weak password."""
        weak_data = self.valid_user_data.copy()
        weak_data["password"] = "weak"
        
        response = self.client.post("/auth/register", json=weak_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Password must" in data["detail"]
    
    def test_register_missing_password(self):
        """Test registration with missing password."""
        invalid_data = self.valid_user_data.copy()
        del invalid_data["password"]
        
        response = self.client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_register_without_name(self):
        """Test registration without optional name field."""
        data_without_name = {
            "email": "test@example.com",
            "password": "StrongPass123!"
        }
        
        response = self.client.post("/auth/register", json=data_without_name)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["user"]["name"] == ""
    
    def test_login_success(self):
        """Test successful user login."""
        # Register user first
        self.client.post("/auth/register", json=self.valid_user_data)
        
        # Login
        response = self.client.post("/auth/login", json=self.valid_login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == self.valid_login_data["email"]
    
    def test_login_invalid_email(self):
        """Test login with invalid email format."""
        invalid_login = self.valid_login_data.copy()
        invalid_login["email"] = "invalid-email"
        
        response = self.client.post("/auth/login", json=invalid_login)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_login_user_not_found(self):
        """Test login with non-existent user."""
        response = self.client.post("/auth/login", json=self.valid_login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Register user first
        self.client.post("/auth/register", json=self.valid_user_data)
        
        # Login with wrong password
        wrong_login = self.valid_login_data.copy()
        wrong_login["password"] = "WrongPassword123!"
        
        response = self.client.post("/auth/login", json=wrong_login)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]
    
    def test_logout_success(self):
        """Test successful user logout."""
        # Register and login user
        self.client.post("/auth/register", json=self.valid_user_data)
        login_response = self.client.post("/auth/login", json=self.valid_login_data)
        access_token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    def test_logout_without_token(self):
        """Test logout without authentication token."""
        response = self.client.post("/auth/logout")
        
        assert response.status_code == 403  # No credentials provided
    
    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]
    
    def test_get_current_user_success(self):
        """Test getting current user information."""
        # Register and login user
        self.client.post("/auth/register", json=self.valid_user_data)
        login_response = self.client.post("/auth/login", json=self.valid_login_data)
        access_token = login_response.json()["access_token"]
        
        # Get user info
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.valid_user_data["email"]
        assert data["name"] == self.valid_user_data["name"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_current_user_without_token(self):
        """Test getting current user without authentication token."""
        response = self.client.get("/auth/me")
        
        assert response.status_code == 403  # No credentials provided
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]
    
    def test_rate_limiting_register(self):
        """Test rate limiting on register endpoint."""
        # Make multiple requests quickly
        for i in range(6):  # One more than the limit
            response = self.client.post("/auth/register", json={
                "email": f"test{i}@example.com",
                "password": "StrongPass123!"
            })
            
            if i < 5:  # First 5 should succeed or fail for other reasons
                assert response.status_code in [201, 400]  # 400 for duplicate or validation
            else:  # 6th should be rate limited
                assert response.status_code == 429
                data = response.json()
                assert "Rate limit exceeded" in data["detail"]
    
    def test_rate_limiting_login(self):
        """Test rate limiting on login endpoint."""
        # Register a user first
        self.client.post("/auth/register", json=self.valid_user_data)
        
        # Make multiple login requests quickly
        for i in range(6):  # One more than the limit
            response = self.client.post("/auth/login", json=self.valid_login_data)
            
            if i < 5:  # First 5 should succeed
                assert response.status_code == 200
            else:  # 6th should be rate limited
                assert response.status_code == 429
                data = response.json()
                assert "Rate limit exceeded" in data["detail"]
    
    def test_protected_route_access(self):
        """Test that protected routes require authentication."""
        # Try to access protected route without token
        response = self.client.get("/auth/me")
        assert response.status_code == 403
        
        # Register and login user
        self.client.post("/auth/register", json=self.valid_user_data)
        login_response = self.client.post("/auth/login", json=self.valid_login_data)
        access_token = login_response.json()["access_token"]
        
        # Access protected route with valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.client.get("/auth/me", headers=headers)
        assert response.status_code == 200
    
    def test_token_contains_user_id(self):
        """Test that generated token contains correct user ID."""
        # Register user
        register_response = self.client.post("/auth/register", json=self.valid_user_data)
        access_token = register_response.json()["access_token"]
        user_id = register_response.json()["user"]["id"]
        
        # Validate token contains correct user ID
        validated_user_id = auth_service.validate_access_token(access_token)
        assert validated_user_id == user_id