"""
Authentication service unit tests.
"""

import pytest
from app.services.auth import hash_password, verify_password, create_token, verify_token


class TestPasswordHashing:
    """Password hashing and verification tests."""

    def test_hash_and_verify_correct_password(self):
        """Correct password should verify successfully."""
        hashed = hash_password("my_secure_password")
        assert verify_password("my_secure_password", hashed)

    def test_verify_wrong_password(self):
        """Wrong password should fail verification."""
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_hash_produces_different_values(self):
        """Two hashes of the same password should differ (different salts)."""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2


class TestJwtToken:
    """JWT token generation and verification tests."""

    def test_create_and_verify_token(self):
        """Generated token should verify correctly and return user_id."""
        user_id = "test-user-123"
        token = create_token(user_id)
        assert verify_token(token) == user_id

    def test_verify_invalid_token(self):
        """Invalid token should return None."""
        assert verify_token("invalid.token.here") is None

    def test_verify_empty_token(self):
        """Empty token should return None."""
        assert verify_token("") is None
