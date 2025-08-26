from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import time
from collections import defaultdict

from app.services.auth_service import auth_service, LoginCredentials, RegisterData
from app.core.database import user_storage


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)  # Remove min_length to handle in service
    name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    """Authentication response."""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# Rate limiting storage (in-memory for POC)
rate_limit_storage = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60


def check_rate_limit(request: Request, endpoint: str) -> None:
    """Check rate limiting for auth endpoints."""
    client_ip = request.client.host
    current_time = time.time()
    key = f"{client_ip}:{endpoint}"
    
    # Clean old requests outside the window
    rate_limit_storage[key] = [
        req_time for req_time in rate_limit_storage[key]
        if current_time - req_time < RATE_LIMIT_WINDOW_SECONDS
    ]
    
    # Check if rate limit exceeded
    if len(rate_limit_storage[key]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Add current request
    rate_limit_storage[key].append(current_time)


# JWT token dependency
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    JWT middleware for protected routes.
    Returns user_id if token is valid, raises HTTPException otherwise.
    """
    token = credentials.credentials
    user_id = auth_service.validate_access_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists in storage
    user = user_storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, register_data: RegisterRequest) -> AuthResponse:
    """Register a new user with email and password."""
    # Apply rate limiting
    check_rate_limit(request, "register")
    
    # Convert request to service data
    service_data = RegisterData(
        email=register_data.email,
        password=register_data.password,
        name=register_data.name
    )
    
    # Attempt registration
    result = auth_service.register_user(
        service_data,
        lambda email: user_storage.user_exists(email)
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message
        )
    
    # Create user in storage
    user_data = {
        'id': result.user_id,
        'email': register_data.email,
        'name': register_data.name or '',
        'password_hash': auth_service._hash_password(register_data.password),
        'created_at': datetime.now(),
        'profile_complete': False
    }
    
    user_storage.create_user(user_data)
    
    # Return response
    return AuthResponse(
        access_token=result.access_token,
        user={
            'id': result.user_id,
            'email': register_data.email,
            'name': register_data.name or '',
            'profile_complete': False
        }
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, login_data: LoginRequest) -> AuthResponse:
    """Login user with email and password."""
    # Apply rate limiting
    check_rate_limit(request, "login")
    
    # Convert request to service data
    credentials = LoginCredentials(
        email=login_data.email,
        password=login_data.password
    )
    
    # Attempt login
    result = auth_service.login_user(
        credentials,
        lambda email: user_storage.get_user_by_email(email)
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error_message
        )
    
    # Get user data for response
    user = user_storage.get_user_by_id(result.user_id)
    
    return AuthResponse(
        access_token=result.access_token,
        user={
            'id': user['id'],
            'email': user['email'],
            'name': user.get('name', ''),
            'profile_complete': user.get('profile_complete', False)
        }
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: str = Depends(get_current_user)) -> MessageResponse:
    """
    Logout user by invalidating their token.
    Note: In a stateless JWT system, true token invalidation requires 
    a blacklist or token versioning. For this POC, we return success
    and rely on client-side token removal.
    """
    # In a production system, you would add the token to a blacklist
    # or increment a user token version number
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current authenticated user information."""
    user = user_storage.get_user_by_id(current_user)
    
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user.get('name', ''),
        'profile_complete': user.get('profile_complete', False),
        'created_at': user.get('created_at')
    }