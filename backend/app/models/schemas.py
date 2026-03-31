"""
Pydantic request/response models matching the TuneMuse API contract.

All models use Pydantic v2 syntax. Float scores that represent normalized
values (e.g. confidence, quality, intensity) are constrained to [0.0, 1.0]
via Field(ge=0.0, le=1.0).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Audio analysis request models
# ---------------------------------------------------------------------------


class PitchContourStats(BaseModel):
    """
    Statistical summary of a pitch contour extracted from the audio signal.

    Contains the min/max/mean pitch values in Hz and optional standard
    deviation, giving a compact representation of the singer's pitch range
    and variability within a single recording.
    """

    pitch_min: float = Field(..., description="Minimum detected pitch in Hz")
    pitch_max: float = Field(..., description="Maximum detected pitch in Hz")
    pitch_mean: float = Field(..., description="Mean detected pitch in Hz")
    pitch_std: Optional[float] = Field(
        None, description="Standard deviation of pitch in Hz"
    )


class AudioFeatures(BaseModel):
    """
    Pre-computed audio features sent from the frontend audio analysis pipeline.

    These features are extracted client-side (e.g. via Web Audio API / Essentia.js)
    and forwarded to the backend for vocal profiling and recommendation.
    """

    pitch_contour: PitchContourStats = Field(
        ..., description="Statistical summary of the pitch contour"
    )
    spectral_centroid_mean: Optional[float] = Field(
        None, description="Mean spectral centroid in Hz (brightness indicator)"
    )
    rms_energy_mean: Optional[float] = Field(
        None, description="Mean RMS energy (loudness proxy)"
    )
    zero_crossing_rate_mean: Optional[float] = Field(
        None, description="Mean zero-crossing rate (noisiness indicator)"
    )
    tempo_bpm: Optional[float] = Field(
        None, description="Estimated tempo in beats per minute"
    )


class AnalyzeRequest(BaseModel):
    """
    Request body for the POST /analyze endpoint.

    The client submits a chunk of vocal audio described by its duration,
    pre-extracted features, a signal quality score, and optionally extra
    context such as genre preferences.

    Validation rules:
    - duration must be between 5 and 180 seconds.
    - pitch_min must be strictly less than pitch_max.
    - signal_quality must be in [0.0, 1.0].
    """

    duration: float = Field(
        ...,
        gt=0,
        description="Duration of the audio clip in seconds (5-180)",
    )
    features: AudioFeatures = Field(
        ..., description="Pre-computed audio features from client"
    )
    signal_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Signal quality score between 0 and 1",
    )
    source_type: str = Field(
        "microphone",
        description="Audio source type, e.g. 'microphone' or 'upload'",
    )
    genre_preferences: Optional[list[str]] = Field(
        None, description="Optional list of preferred genres for recommendations"
    )

    # -- Validators ----------------------------------------------------------

    @field_validator("duration")
    @classmethod
    def duration_in_range(cls, v: float) -> float:
        """Ensure duration is between 5 and 180 seconds."""
        if v < 5 or v > 180:
            raise ValueError("duration must be between 5 and 180 seconds")
        return v

    @model_validator(mode="after")
    def pitch_min_less_than_max(self) -> "AnalyzeRequest":
        """Ensure pitch_min is strictly less than pitch_max in the contour stats."""
        contour = self.features.pitch_contour
        if contour.pitch_min >= contour.pitch_max:
            raise ValueError("pitch_min must be less than pitch_max")
        return self


# ---------------------------------------------------------------------------
# Vocal profile response models
# ---------------------------------------------------------------------------


class PitchProfile(BaseModel):
    """
    Describes the singer's pitch characteristics derived from the analysis.

    Includes the detected range in Hz, an estimated vocal classification
    (e.g. 'tenor', 'alto'), and a stability score indicating how steadily
    the singer can hold pitch.
    """

    range_min_hz: float = Field(..., description="Lower bound of detected vocal range in Hz")
    range_max_hz: float = Field(..., description="Upper bound of detected vocal range in Hz")
    vocal_classification: str = Field(
        ..., description="Estimated vocal type, e.g. 'soprano', 'tenor', 'baritone'"
    )
    stability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Pitch stability score (0 = unstable, 1 = rock-solid)"
    )


class RhythmProfile(BaseModel):
    """
    Rhythmic characteristics of the vocal performance.

    Captures detected tempo, how accurately the singer stays on-beat,
    and any swing or syncopation tendency.
    """

    tempo_bpm: Optional[float] = Field(None, description="Detected tempo in BPM")
    timing_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="How closely the singer follows the beat (0-1)"
    )
    swing_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Swing feel ratio (0 = straight, 1 = heavy swing)"
    )


class MoodProfile(BaseModel):
    """
    Emotional/mood classification inferred from vocal features.

    The primary mood is a human-readable label (e.g. 'melancholic', 'energetic'),
    accompanied by valence (positive/negative) and energy (calm/excited) axes.
    """

    primary_mood: str = Field(..., description="Dominant mood label, e.g. 'joyful', 'melancholic'")
    valence: float = Field(
        ..., ge=0.0, le=1.0, description="Emotional valence (0 = negative, 1 = positive)"
    )
    energy: float = Field(
        ..., ge=0.0, le=1.0, description="Energy level (0 = calm, 1 = excited)"
    )


class TimbreProfile(BaseModel):
    """
    Timbral qualities of the voice.

    Brightness indicates how much high-frequency energy is present,
    warmth measures low-mid richness, and breathiness captures
    the amount of air noise in the voice.
    """

    brightness: float = Field(
        ..., ge=0.0, le=1.0, description="Spectral brightness (0 = dark, 1 = bright)"
    )
    warmth: float = Field(
        ..., ge=0.0, le=1.0, description="Timbral warmth (0 = thin, 1 = warm/full)"
    )
    breathiness: float = Field(
        ..., ge=0.0, le=1.0, description="Breathiness level (0 = clear, 1 = airy)"
    )


class ExpressionProfile(BaseModel):
    """
    Expressive qualities of the vocal performance.

    Captures vibrato presence, dynamic range usage, and overall
    expressiveness which combines multiple micro-features.
    """

    vibrato_extent: float = Field(
        ..., ge=0.0, le=1.0, description="Vibrato intensity (0 = none, 1 = heavy)"
    )
    dynamic_range: float = Field(
        ..., ge=0.0, le=1.0, description="Dynamic range usage (0 = flat, 1 = very dynamic)"
    )
    expressiveness: float = Field(
        ..., ge=0.0, le=1.0, description="Overall expressiveness score (0-1)"
    )


class VocalProfileResponse(BaseModel):
    """
    Complete vocal profile assembled from all sub-profiles.

    This is the primary output of the audio analysis pipeline, combining
    pitch, rhythm, mood, timbre, and expression into one coherent profile
    that drives the recommendation engine.
    """

    pitch: PitchProfile
    rhythm: RhythmProfile
    mood: MoodProfile
    timbre: TimbreProfile
    expression: ExpressionProfile


# ---------------------------------------------------------------------------
# Recommendation models
# ---------------------------------------------------------------------------


class RecommendationResponse(BaseModel):
    """
    A single song recommendation returned by the recommendation engine.

    Each recommendation includes the song metadata, a match score, a human-readable
    explanation of why this song suits the singer, and a confidence level.

    Confidence levels:
    - 'high': strong feature alignment with the vocal profile.
    - 'medium': reasonable match with some uncertainty.
    - 'exploratory': stretch suggestion to help the singer grow.
    """

    song_title: str = Field(..., description="Title of the recommended song")
    artist: str = Field(..., description="Artist or band name")
    genre: str = Field(..., description="Primary genre of the song")
    match_score: float = Field(
        ..., ge=0.0, le=1.0, description="How well this song matches the vocal profile (0-1)"
    )
    confidence: Literal["high", "medium", "exploratory"] = Field(
        ..., description="Confidence level of this recommendation"
    )
    explanation: str = Field(
        ..., description="Human-readable explanation of why this song is recommended"
    )
    preview_url: Optional[str] = Field(
        None, description="Optional URL to a song preview or streaming link"
    )


# ---------------------------------------------------------------------------
# Analyze response
# ---------------------------------------------------------------------------


class AnalyzeResponse(BaseModel):
    """
    Response body returned by POST /analyze after processing a vocal clip.

    Contains a unique session ID, processing status, the computed vocal
    profile, and a ranked list of song recommendations.
    """

    session_id: str = Field(..., description="Unique identifier for this analysis session")
    status: str = Field(
        ..., description="Processing status, e.g. 'complete', 'processing', 'error'"
    )
    vocal_profile: VocalProfileResponse = Field(
        ..., description="Full vocal profile derived from the audio"
    )
    recommendations: list[RecommendationResponse] = Field(
        default_factory=list, description="Ranked list of song recommendations"
    )


# ---------------------------------------------------------------------------
# Session history models
# ---------------------------------------------------------------------------


class SessionSummary(BaseModel):
    """
    Compact summary of a past analysis session, used in list views.

    Contains enough information to display a session card (id, status,
    primary mood, number of recommendations, and creation timestamp).
    """

    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Session status")
    primary_mood: Optional[str] = Field(
        None, description="Primary mood detected in this session"
    )
    recommendation_count: int = Field(
        0, description="Number of recommendations generated"
    )
    created_at: datetime = Field(..., description="Timestamp when the session was created")


class SessionListResponse(BaseModel):
    """
    Paginated list of session summaries returned by GET /sessions.
    """

    sessions: list[SessionSummary] = Field(
        default_factory=list, description="List of session summaries"
    )
    total: int = Field(0, description="Total number of sessions available")


class SessionDetailResponse(AnalyzeResponse):
    """
    Detailed view of a single analysis session (extends AnalyzeResponse).

    Adds metadata fields that are not part of the initial analyze response
    but are available when retrieving a stored session by ID.
    """

    source_type: str = Field(
        "microphone", description="Audio source type used in this session"
    )
    duration: float = Field(
        ..., description="Duration of the analyzed audio clip in seconds"
    )
    created_at: datetime = Field(..., description="Timestamp when the session was created")
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the last update to this session"
    )


# ---------------------------------------------------------------------------
# Authentication models
# ---------------------------------------------------------------------------


class AuthRegisterRequest(BaseModel):
    """
    Request body for POST /auth/register.

    Requires email and password. Display name and locale are optional;
    the backend will generate defaults if omitted.
    """

    email: str = Field(..., description="User email address (used as login identifier)")
    password: str = Field(
        ..., min_length=8, description="Password (minimum 8 characters)"
    )
    display_name: Optional[str] = Field(
        None, description="Optional display name shown in the UI"
    )
    locale: Optional[str] = Field(
        None, description="Optional locale code, e.g. 'en', 'zh-CN'"
    )


class AuthLoginRequest(BaseModel):
    """
    Request body for POST /auth/login.
    """

    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class AuthResponse(BaseModel):
    """
    Response body returned on successful registration or login.

    Contains the issued JWT token and basic user info so the frontend
    can populate the session immediately without a separate profile fetch.
    """

    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    token: str = Field(..., description="JWT bearer token for authenticated requests")


# ---------------------------------------------------------------------------
# Error models
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """
    Standard error response body returned for 4xx/5xx status codes.

    The 'error' field is a machine-readable error code (e.g. 'NOT_FOUND'),
    and 'message' provides a human-readable description.
    """

    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")


class ValidationErrorDetail(BaseModel):
    """
    Details of a single field validation failure.

    Used inside ValidationErrorResponse to pinpoint exactly which field
    failed and why, following a structure similar to FastAPI's default
    validation error format.
    """

    loc: list[str] = Field(
        ..., description="Path to the field that failed validation, e.g. ['body', 'duration']"
    )
    msg: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Error type identifier, e.g. 'value_error'")


class ValidationErrorResponse(BaseModel):
    """
    Response body for 422 Unprocessable Entity errors.

    Contains a list of individual field-level validation errors so the
    frontend can display targeted feedback next to the relevant inputs.
    """

    error: str = Field(default="VALIDATION_ERROR", description="Error code")
    message: str = Field(
        default="Request validation failed", description="Summary message"
    )
    details: list[ValidationErrorDetail] = Field(
        default_factory=list, description="List of individual validation errors"
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """
    Response body for the GET /health endpoint.

    Returns the application status and current version string. Used by
    load balancers, monitoring systems, and deployment pipelines to verify
    the service is running correctly.
    """

    status: str = Field(..., description="Service status, e.g. 'ok'")
    version: str = Field(..., description="Application version string, e.g. '0.1.0'")
