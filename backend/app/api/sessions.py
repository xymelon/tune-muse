"""
Session history API routes: view analysis history and session details.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request, Query

from app.config import settings
from app.db.database import get_connection
from app.db.queries import get_sessions_by_user, get_session_by_id
from app.api.auth import get_current_user

logger = logging.getLogger("tunemuse.api.sessions")

router = APIRouter(tags=["sessions"])


async def _require_auth(request: Request) -> str:
    """Verify user is authenticated, return user_id. Raises 401 if not logged in."""
    user_id = await get_current_user(request)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Authentication required to view analysis history."},
        )
    return user_id


@router.get("/sessions")
async def list_sessions(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    """
    Get paginated list of analysis sessions for the authenticated user.

    Query params:
    - limit: number per page (1-100, default 20)
    - offset: paging Offset (default 0)
    - sort: sort direction by created_at ("asc" or "desc", default "desc")
    """
    user_id = await _require_auth(request)

    db = await get_connection(settings.database_url)
    try:
        sessions, total = await get_sessions_by_user(db, user_id, limit, offset, sort)
        return {
            "sessions": sessions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        await db.close()


@router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str):
    """
    Get full details of a specific analysis session (including vocal profile and recommendations).

    Only allows access to own sessions; returns 404 otherwise.
    """
    user_id = await _require_auth(request)

    db = await get_connection(settings.database_url)
    try:
        session = await get_session_by_id(db, session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": "Analysis session not found."},
            )

        # Verify session belongs to current user
        if session.get("user_id") and session["user_id"] != user_id:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": "Analysis session not found."},
            )

        # Build response (convert database rows to API response format)
        profile = session.get("vocal_profile")
        recs = session.get("recommendations", [])

        vocal_profile = None
        if profile:
            vocal_profile = {
                "pitch": {
                    "range_low": profile["pitch_min_note"],
                    "range_high": profile["pitch_max_note"],
                    "comfortable_zone": f"{profile['pitch_min_note']}–{profile['pitch_max_note']}",
                    "stability": profile["pitch_stability"],
                    "description": "",
                },
                "rhythm": {
                    "tempo_bpm": profile["rhythm_tempo_bpm"],
                    "regularity": profile["rhythm_regularity"],
                    "description": "",
                },
                "mood": {
                    "valence": profile["mood_valence"],
                    "energy": profile["mood_energy"],
                    "tension": profile["mood_tension"],
                    "label": profile["mood_label"],
                    "description": "",
                },
                "timbre": {
                    "warmth": profile["timbre_warmth"],
                    "brightness": profile["timbre_brightness"],
                    "breathiness": profile["timbre_breathiness"],
                    "label": profile["timbre_label"],
                    "description": "",
                },
                "expression": {
                    "vibrato": profile["expression_vibrato"],
                    "dynamic_range": profile["expression_dynamic_range"],
                    "articulation": profile["expression_articulation"],
                    "description": "",
                },
                "confidence": profile["confidence_overall"],
            }

        recommendations = []
        for rec in recs:
            ref_songs = rec.get("reference_songs")
            if isinstance(ref_songs, str):
                try:
                    ref_songs = json.loads(ref_songs)
                except (json.JSONDecodeError, TypeError):
                    ref_songs = None

            recommendations.append({
                "rank": rec["rank"],
                "genre": rec["genre"],
                "sub_style": rec.get("sub_style"),
                "tempo_range": {"low": rec["tempo_range_low"], "high": rec["tempo_range_high"]},
                "vocal_difficulty": rec["vocal_difficulty"],
                "mood_alignment": rec["mood_alignment"],
                "match_explanation": rec["match_explanation"],
                "confidence": rec["confidence"],
                "reference_songs": ref_songs,
                "match_score": rec["match_score"],
            })

        return {
            "session_id": session["id"],
            "status": session["status"],
            "source_type": session["source_type"],
            "audio_duration_sec": session["audio_duration_sec"],
            "created_at": session["created_at"],
            "completed_at": session.get("completed_at"),
            "vocal_profile": vocal_profile,
            "recommendations": recommendations,
        }
    finally:
        await db.close()
