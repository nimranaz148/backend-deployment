# src\api\auth.py
"""
Better-Auth compatible authentication API endpoints.
Implements signup/signin with user background collection.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import hashlib
import secrets
from datetime import datetime, timedelta
from src.services.db_service import db_service

router = APIRouter()

# In-memory session store (in production, use Redis or database)
sessions = {}


class UserBackground(BaseModel):
    """User's software and hardware background for personalization."""
    programming_experience: str = Field(
        ..., 
        description="Level: beginner, intermediate, or advanced"
    )
    robotics_experience: str = Field(
        ..., 
        description="Level: none, hobbyist, or professional"
    )
    preferred_languages: List[str] = Field(
        default=[], 
        description="Programming languages the user knows"
    )
    hardware_access: List[str] = Field(
        default=[], 
        description="Hardware the user has access to"
    )


class SignupRequest(BaseModel):
    """Request to create a new user account."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)
    background: UserBackground


class SigninRequest(BaseModel):
    """Request to sign in to an existing account."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response with user data and session token."""
    user: dict
    session_token: str
    expires_at: str


class UserResponse(BaseModel):
    """Response with user data."""
    id: str
    email: str
    name: str
    background: Optional[UserBackground] = None


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Create a new user account with background information.
    Better-Auth compatible signup endpoint.
    """
    try:
        # Check if user already exists
        existing_user = db_service.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user in database
        user_id = f"user_{secrets.token_hex(8)}"
        password_hash = hash_password(request.password)
        
        user_data = {
            "id": user_id,
            "email": request.email,
            "name": request.name,
            "password_hash": password_hash,
            "background": request.background.model_dump(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        db_service.create_user(user_data)
        
        # Create session
        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        sessions[session_token] = {
            "user_id": user_id,
            "expires_at": expires_at
        }
        
        return AuthResponse(
            user={
                "id": user_id,
                "email": request.email,
                "name": request.name,
                "background": request.background.model_dump()
            },
            session_token=session_token,
            expires_at=expires_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/auth/signin", response_model=AuthResponse)
async def signin(request: SigninRequest):
    """
    Sign in to an existing account.
    Better-Auth compatible signin endpoint.
    """
    try:
        # Get user from database
        user = db_service.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        password_hash = hash_password(request.password)
        if user.get("password_hash") != password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create session
        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        sessions[session_token] = {
            "user_id": user["id"],
            "expires_at": expires_at
        }
        
        return AuthResponse(
            user={
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "background": user.get("background")
            },
            session_token=session_token,
            expires_at=expires_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signin failed: {str(e)}")


@router.post("/auth/signout")
async def signout(session_token: str):
    """
    Sign out and invalidate session.
    Better-Auth compatible signout endpoint.
    """
    if session_token in sessions:
        del sessions[session_token]
    return {"success": True}


@router.get("/auth/session", response_model=UserResponse)
async def get_session(session_token: str):
    """
    Get current session user.
    Better-Auth compatible session endpoint.
    """
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    session = sessions[session_token]
    if datetime.utcnow() > session["expires_at"]:
        del sessions[session_token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    user = db_service.get_user_by_id(session["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        background=user.get("background")
    )
