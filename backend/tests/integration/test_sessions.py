"""
Authentication and session endpoint integration tests.
"""

import os
import pytest
import httpx
from app.main import app
from app.db.database import init_database


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    """Creates an independent temporary database for each test."""
    db_url = f"sqlite:///{tmp_path}/test.db"
    os.environ["DATABASE_URL"] = db_url

    # Recreate settings singleton to ensure all modules reference the updated database path
    from app.config import Settings
    import app.config
    new_settings = Settings()
    app.config.settings = new_settings

    # Update imported settings references in each route module
    import app.api.analyze as analyze_mod
    import app.api.auth as auth_mod
    import app.api.sessions as sessions_mod
    analyze_mod.settings = new_settings
    auth_mod.settings = new_settings
    sessions_mod.settings = new_settings

    await init_database(db_url)
    yield


class TestAuth:
    """Authentication endpoint tests."""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Successful registration should return 201 + token."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/auth/register", json={
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test User",
            })
            assert response.status_code == 201
            data = response.json()
            assert "token" in data
            assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Duplicate email registration should return 409."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json={
                "email": "dup@example.com", "password": "pass123",
            })
            response = await client.post("/api/v1/auth/register", json={
                "email": "dup@example.com", "password": "pass456",
            })
            assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Correct credentials login should return 200 + token."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json={
                "email": "login@example.com", "password": "pass123",
            })
            response = await client.post("/api/v1/auth/login", json={
                "email": "login@example.com", "password": "pass123",
            })
            assert response.status_code == 200
            assert "token" in response.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        """Wrong password login should return 401."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/v1/auth/register", json={
                "email": "wrong@example.com", "password": "correct",
            })
            response = await client.post("/api/v1/auth/login", json={
                "email": "wrong@example.com", "password": "incorrect",
            })
            assert response.status_code == 401


class TestSessions:
    """Session history endpoint tests."""

    @pytest.mark.asyncio
    async def test_sessions_requires_auth(self):
        """Unauthenticated access to /sessions should return 401."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/sessions")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sessions_empty_for_new_user(self):
        """New user should return empty session list."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            reg = await client.post("/api/v1/auth/register", json={
                "email": "new@example.com", "password": "pass123",
            })
            token = reg.json()["token"]
            response = await client.get(
                "/api/v1/sessions",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["sessions"] == []
            assert data["total"] == 0
