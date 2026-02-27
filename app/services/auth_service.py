"""
Authentication Service

Handles JWT token creation/validation and password verification.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user_models import TokenPayload, UserInDB
from app.services.database import db

logger = logging.getLogger(__name__)

security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt.

    Returns False on any verification or backend error instead of raising,
    so the login route can consistently treat it as "invalid credentials".
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError as e:
        # Covers bcrypt's 72-byte limit and any other backend issues
        logger.warning("Password verification error: %s", str(e))
        return False
    except Exception as e:
        logger.exception("Unexpected error during password verification")
        return False


def get_password_hash(password: str) -> str:
    """
    Generate password hash using bcrypt.

    Note: Not used in the current flow (admins are seeded),
    but provided for completeness.
    """
    if not password:
        raise ValueError("Password cannot be empty")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(user_id: UUID, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's UUID
        email: User's email
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenPayload(sub=user_id, email=email, exp=payload.get("exp"))
        
    except JWTError as e:
        logger.warning("JWT decode failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Fetch user from database by email.
    
    Args:
        email: User's email address
        
    Returns:
        UserInDB if found, None otherwise
    """
    if db.pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not connected",
        )
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, created_at, updated_at FROM users WHERE email = $1",
            email,
        )
        
        if row is None:
            return None
        
        return UserInDB(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def get_user_by_id(user_id: UUID) -> Optional[UserInDB]:
    """
    Fetch user from database by ID.
    
    Args:
        user_id: User's UUID
        
    Returns:
        UserInDB if found, None otherwise
    """
    if db.pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not connected",
        )
    
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, created_at, updated_at FROM users WHERE id = $1",
            user_id,
        )
        
        if row is None:
            return None
        
        return UserInDB(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate user with email and password.
    
    Args:
        email: User's email
        password: Plain text password
        
    Returns:
        UserInDB if authentication successful, None otherwise
    """
    user = await get_user_by_email(email)
    
    if user is None:
        logger.info("Authentication failed: user not found email=%s", email)
        return None
    
    if not verify_password(password, user.password_hash):
        logger.info("Authentication failed: invalid password email=%s", email)
        return None
    
    logger.info("Authentication successful: email=%s", email)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInDB:
    """
    FastAPI dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_payload = decode_access_token(credentials.credentials)
    
    try:
        user_id = UUID(token_payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
