import pytest
import jwt
from datetime import datetime, timedelta

from app.services.auth_service import AuthService, LoginCredentials, RegisterData, AuthResult


class TestAuthService:
    """Test cases for AuthService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_service = AuthService()
        self.valid_email = "test@example.com"
        self.valid_password = "StrongPass123!"
        self.weak_password = "weak"
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password"
        hashed = self.auth_service._hash_password(password)
        
        # Hash should be different from original password
        assert hashed != password
        # Hash should be bcrypt format
        assert hashed.startswith('$2b$')
        # Should be able to verify
        assert self.auth_service._verify_password(password, hashed)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password"
        hashed = self.auth_service._hash_password(password)
        
        assert self.auth_service._verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password"
        hashed = self.auth_service._hash_password(password)
        
        assert self.auth_service._verify_password("wrong_password", hashed) is False
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert self.auth_service._validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            ""
        ]
        
        for email in invalid_emails:
            assert self.auth_service._validate_email(email) is False
    
    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid passwords."""
        valid_passwords = [
            "StrongPass123!",
            "MySecure$Pass9",
            "Complex!Pass123"
        ]
        
        for password in valid_passwords:
            is_valid, message = self.auth_service._validate_password_strength(password)
            assert is_valid is True
            assert message == ""
    
    def test_validate_password_strength_too_short(self):
        """Test password strength validation with too short password."""
        is_valid, message = self.auth_service._validate_password_strength("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in message
    
    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation without lowercase."""
        is_valid, message = self.auth_service._validate_password_strength("STRONG123!")
        assert is_valid is False
        assert "lowercase letter" in message
    
    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase."""
        is_valid, message = self.auth_service._validate_password_strength("strong123!")
        assert is_valid is False
        assert "uppercase letter" in message
    
    def test_validate_password_strength_no_number(self):
        """Test password strength validation without number."""
        is_valid, message = self.auth_service._validate_password_strength("StrongPass!")
        assert is_valid is False
        assert "number" in message
    
    def test_validate_password_strength_no_special(self):
        """Test password strength validation without special character."""
        is_valid, message = self.auth_service._validate_password_strength("StrongPass123")
        assert is_valid is False
        assert "special character" in message
    
    def test_generate_access_token(self):
        """Test JWT access token generation."""
        user_id = "test_user_123"
        token = self.auth_service.generate_access_token(user_id)
        
        # Token should be a string
        assert isinstance(token, str)
        # Token should have JWT format (3 parts separated by dots)
        assert len(token.split('.')) == 3
        
        # Decode and verify payload
        payload = jwt.decode(token, self.auth_service.secret_key, algorithms=[self.auth_service.algorithm])
        assert payload['sub'] == user_id
        assert payload['type'] == 'access'
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_validate_access_token_valid(self):
        """Test access token validation with valid token."""
        user_id = "test_user_123"
        token = self.auth_service.generate_access_token(user_id)
        
        validated_user_id = self.auth_service.validate_access_token(token)
        assert validated_user_id == user_id
    
    def test_validate_access_token_invalid(self):
        """Test access token validation with invalid token."""
        invalid_token = "invalid.jwt.token"
        
        validated_user_id = self.auth_service.validate_access_token(invalid_token)
        assert validated_user_id is None
    
    def test_validate_access_token_expired(self):
        """Test access token validation with expired token."""
        user_id = "test_user_123"
        
        # Create expired token (expired 1 minute ago)
        expire = datetime.utcnow() - timedelta(minutes=1)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(minutes=2),
            "type": "access"
        }
        expired_token = jwt.encode(payload, self.auth_service.secret_key, algorithm=self.auth_service.algorithm)
        
        validated_user_id = self.auth_service.validate_access_token(expired_token)
        assert validated_user_id is None
    
    def test_validate_registration_data_valid(self):
        """Test registration data validation with valid data."""
        data = RegisterData(email=self.valid_email, password=self.valid_password)
        
        is_valid, message = self.auth_service.validate_registration_data(data)
        assert is_valid is True
        assert message == ""
    
    def test_validate_registration_data_invalid_email(self):
        """Test registration data validation with invalid email."""
        data = RegisterData(email="invalid-email", password=self.valid_password)
        
        is_valid, message = self.auth_service.validate_registration_data(data)
        assert is_valid is False
        assert "email format" in message
    
    def test_validate_registration_data_weak_password(self):
        """Test registration data validation with weak password."""
        data = RegisterData(email=self.valid_email, password=self.weak_password)
        
        is_valid, message = self.auth_service.validate_registration_data(data)
        assert is_valid is False
        assert "Password must" in message
    
    def test_register_user_success(self):
        """Test successful user registration."""
        data = RegisterData(email=self.valid_email, password=self.valid_password)
        
        # Mock user_exists_func that returns False (user doesn't exist)
        def user_exists_func(email):
            return False
        
        result = self.auth_service.register_user(data, user_exists_func)
        
        assert result.success is True
        assert result.user_id is not None
        assert result.access_token is not None
        assert result.error_message is None
    
    def test_register_user_email_exists(self):
        """Test user registration with existing email."""
        data = RegisterData(email=self.valid_email, password=self.valid_password)
        
        # Mock user_exists_func that returns True (user exists)
        def user_exists_func(email):
            return True
        
        result = self.auth_service.register_user(data, user_exists_func)
        
        assert result.success is False
        assert result.user_id is None
        assert result.access_token is None
        assert "already registered" in result.error_message
    
    def test_register_user_invalid_data(self):
        """Test user registration with invalid data."""
        data = RegisterData(email="invalid-email", password=self.weak_password)
        
        def user_exists_func(email):
            return False
        
        result = self.auth_service.register_user(data, user_exists_func)
        
        assert result.success is False
        assert result.user_id is None
        assert result.access_token is None
        assert result.error_message is not None
    
    def test_login_user_success(self):
        """Test successful user login."""
        credentials = LoginCredentials(email=self.valid_email, password=self.valid_password)
        hashed_password = self.auth_service._hash_password(self.valid_password)
        
        # Mock get_user_func that returns user data
        def get_user_func(email):
            if email == self.valid_email:
                return {
                    'id': 'test_user_123',
                    'password_hash': hashed_password
                }
            return None
        
        result = self.auth_service.login_user(credentials, get_user_func)
        
        assert result.success is True
        assert result.user_id == 'test_user_123'
        assert result.access_token is not None
        assert result.error_message is None
    
    def test_login_user_invalid_email(self):
        """Test user login with invalid email format."""
        credentials = LoginCredentials(email="invalid-email", password=self.valid_password)
        
        def get_user_func(email):
            return None
        
        result = self.auth_service.login_user(credentials, get_user_func)
        
        assert result.success is False
        assert result.user_id is None
        assert result.access_token is None
        assert "email format" in result.error_message
    
    def test_login_user_not_found(self):
        """Test user login with non-existent user."""
        credentials = LoginCredentials(email=self.valid_email, password=self.valid_password)
        
        # Mock get_user_func that returns None (user not found)
        def get_user_func(email):
            return None
        
        result = self.auth_service.login_user(credentials, get_user_func)
        
        assert result.success is False
        assert result.user_id is None
        assert result.access_token is None
        assert "Invalid credentials" in result.error_message
    
    def test_login_user_wrong_password(self):
        """Test user login with wrong password."""
        credentials = LoginCredentials(email=self.valid_email, password="wrong_password")
        hashed_password = self.auth_service._hash_password(self.valid_password)
        
        # Mock get_user_func that returns user data
        def get_user_func(email):
            if email == self.valid_email:
                return {
                    'id': 'test_user_123',
                    'password_hash': hashed_password
                }
            return None
        
        result = self.auth_service.login_user(credentials, get_user_func)
        
        assert result.success is False
        assert result.user_id is None
        assert result.access_token is None
        assert "Invalid credentials" in result.error_message