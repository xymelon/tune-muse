"""
Analysis API integration tests.

Tests the POST /api/v1/analyze endpoint using httpx.AsyncClient + ASGITransport,
verifying the complete request-analysis-response flow, including:
- Normal analysis flow (200 response)
- Low quality signal rejection (422 response)
- Invalid pitch range detection (422 response)
- Health check endpoint (200 response)
"""

import os

import httpx
import pytest

from app.main import app


# ---------------------------------------------------------------------------
# Test database fixture — each test uses an independent temporary database
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    """
    Creates a test database in a temporary directory, auto-cleaned after test.
    Points DATABASE_URL env var to the temp database to avoid polluting dev data.
    """
    db_url = f"sqlite:///{tmp_path}/test.db"
    os.environ["DATABASE_URL"] = db_url

    # Reload settings to use the new DATABASE_URL
    # Must update settings references in both app.config and app.api.analyze
    from app.config import Settings
    import app.config
    import app.api.analyze as analyze_module
    new_settings = Settings()
    app.config.settings = new_settings
    analyze_module.settings = new_settings

    from app.db.database import init_database
    await init_database(db_url)
    yield


# ---------------------------------------------------------------------------
# Standard test request payload
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "source_type": "recording",
    "duration_seconds": 30.0,
    "features": {
        "mfcc_mean": [15.0, -3.5, 2.0, 1.0, -0.5, 0.8, -0.3, 0.2, -0.1, 0.05, -0.02, 0.01, -0.005],
        "mfcc_std": [3.0] * 13,
        "pitch_min_hz": 196.0,
        "pitch_max_hz": 523.25,
        "pitch_median_hz": 330.0,
        "pitch_stability": 0.72,
        "pitch_contour_stats": {
            "mean": 340.0,
            "std": 60.0,
            "quartile_25": 260.0,
            "quartile_75": 400.0,
        },
        "tempo_bpm": 88,
        "rhythm_regularity": 0.68,
        "spectral_centroid_mean": 1800.0,
        "spectral_centroid_std": 400.0,
        "spectral_flatness_mean": 0.15,
        "spectral_rolloff_mean": 3800.0,
        "zero_crossing_rate_mean": 0.06,
        "rms_mean": 0.12,
        "rms_std": 0.04,
        "chroma_mean": [0.5, 0.3, 0.2, 0.3, 0.6, 0.4, 0.2, 0.5, 0.3, 0.2, 0.3, 0.4],
        "signal_quality_score": 0.85,
    },
}


# ===================================================================
# Integration testing
# ===================================================================


class TestAnalyzeEndpoint:
    """POST /api/v1/analyze endpoint integration test."""

    async def test_analyze_valid_features(self):
        """
        Submit valid feature data and verify:
        1. HTTP 200 response
        2. Contains session_id (UUID format)
        3. status is "completed"
        4. vocal_profile contains 5 dimensions (pitch, rhythm, mood, timbre, expression)
        5. recommendations contain 3-8 results
        """
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/analyze", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "session_id" in data
        assert data["status"] == "completed"

        # Verify the 5 dimensions of Vocal profile
        profile = data["vocal_profile"]
        for dimension in ("pitch", "rhythm", "mood", "timbre", "expression"):
            assert dimension in profile, f"vocal_profile is missing '{dimension}' dimension"

        # Verify the number of recommendations (3-8 when the knowledge base is not empty, it can be 0 when it is empty)
        recs = data["recommendations"]
        assert isinstance(recs, list)
        if len(recs) > 0:
            assert 3 <= len(recs) <= 8

    async def test_analyze_low_quality_rejected(self):
        """
        Signal quality below the threshold (0.3) should return a 422 error,
        The error details include the 'low_quality_audio' error code.
        """
        low_quality_payload = {
            **VALID_PAYLOAD,
            "features": {
                **VALID_PAYLOAD["features"],
                "signal_quality_score": 0.1,
            },
        }

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/analyze", json=low_quality_payload)

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "low_quality_audio"

    async def test_analyze_invalid_pitch_range(self):
        """
        A 422 validation error should be returned when pitch_min_hz > pitch_max_hz.
        This is a physically impossible input and should be intercepted during the request validation phase.
        """
        invalid_payload = {
            **VALID_PAYLOAD,
            "features": {
                **VALID_PAYLOAD["features"],
                "pitch_min_hz": 600.0,
                "pitch_max_hz": 200.0,
            },
        }

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/analyze", json=invalid_payload)

        # FastAPI's Pydantic validation will return 422
        assert response.status_code == 422


class TestHealthCheck:
    """GET /api/v1/health endpoint test."""

    async def test_health_check(self):
        """The health check should return status=ok and the current version number."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "0.1.0"}
