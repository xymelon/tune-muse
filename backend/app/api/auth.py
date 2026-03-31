"""
Authentication API routes: user registration and login.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.db.database import get_connection
from app.db.queries import create_user, get_user_by_email
from app.services.auth import hash_password, verify_password, create_token, verify_token

logger = logging.getLogger("tunemuse.api.auth")

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: str
    password: str
    display_name: str | None = None
    locale: str = "en"


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str


async def get_current_user(request: Request) -> str | None:
    """
    Extract and verify the User ID from the request's Authorization header.

    Args:
        request: FastAPI Request object

    Returns:
        User ID string, returns None if there is no token or the token is invalid
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    return verify_token(token)


@router.post("/auth/register", status_code=201)
async def register(req: RegisterRequest):
    """
    Register a new user.

    Returns user info and JWT token on success. Returns 409 if email already exists.
    """
    db = await get_connection(settings.database_url)
    try:
        # Check if email is already registered
        existing = await get_user_by_email(db, req.email)
        if existing:
            raise HTTPException(
                status_code=409,
                detail={"error": "email_exists", "message": "This email is already registered."},
            )

        # Create user
        password_hash = hash_password(req.password)
        user = await create_user(db, req.email, password_hash, req.display_name, req.locale)

        # Generate token
        token = create_token(user["id"])

        return {
            "user_id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name", ""),
            "token": token,
        }
    finally:
        await db.close()


@router.post("/auth/login")
async def login(req: LoginRequest):
    """
    User login.

    Returns user info and JWT token on success. Returns 401 for invalid credentials.
    """
    db = await get_connection(settings.database_url)
    try:
        user = await get_user_by_email(db, req.email)
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_credentials", "message": "Invalid email or password."},
            )

        token = create_token(user["id"])

        return {
            "user_id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name", ""),
            "token": token,
        }
    finally:
        await db.close()
