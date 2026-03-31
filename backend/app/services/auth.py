"""
Authentication service: password hashing and JWT token management.

Uses passlib + bcrypt for password hashing, python-jose for JWT token generation and verification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt password hashing context
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password with bcrypt.

    Args:
        password: Plain-text password from user input

    Returns:
        bcrypt hash string
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify whether a plain-text password matches the hash.

    Args:
        plain_password: Plain-text password from user input
        hashed_password: Stored hash from database

    Returns:
        True if matches, False otherwise
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: str) -> str:
    """
    Generate a JWT access token for a user.

    Args:
        user_id: User unique identifier

    Returns:
        JWT token string (expiry controlled by settings.token_expiry_days)
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.token_expiry_days)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_token(token: str) -> str | None:
    """
    Validate the JWT token and extract the User ID.

    Args:
        token: JWT token string

    Returns:
        User ID string, or None if the token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None
