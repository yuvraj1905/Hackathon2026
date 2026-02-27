"""
User Models

Pydantic models for user authentication and management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user model with common fields."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Model for creating a new user (not used - admin seeding only)."""
    password: str = Field(..., min_length=6, description="User password")


class UserLogin(BaseModel):
    """Model for user login request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserInDB(UserBase):
    """User model as stored in database."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: UUID = Field(..., description="User unique identifier")
    password_hash: str = Field(..., description="Hashed password")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserResponse(UserBase):
    """User model for API responses (excludes sensitive data)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: UUID = Field(..., description="User unique identifier")
    created_at: datetime = Field(..., description="Account creation timestamp")


class TokenResponse(BaseModel):
    """JWT token response model."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user details")


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
