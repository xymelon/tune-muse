"""
Database initialization module.
Creates all required tables and indexes for the TuneMuse application.
Uses aiosqlite for async SQLite access with WAL mode for concurrent reads.
"""

import aiosqlite

# Default database file path (can be overridden via config.settings.database_url)
DEFAULT_DB_PATH = "./tunemuse.db"

# SQL schema: create all required tables
# Table structure strictly corresponds to entities defined in data-model.md
SCHEMA_SQL = """
-- Users table: supports anonymous (not stored) and registered users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    display_name TEXT,
    locale TEXT NOT NULL DEFAULT 'en',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Analysis sessions table: a complete recording/upload -> analysis -> recommendation flow
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    source_type TEXT NOT NULL CHECK(source_type IN ('recording', 'upload')),
    audio_duration_sec REAL NOT NULL CHECK(audio_duration_sec > 0),
    audio_format TEXT,
    signal_quality_score REAL NOT NULL CHECK(signal_quality_score >= 0 AND signal_quality_score <= 1),
    status TEXT NOT NULL DEFAULT 'processing' CHECK(status IN ('processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Vocal profiles table: AI analysis results, one per session
CREATE TABLE IF NOT EXISTS vocal_profiles (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    pitch_min_hz REAL NOT NULL,
    pitch_max_hz REAL NOT NULL,
    pitch_min_note TEXT NOT NULL,
    pitch_max_note TEXT NOT NULL,
    pitch_median_hz REAL NOT NULL,
    pitch_stability REAL NOT NULL CHECK(pitch_stability >= 0 AND pitch_stability <= 1),
    rhythm_tempo_bpm REAL,
    rhythm_regularity REAL NOT NULL CHECK(rhythm_regularity >= 0 AND rhythm_regularity <= 1),
    mood_valence REAL NOT NULL CHECK(mood_valence >= 0 AND mood_valence <= 1),
    mood_energy REAL NOT NULL CHECK(mood_energy >= 0 AND mood_energy <= 1),
    mood_tension REAL NOT NULL CHECK(mood_tension >= 0 AND mood_tension <= 1),
    mood_label TEXT NOT NULL,
    timbre_warmth REAL NOT NULL CHECK(timbre_warmth >= 0 AND timbre_warmth <= 1),
    timbre_brightness REAL NOT NULL CHECK(timbre_brightness >= 0 AND timbre_brightness <= 1),
    timbre_breathiness REAL NOT NULL CHECK(timbre_breathiness >= 0 AND timbre_breathiness <= 1),
    timbre_label TEXT NOT NULL,
    expression_vibrato REAL NOT NULL CHECK(expression_vibrato >= 0 AND expression_vibrato <= 1),
    expression_dynamic_range REAL NOT NULL CHECK(expression_dynamic_range >= 0 AND expression_dynamic_range <= 1),
    expression_articulation TEXT NOT NULL,
    confidence_overall REAL NOT NULL CHECK(confidence_overall >= 0 AND confidence_overall <= 1),
    raw_features_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

-- Recommendations table: 3-8 recommendation results per session
CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    rank INTEGER NOT NULL CHECK(rank >= 1 AND rank <= 8),
    genre TEXT NOT NULL,
    sub_style TEXT,
    tempo_range_low INTEGER NOT NULL,
    tempo_range_high INTEGER NOT NULL,
    vocal_difficulty INTEGER NOT NULL CHECK(vocal_difficulty >= 1 AND vocal_difficulty <= 5),
    mood_alignment TEXT NOT NULL,
    match_explanation TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'exploratory')),
    reference_songs TEXT,
    match_score REAL NOT NULL CHECK(match_score >= 0 AND match_score <= 1),
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

-- Indexes: speed up user-based session queries and time-based sorting
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON analysis_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON analysis_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_recommendations_session_id ON recommendations(session_id);
CREATE INDEX IF NOT EXISTS idx_vocal_profiles_session_id ON vocal_profiles(session_id);
"""


def _extract_db_path(database_url: str) -> str:
    """
    Extract the file path from a database_url string.
    Supported format: 'sqlite:///./tunemuse.db' -> './tunemuse.db'

    Args:
        database_url: SQLite connection string

    Returns:
        The actual path to the database file
    """
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    return database_url


async def init_database(database_url: str | None = None) -> None:
    """
    Initialize the database: create all tables and indexes, enable WAL mode.
    Skips if tables already exist (using IF NOT EXISTS).

    Args:
        database_url: SQLite database connection string, defaults to DEFAULT_DB_PATH

    Example:
        await init_database("sqlite:///./tunemuse.db")
    """
    db_path = _extract_db_path(database_url or f"sqlite:///{DEFAULT_DB_PATH}")

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode: allows concurrent reads, improves performance
        await db.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        await db.execute("PRAGMA foreign_keys=ON")

        # Execute table creation SQL
        await db.executescript(SCHEMA_SQL)
        await db.commit()


async def get_connection(database_url: str | None = None) -> aiosqlite.Connection:
    """
    Get a database connection. The caller is responsible for closing it.

    Args:
        database_url: SQLite database connection string

    Returns:
        An aiosqlite async connection object

    Example:
        db = await get_connection()
        try:
            # use db...
        finally:
            await db.close()
    """
    db_path = _extract_db_path(database_url or f"sqlite:///{DEFAULT_DB_PATH}")
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db
