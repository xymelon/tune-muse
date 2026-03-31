# API Contracts: AI Music Recommendation

**Feature**: 001-ai-music-recommend
**Date**: 2026-03-29
**Base URL**: `/api/v1`
**Format**: JSON (application/json) unless noted

---

## POST /api/v1/analyze

Submit extracted audio features for vocal analysis and song recommendation.

**Description**: The primary analysis endpoint. Receives a feature vector
extracted client-side (by Meyda.js + pitchfinder) and returns a vocal profile
with personalized song direction recommendations.

### Request

**Content-Type**: `application/json`

```json
{
  "source_type": "recording",
  "duration_seconds": 28.5,
  "features": {
    "mfcc_mean": [12.3, -4.1, 2.8, 1.2, -0.5, 0.8, -0.3, 0.2, -0.1, 0.05, -0.02, 0.01, -0.005],
    "mfcc_std": [3.2, 1.1, 0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.08, 0.06, 0.04, 0.03],
    "pitch_min_hz": 130.8,
    "pitch_max_hz": 440.0,
    "pitch_median_hz": 261.6,
    "pitch_stability": 0.82,
    "pitch_contour_stats": {
      "mean": 265.3,
      "std": 45.2,
      "quartile_25": 220.0,
      "quartile_75": 310.0
    },
    "tempo_bpm": 92,
    "rhythm_regularity": 0.75,
    "spectral_centroid_mean": 2100.5,
    "spectral_centroid_std": 450.2,
    "spectral_flatness_mean": 0.12,
    "spectral_rolloff_mean": 4200.0,
    "zero_crossing_rate_mean": 0.08,
    "rms_mean": 0.15,
    "rms_std": 0.04,
    "chroma_mean": [0.5, 0.3, 0.2, 0.4, 0.6, 0.3, 0.2, 0.5, 0.4, 0.3, 0.2, 0.4],
    "signal_quality_score": 0.88
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_type | string | yes | "recording" or "upload" |
| duration_seconds | number | yes | Duration of analyzed audio (5.0–180.0) |
| features | object | yes | Extracted audio features (see below) |
| features.mfcc_mean | number[13] | yes | Mean of 13 MFCC coefficients |
| features.mfcc_std | number[13] | yes | Std deviation of 13 MFCC coefficients |
| features.pitch_min_hz | number | yes | Lowest detected fundamental frequency |
| features.pitch_max_hz | number | yes | Highest detected fundamental frequency |
| features.pitch_median_hz | number | yes | Median pitch frequency |
| features.pitch_stability | number | yes | Pitch stability score (0.0–1.0) |
| features.pitch_contour_stats | object | yes | Statistical summary of pitch contour |
| features.tempo_bpm | number | no | Estimated tempo (null if not detectable) |
| features.rhythm_regularity | number | yes | Rhythm regularity score (0.0–1.0) |
| features.spectral_centroid_mean | number | yes | Mean spectral centroid (Hz) |
| features.spectral_centroid_std | number | yes | Std of spectral centroid |
| features.spectral_flatness_mean | number | yes | Mean spectral flatness (0.0–1.0) |
| features.spectral_rolloff_mean | number | yes | Mean spectral rolloff (Hz) |
| features.zero_crossing_rate_mean | number | yes | Mean zero crossing rate |
| features.rms_mean | number | yes | Mean RMS energy |
| features.rms_std | number | yes | Std of RMS energy |
| features.chroma_mean | number[12] | yes | Mean chroma vector (12 pitch classes) |
| features.signal_quality_score | number | yes | Signal quality assessment (0.0–1.0) |

### Response (200 OK)

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "vocal_profile": {
    "pitch": {
      "range_low": "C3",
      "range_high": "A4",
      "comfortable_zone": "E3–E4",
      "stability": 0.82,
      "description": "Your voice comfortably spans nearly two octaves with good pitch control."
    },
    "rhythm": {
      "tempo_bpm": 92,
      "regularity": 0.75,
      "description": "You naturally gravitate toward moderate tempos with a steady, relaxed rhythmic feel."
    },
    "mood": {
      "valence": 0.4,
      "energy": 0.35,
      "tension": 0.5,
      "label": "Reflective & Gentle",
      "description": "Your singing conveys a thoughtful, introspective quality with gentle emotional depth."
    },
    "timbre": {
      "warmth": 0.78,
      "brightness": 0.35,
      "breathiness": 0.55,
      "label": "Warm & Breathy",
      "description": "Your voice has a warm, slightly breathy quality that creates an intimate, personal feel."
    },
    "expression": {
      "vibrato": 0.6,
      "dynamic_range": 0.5,
      "articulation": "legato",
      "description": "You use gentle vibrato and smooth phrasing with moderate dynamic variation."
    },
    "confidence": 0.85
  },
  "recommendations": [
    {
      "rank": 1,
      "genre": "Ballad",
      "sub_style": "Classic Ballad",
      "tempo_range": { "low": 60, "high": 85 },
      "vocal_difficulty": 2,
      "mood_alignment": "Matches your reflective, gentle emotional expression",
      "match_explanation": "Your warm timbre and stable mid-range pitch (C3–A4) are ideal for ballad-style singing. The gentle vibrato and legato phrasing detected in your voice suit the sustained melodic lines typical of classic ballads at 60–85 BPM.",
      "confidence": "high",
      "reference_songs": ["Someone Like You – Adele", "Yesterday – The Beatles", "Moon Serenade – Hacken Lee"],
      "match_score": 0.87
    },
    {
      "rank": 2,
      "genre": "Folk",
      "sub_style": "Singer-Songwriter Folk",
      "tempo_range": { "low": 75, "high": 110 },
      "vocal_difficulty": 2,
      "mood_alignment": "Suits your introspective vocal character",
      "match_explanation": "The breathy warmth in your voice creates the intimate, conversational quality that defines singer-songwriter folk. Your comfortable range and moderate dynamic variation work well for storytelling through song.",
      "confidence": "high",
      "reference_songs": ["Dust in the Wind – Kansas", "Chengdu – Zhao Lei"],
      "match_score": 0.82
    }
  ]
}
```

