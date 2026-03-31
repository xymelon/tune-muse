"""
Database query functions for all CRUD operations.
All functions are async and use aiosqlite for non-blocking database access.
"""

import json
import uuid
from datetime import datetime, timezone

import aiosqlite


def _new_id() -> str:
    """Generate a new UUID string to use as a primary key."""
    return str(uuid.uuid4())


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# User-related queries
# ============================================================


async def create_user(
    db: aiosqlite.Connection,
    email: str,
    password_hash: str,
    display_name: str | None = None,
    locale: str = "en",
) -> dict:
    """
    Create a new registered user.

    Args:
        db: Database connection
        email: User email (unique)
        password_hash: bcrypt-hashed password
        display_name: Optional display name
        locale: UI language preference, defaults to "en"

    Returns:
        A dict containing id, email, display_name, locale, created_at

    Raises:
        aiosqlite.IntegrityError: If the email already exists
    """
    user_id = _new_id()
    now = _now_iso()
    await db.execute(
        """INSERT INTO users (id, email, password_hash, display_name, locale, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, email, password_hash, display_name, locale, now, now),
    )
    await db.commit()
    return {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "locale": locale,
        "created_at": now,
    }


async def get_user_by_email(db: aiosqlite.Connection, email: str) -> dict | None:
    """
    Find a user by email.

    Args:
        db: Database connection
        email: User email

    Returns:
        User dict or None (if not found)
    """
    cursor = await db.execute(
        "SELECT id, email, password_hash, display_name, locale FROM users WHERE email = ?",
        (email,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


async def get_user_by_id(db: aiosqlite.Connection, user_id: str) -> dict | None:
    """Find a user by ID."""
    cursor = await db.execute(
        "SELECT id, email, display_name, locale FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


# ============================================================
# Analysis session queries
# ============================================================


async def create_session(
    db: aiosqlite.Connection,
    source_type: str,
    audio_duration_sec: float,
    signal_quality_score: float,
    audio_format: str | None = None,
    user_id: str | None = None,
) -> str:
    """
    Create a new analysis session record. Initial status is "processing".

    Args:
        db: Database connection
        source_type: "recording" or "upload"
        audio_duration_sec: Audio duration in seconds
        signal_quality_score: Signal quality score (0.0-1.0)
        audio_format: Audio format (only present for uploads)
        user_id: Associated user ID (None for anonymous)

    Returns:
        The newly created session ID
    """
    session_id = _new_id()
    now = _now_iso()
    await db.execute(
        """INSERT INTO analysis_sessions
           (id, user_id, source_type, audio_duration_sec, audio_format,
            signal_quality_score, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'processing', ?)""",
        (session_id, user_id, source_type, audio_duration_sec, audio_format,
         signal_quality_score, now),
    )
    await db.commit()
    return session_id


async def update_session_status(
    db: aiosqlite.Connection,
    session_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """
    Update session status (processing -> completed or failed).

    Args:
        db: Database connection
        session_id: Session ID
        status: New status ("completed" or "failed")
        error_message: Error message on failure
    """
    completed_at = _now_iso() if status == "completed" else None
    await db.execute(
        """UPDATE analysis_sessions
           SET status = ?, error_message = ?, completed_at = ?
           WHERE id = ?""",
        (status, error_message, completed_at, session_id),
    )
    await db.commit()


async def get_session_by_id(db: aiosqlite.Connection, session_id: str) -> dict | None:
    """
    Get full session information (including vocal profile and recommendations).

    Args:
        db: Database connection
        session_id: Session ID

    Returns:
        A complete dict containing session + vocal_profile + recommendations, or None
    """
    # Get basic session information
    cursor = await db.execute(
        "SELECT * FROM analysis_sessions WHERE id = ?", (session_id,)
    )
    session_row = await cursor.fetchone()
    if session_row is None:
        return None
    session = dict(session_row)

    # Get vocal profile
    cursor = await db.execute(
        "SELECT * FROM vocal_profiles WHERE session_id = ?", (session_id,)
    )
    profile_row = await cursor.fetchone()
    session["vocal_profile"] = dict(profile_row) if profile_row else None

    # Get recommendations
    cursor = await db.execute(
        "SELECT * FROM recommendations WHERE session_id = ? ORDER BY rank",
        (session_id,),
    )
    rows = await cursor.fetchall()
    session["recommendations"] = [dict(r) for r in rows]

    return session


async def get_sessions_by_user(
    db: aiosqlite.Connection,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    sort: str = "desc",
) -> tuple[list[dict], int]:
    """
    Get paginated list of analysis sessions for a user.

    Args:
        db: Database connection
        user_id: User ID
        limit: Number per page (1-100)
        offset: Pagination offset
        sort: Sort direction ("asc" or "desc")

    Returns:
        (session list, total count) tuple
    """
    order = "DESC" if sort == "desc" else "ASC"

    # Get total count
    cursor = await db.execute(
        "SELECT COUNT(*) FROM analysis_sessions WHERE user_id = ?", (user_id,)
    )
    total = (await cursor.fetchone())[0]

    # Get paginated data (with vocal profile summary)
    cursor = await db.execute(
        f"""SELECT s.id, s.source_type, s.status, s.audio_duration_sec, s.created_at,
                   vp.pitch_min_note, vp.pitch_max_note, vp.mood_label, vp.timbre_label,
                   (SELECT COUNT(*) FROM recommendations r WHERE r.session_id = s.id) as rec_count
            FROM analysis_sessions s
            LEFT JOIN vocal_profiles vp ON vp.session_id = s.id
            WHERE s.user_id = ?
            ORDER BY s.created_at {order}
            LIMIT ? OFFSET ?""",
        (user_id, limit, offset),
    )
    rows = await cursor.fetchall()

    sessions = []
    for row in rows:
        row_dict = dict(row)
        sessions.append({
            "id": row_dict["id"],
            "source_type": row_dict["source_type"],
            "status": row_dict["status"],
            "audio_duration_sec": row_dict["audio_duration_sec"],
            "vocal_profile_summary": {
                "pitch_range": f"{row_dict.get('pitch_min_note', '?')}–{row_dict.get('pitch_max_note', '?')}",
                "mood_label": row_dict.get("mood_label", ""),
                "timbre_label": row_dict.get("timbre_label", ""),
            } if row_dict.get("pitch_min_note") else None,
            "recommendation_count": row_dict.get("rec_count", 0),
            "created_at": row_dict["created_at"],
        })

    return sessions, total


# ============================================================
# Vocal profile queries
# ============================================================


async def create_vocal_profile(db: aiosqlite.Connection, session_id: str, profile: dict) -> str:
    """
    Save an AI-generated vocal profile to the database.

    Args:
        db: Database connection
        session_id: Associated analysis session ID
        profile: Vocal profile data dict containing all vocal_profiles table fields

    Returns:
        The newly created vocal profile ID
    """
    profile_id = _new_id()
    now = _now_iso()

    # Serialize raw_features to JSON string
    raw_json = profile.get("raw_features_json", "{}")
    if isinstance(raw_json, dict):
        raw_json = json.dumps(raw_json)

    await db.execute(
        """INSERT INTO vocal_profiles
           (id, session_id, pitch_min_hz, pitch_max_hz, pitch_min_note, pitch_max_note,
            pitch_median_hz, pitch_stability, rhythm_tempo_bpm, rhythm_regularity,
            mood_valence, mood_energy, mood_tension, mood_label,
            timbre_warmth, timbre_brightness, timbre_breathiness, timbre_label,
            expression_vibrato, expression_dynamic_range, expression_articulation,
            confidence_overall, raw_features_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            profile_id, session_id,
            profile["pitch_min_hz"], profile["pitch_max_hz"],
            profile["pitch_min_note"], profile["pitch_max_note"],
            profile["pitch_median_hz"], profile["pitch_stability"],
            profile.get("rhythm_tempo_bpm"), profile["rhythm_regularity"],
            profile["mood_valence"], profile["mood_energy"], profile["mood_tension"],
            profile["mood_label"],
            profile["timbre_warmth"], profile["timbre_brightness"],
            profile["timbre_breathiness"], profile["timbre_label"],
            profile["expression_vibrato"], profile["expression_dynamic_range"],
            profile["expression_articulation"],
            profile["confidence_overall"], raw_json, now,
        ),
    )
    await db.commit()
    return profile_id


