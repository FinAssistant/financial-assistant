import bcrypt
import jwt
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class LoginCredentials:
    """User login credentials."""
    email: str
    password: str


@dataclass
class RegisterData:
    """User registration data."""
    email: str
    password: str
    name: Optional[str] = None


@dataclass
class AuthResult:
    """Authentication result."""
    success: bool
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    error_message: Optional[str] = None


class AuthService:
    """Authentication service for user registration and login."""
    
    def __init__(self):
        self.secret_key = settings.secret_key or "dev-secret-key"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt with secure salt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format using regex."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Requirements: min 8 chars, mixed case, numbers, symbols.
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def generate_access_token(self, user_id: str) -> str:
        """Generate JWT access token for user."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_access_token(self, token: str) -> Optional[str]:
        """
        Validate JWT access token and return user_id if valid.
        Returns None if token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if token_type != "access" or not user_id:
                return None
                
            return user_id
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def validate_registration_data(self, data: RegisterData) -> tuple[bool, str]:
        """Validate registration data."""
        # Validate email
        if not self._validate_email(data.email):
            return False, "Invalid email format"
        
        # Validate password strength
        is_valid, message = self._validate_password_strength(data.password)
        if not is_valid:
            return False, message
        
        return True, ""
    
    def register_user(self, data: RegisterData, user_exists_func) -> AuthResult:
        """
        Register a new user.
        user_exists_func should return True if user with email already exists.
        """
        # Validate input data
        is_valid, error_message = self.validate_registration_data(data)
        if not is_valid:
            return AuthResult(success=False, error_message=error_message)
        
        # Check if user already exists
        if user_exists_func(data.email):
            return AuthResult(success=False, error_message="Email already registered")
        
        # Hash password
        hashed_password = self._hash_password(data.password)
        
        # Generate user ID
        import uuid
        user_id = str(uuid.uuid4())
        
        # Generate access token
        access_token = self.generate_access_token(user_id)
        
        return AuthResult(
            success=True,
            user_id=user_id,
            access_token=access_token
        )
    
    def login_user(self, credentials: LoginCredentials, get_user_func) -> AuthResult:
        """
        Authenticate user login.
        get_user_func should return user dict with 'id' and 'password_hash' if user exists.
        """
        # Validate email format
        if not self._validate_email(credentials.email):
            return AuthResult(success=False, error_message="Invalid email format")
        
        # Get user from storage
        user = get_user_func(credentials.email)
        if not user:
            return AuthResult(success=False, error_message="Invalid credentials")
        
        # Verify password
        if not self._verify_password(credentials.password, user['password_hash']):
            return AuthResult(success=False, error_message="Invalid credentials")
        
        # Generate access token
        access_token = self.generate_access_token(user['id'])
        
        return AuthResult(
            success=True,
            user_id=user['id'],
            access_token=access_token
        )


# Global auth service instance
auth_service = AuthService()