### Error Responses

**400 Bad Request** — Invalid or missing features:
```json
{
  "error": "validation_error",
  "message": "Feature vector validation failed",
  "details": [
    { "field": "features.pitch_min_hz", "issue": "must be less than pitch_max_hz" }
  ]
}
```

**422 Unprocessable Entity** — Audio quality too low:
```json
{
  "error": "low_quality_audio",
  "message": "The audio signal quality is too low for reliable analysis. Please re-record in a quieter environment.",
  "signal_quality_score": 0.18,
  "minimum_required": 0.3
}
```

---

## POST /api/v1/upload

Upload an audio file for server-side feature extraction and analysis.

**Description**: Alternative to the client-side feature extraction path.
Accepts audio files, extracts features server-side, and returns the same
vocal profile + recommendations as the /analyze endpoint.

### Request

**Content-Type**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | binary | yes | Audio file (MP3, WAV, M4A, OGG). Max 10 MB. |

### Response (200 OK)

Same response schema as `POST /api/v1/analyze`.

### Error Responses

**400 Bad Request** — Unsupported format:
```json
{
  "error": "unsupported_format",
  "message": "Unsupported audio format. Please upload MP3, WAV, M4A, or OGG files.",
  "received_content_type": "application/pdf"
}
```

**413 Payload Too Large**:
```json
{
  "error": "file_too_large",
  "message": "File size exceeds the 10 MB limit.",
  "max_size_bytes": 10485760
}
```

**422 Unprocessable Entity** — No vocals detected:
```json
{
  "error": "no_vocal_content",
  "message": "No vocal content was detected in the uploaded audio. This tool requires singing voice input — instrumental-only audio cannot be analyzed."
}
```

---

## GET /api/v1/sessions

Retrieve analysis history for the authenticated user.

**Authentication**: Required (Bearer token)

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | integer | 20 | Max sessions to return (1–100) |
| offset | integer | 0 | Pagination offset |
| sort | string | "desc" | Sort by created_at: "asc" or "desc" |

### Response (200 OK)

```json
{
  "sessions": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "source_type": "recording",
      "status": "completed",
      "audio_duration_sec": 28.5,
      "vocal_profile_summary": {
        "pitch_range": "C3–A4",
        "mood_label": "Reflective & Gentle",
        "timbre_label": "Warm & Breathy"
      },
      "recommendation_count": 5,
      "created_at": "2026-03-29T14:30:00Z"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

**401 Unauthorized**:
```json
{
  "error": "unauthorized",
  "message": "Authentication required to view analysis history."
}
```

---

## GET /api/v1/sessions/:id

Retrieve full details of a specific analysis session.

**Authentication**: Required (Bearer token). User can only access own sessions.

### Response (200 OK)

Same schema as `POST /api/v1/analyze` response, plus:

```json
{
  "session_id": "...",
  "status": "completed",
  "source_type": "recording",
  "audio_duration_sec": 28.5,
  "created_at": "2026-03-29T14:30:00Z",
  "completed_at": "2026-03-29T14:30:22Z",
  "vocal_profile": { "..." },
  "recommendations": [ "..." ]
}
```

**404 Not Found**:
```json
{
  "error": "not_found",
  "message": "Analysis session not found."
}
```

---

## POST /api/v1/auth/register

Register a new user account.

### Request

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "display_name": "Song Explorer",
  "locale": "zh-CN"
}
```

### Response (201 Created)

```json
{
  "user_id": "u1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "user@example.com",
  "display_name": "Song Explorer",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**409 Conflict**: Email already registered.

---

## POST /api/v1/auth/login

Authenticate an existing user.

### Request

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

### Response (200 OK)

```json
{
  "user_id": "u1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "display_name": "Song Explorer"
}
```

**401 Unauthorized**: Invalid credentials.

---

## GET /api/v1/health

Health check endpoint.

### Response (200 OK)

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```
