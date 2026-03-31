"""
Analyze API contract tests.

Verify that the API's OpenAPI schema and actual response structure comply with the agreed contract,
Ensure the consistency of front-end and back-end interfaces.

Test content:
- The /api/v1/analyze endpoint exists in the OpenAPI schema
- The response structure of POST /api/v1/analyze is as expected
"""

import os

import httpx
import pytest

from app.main import app


# ---------------------------------------------------------------------------
# Test database fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    """Create a test database in the temporary directory."""
    db_url = f"sqlite:///{tmp_path}/test.db"
    os.environ["DATABASE_URL"] = db_url

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
# Contract testing
# ===================================================================


class TestAnalyzeContract:
    """Verify the API contract of /api/v1/analyze."""

    async def test_openapi_schema_has_analyze_endpoint(self):
        """
        The /api/v1/analyze path should be included in the OpenAPI schema (GET /openapi.json),
        Make sure the API documentation and actual routing are consistent.
        """
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "/api/v1/analyze" in schema["paths"], (
            "/api/v1/analyze endpoint not found in OpenAPI schema"
        )

    async def test_analyze_response_matches_schema(self):
        """
        The actual response structure of POST /api/v1/analyze should conform to the contract:
        - session_id: string
        - status: string
        - vocal_profile: dictionary containing pitch, rhythm, mood, timbre, expression
        - recommendations: list, each item contains fields such as genre, confidence, etc.
        """
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/analyze", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert isinstance(data["session_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["vocal_profile"], dict)
        assert isinstance(data["recommendations"], list)

        # Verify vocal_profile substructure
        profile = data["vocal_profile"]
        for key in ("pitch", "rhythm", "mood", "timbre", "expression"):
            assert key in profile, f"vocal_profile missing '{key}'"
            assert isinstance(profile[key], dict), f"vocal_profile['{key}'] should be a dictionary type"

        # Validate recommendations substructure (if there are recommendation results)
        for rec in data["recommendations"]:
            assert "genre" in rec, "The 'genre' field is missing from the recommended results"
            assert "confidence" in rec, "Recommended results are missing the 'confidence' field"
