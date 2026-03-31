"""
Analysis API routes: handles audio feature submission and file uploads.

Contains two core endpoints:
- POST /analyze: receives client-extracted feature vectors, returns vocal profile + recommendations
- POST /upload: receives audio files, extracts features server-side, then follows the same analysis pipeline
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_connection
from app.db.queries import (
    create_session,
    create_vocal_profile,
    create_recommendations,
    update_session_status,
)
from app.services.vocal_analyzer import analyze_features
from app.services.recommendation import get_recommendations

logger = logging.getLogger("tunemuse.api.analyze")

router = APIRouter()


# ============================================================
# Request/response models (inline to avoid circular imports)
# ============================================================


class PitchContourStats(BaseModel):
    mean: float
    std: float
    quartile_25: float
    quartile_75: float


class AudioFeatures(BaseModel):
    """Client-extracted audio feature vector."""
    mfcc_mean: list[float]
    mfcc_std: list[float]
    pitch_min_hz: float
    pitch_max_hz: float
    pitch_median_hz: float
    pitch_stability: float = Field(ge=0.0, le=1.0)
    pitch_contour_stats: PitchContourStats
    tempo_bpm: float | None = None
    rhythm_regularity: float = Field(ge=0.0, le=1.0)
    spectral_centroid_mean: float
    spectral_centroid_std: float
    spectral_flatness_mean: float = Field(ge=0.0, le=1.0)
    spectral_rolloff_mean: float
    zero_crossing_rate_mean: float
    rms_mean: float
    rms_std: float
    chroma_mean: list[float]
    signal_quality_score: float = Field(ge=0.0, le=1.0)


class AnalyzeRequest(BaseModel):
    """Analysis request: contains source type, duration, and feature vector."""
    source_type: str = Field(pattern="^(recording|upload)$")
    duration_seconds: float = Field(gt=0, le=180)
    features: AudioFeatures


# ============================================================
# POST /analyze — Submit feature vectors for analysis
# ============================================================


@router.post("/analyze")
async def analyze_audio(raw_request: Request, request: AnalyzeRequest):
    """
    Receives client-extracted audio features, performs vocal analysis and song recommendation.

    process:
    1. Verify signal quality (reject if below threshold)
    2. Create analysis session records
    3. Call vocal_analyzer to generate Vocal profile
    4. Call the recommendation engine to generate recommendations
    5. Try LLM refinement (optional, failure will not affect the results)
    6. Save results to database
    7. Return the complete analysis response
    """
    features = request.features

    # Signal quality threshold check
    if features.signal_quality_score < settings.min_signal_quality:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "low_quality_audio",
                "message": "The audio signal quality is too low for reliable analysis. "
                           "Please re-record in a quieter environment.",
                "signal_quality_score": features.signal_quality_score,
                "minimum_required": settings.min_signal_quality,
            },
        )

    # Pitch range validation: minimum pitch must not exceed maximum pitch
    if features.pitch_min_hz > 0 and features.pitch_max_hz > 0 and features.pitch_min_hz > features.pitch_max_hz:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "message": "Feature vector validation failed",
                "details": [{"field": "features.pitch_min_hz", "issue": "must be less than pitch_max_hz"}],
            },
        )

    db = await get_connection(settings.database_url)
    try:
        # Extract the authenticated User ID (if there is Bearer token)
        user_id = None
        if raw_request:
            try:
                from app.api.auth import get_current_user
                user_id = await get_current_user(raw_request)
            except Exception:
                pass  # Anonymous access is also allowed

        # Create analysis session
        session_id = await create_session(
            db,
            source_type=request.source_type,
            audio_duration_sec=request.duration_seconds,
            signal_quality_score=features.signal_quality_score,
            user_id=user_id,
        )

        # Feature dict (passed to analysis service)
        features_dict = features.model_dump()

        # Generate vocal profile
        vocal_profile = analyze_features(features_dict)

        # Generate recommendations (rule engine)
        raw_recommendations = get_recommendations(vocal_profile)

        # Normalize rule engine output to API contract format
        # Rule engine output field names may differ from API contract; mapping required
        from app.services.recommendation import _load_knowledge_base
        kb = _load_knowledge_base()
        kb_map = {d["id"]: d for d in kb} if kb else {}

        recommendations = []
        for i, rec in enumerate(raw_recommendations):
            direction = kb_map.get(rec.get("direction_id", ""))
            tempo_range = direction.get("tempo_range", {"low": 60, "high": 120}) if direction else {"low": 60, "high": 120}
            vocal_difficulty = direction.get("vocal_difficulty", 3) if direction else 3

            recommendations.append({
                "rank": i + 1,
                "genre": rec.get("genre", "Unknown"),
                "sub_style": rec.get("sub_style"),
                "tempo_range": tempo_range,
                "vocal_difficulty": vocal_difficulty,
                "mood_alignment": rec.get("description", "Matches your vocal style"),
                "match_explanation": rec.get("explanation", rec.get("description", "")),
                "confidence": rec.get("confidence", "medium"),
                "reference_songs": rec.get("example_songs"),
                "match_score": round(rec.get("score", 0.5), 2),
            })

        # Attempt LLM refinement (graceful degradation)
        try:
            from app.services.llm_client import refine_recommendations
            recommendations = await refine_recommendations(vocal_profile, recommendations)
        except Exception as e:
            logger.warning("LLM refinement failed, using rule engine results: %s", e)

        # Save vocal profile to database
        profile_data = {
            "pitch_min_hz": features.pitch_min_hz,
            "pitch_max_hz": features.pitch_max_hz,
            "pitch_min_note": vocal_profile["pitch"]["range_low"],
            "pitch_max_note": vocal_profile["pitch"]["range_high"],
            "pitch_median_hz": features.pitch_median_hz,
            "pitch_stability": features.pitch_stability,
            "rhythm_tempo_bpm": features.tempo_bpm,
            "rhythm_regularity": features.rhythm_regularity,
            "mood_valence": vocal_profile["mood"]["valence"],
            "mood_energy": vocal_profile["mood"]["energy"],
            "mood_tension": vocal_profile["mood"]["tension"],
            "mood_label": vocal_profile["mood"]["label"],
            "timbre_warmth": vocal_profile["timbre"]["warmth"],
            "timbre_brightness": vocal_profile["timbre"]["brightness"],
            "timbre_breathiness": vocal_profile["timbre"]["breathiness"],
            "timbre_label": vocal_profile["timbre"]["label"],
            "expression_vibrato": vocal_profile["expression"]["vibrato"],
            "expression_dynamic_range": vocal_profile["expression"]["dynamic_range"],
            "expression_articulation": vocal_profile["expression"]["articulation"],
            "confidence_overall": vocal_profile["confidence"],
            "raw_features_json": features_dict,
        }
        await create_vocal_profile(db, session_id, profile_data)

        # Save recommendations
        rec_db_data = []
        for rec in recommendations:
            rec_db_data.append({
                "rank": rec["rank"],
                "genre": rec["genre"],
                "sub_style": rec.get("sub_style"),
                "tempo_range_low": rec["tempo_range"]["low"],
                "tempo_range_high": rec["tempo_range"]["high"],
                "vocal_difficulty": rec["vocal_difficulty"],
                "mood_alignment": rec["mood_alignment"],
                "match_explanation": rec["match_explanation"],
                "confidence": rec["confidence"],
                "reference_songs": rec.get("reference_songs"),
                "match_score": rec["match_score"],
            })
        await create_recommendations(db, session_id, rec_db_data)

        # Update session status to completed
        await update_session_status(db, session_id, "completed")

        return {
            "session_id": session_id,
            "status": "completed",
            "vocal_profile": vocal_profile,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analysis failed: %s", e, exc_info=True)
        if "session_id" in dir():
            await update_session_status(db, session_id, "failed", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_failed",
                "message": "An error occurred during analysis. Please try again.",
            },
        )
    finally:
        await db.close()


# ============================================================
# POST /upload — Upload audio files
# ============================================================

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mp4", "audio/m4a", "audio/x-m4a", "audio/ogg", "audio/vorbis",
}

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}


@router.post("/upload")
async def upload_audio(raw_request: Request, file: UploadFile = File(...)):
    """
    Receives audio file uploads, extracts features server-side, then performs analysis.

    Supported formats: MP3, WAV, M4A, OGG
    Size limit: 10 MB
    """
    # Validate file type
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_format",
                "message": "Unsupported audio format. Please upload MP3, WAV, M4A, or OGG files.",
            },
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": "File size exceeds the 10 MB limit.",
                "max_size_bytes": settings.max_upload_size,
            },
        )

    # Server-side feature extraction (Phase 5 implementation)
    try:
        from app.services.audio_extractor import extract_features
        features_dict = extract_features(content, ext)
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "not_implemented",
                "message": "Server-side audio analysis is not yet available. "
                           "Please use the recording feature instead.",
            },
        )

    # Follow the same analysis pipeline with extracted features
    analyze_req = AnalyzeRequest(
        source_type="upload",
        duration_seconds=features_dict.pop("duration_seconds", 30.0),
        features=AudioFeatures(**features_dict),
    )
    return await analyze_audio(raw_request, analyze_req)