# ============================================================
# Recommendation queries
# ============================================================


async def create_recommendations(
    db: aiosqlite.Connection, session_id: str, recommendations: list[dict]
) -> list[str]:
    """
    Batch save recommendation results to the database.

    Args:
        db: Database connection
        session_id: Associated analysis session ID
        recommendations: List of recommendation dicts, each containing rank, genre, sub_style, etc.

    Returns:
        List of newly created recommendation IDs
    """
    now = _now_iso()
    ids = []

    for rec in recommendations:
        rec_id = _new_id()
        ids.append(rec_id)

        # reference_songs stored as JSON string
        ref_songs = rec.get("reference_songs")
        if isinstance(ref_songs, list):
            ref_songs = json.dumps(ref_songs, ensure_ascii=False)

        await db.execute(
            """INSERT INTO recommendations
               (id, session_id, rank, genre, sub_style, tempo_range_low, tempo_range_high,
                vocal_difficulty, mood_alignment, match_explanation, confidence,
                reference_songs, match_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec_id, session_id,
                rec["rank"], rec["genre"], rec.get("sub_style"),
                rec["tempo_range_low"], rec["tempo_range_high"],
                rec["vocal_difficulty"], rec["mood_alignment"],
                rec["match_explanation"], rec["confidence"],
                ref_songs, rec["match_score"], now,
            ),
        )

    await db.commit()
    return ids
