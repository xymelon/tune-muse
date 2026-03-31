/**
 * TuneMuse frontend type definitions
 *
 * TypeScript interfaces aligned with the backend API contract.
 * Covers audio features, vocal analysis, recommendations, session management, and authentication data structures.
 */

// ============================================================
// Audio Features — Extracted on the client side via Meyda.js + pitchfinder
// ============================================================

/** Audio feature vector extracted on the client side */
export interface AudioFeatures {
  mfcc_mean: number[];        // Mean of 13 MFCC coefficients
  mfcc_std: number[];         // Standard deviation of 13 MFCC coefficients
  pitch_min_hz: number;       // Minimum fundamental frequency (Hz)
  pitch_max_hz: number;       // Maximum fundamental frequency (Hz)
  pitch_median_hz: number;    // Median fundamental frequency (Hz)
  pitch_stability: number;    // Pitch stability 0-1
  pitch_contour_stats: {
    mean: number;
    std: number;
    quartile_25: number;
    quartile_75: number;
  };
  tempo_bpm: number | null;   // Tempo in BPM, null if undetectable
  rhythm_regularity: number;  // Rhythm regularity 0-1
  spectral_centroid_mean: number;   // Spectral centroid mean
  spectral_centroid_std: number;    // Spectral centroid standard deviation
  spectral_flatness_mean: number;   // Spectral flatness mean
  spectral_rolloff_mean: number;    // Spectral rolloff mean
  zero_crossing_rate_mean: number;  // Zero crossing rate mean
  rms_mean: number;                 // RMS energy mean
  rms_std: number;                  // RMS energy standard deviation
  chroma_mean: number[];            // Chroma mean for 12 pitch classes
  signal_quality_score: number;     // Signal quality score 0-1
}

// ============================================================
// Analysis Request / Response
// ============================================================

/** Request body for submitting analysis */
export interface AnalyzeRequest {
  source_type: 'recording' | 'upload'; // Audio source: live recording / file upload
  duration_seconds: number;            // Audio duration (seconds)
  features: AudioFeatures;             // Client-extracted features
}

// ============================================================
// Vocal Profile — Dimensions of the analysis result
// ============================================================

/** Pitch profile */
export interface PitchProfile {
  range_low: string;          // Lowest note name, e.g. "C3"
  range_high: string;         // Highest note name, e.g. "A4"
  comfortable_zone: string;   // Comfortable vocal zone, e.g. "E3-E4"
  stability: number;          // Stability score
  description: string;        // Natural language description
}

/** Rhythm profile */
export interface RhythmProfile {
  tempo_bpm: number | null;   // Tempo in BPM
  regularity: number;         // Regularity score
  description: string;
}

/** Mood profile */
export interface MoodProfile {
  valence: number;            // Valence (positive/negative)
  energy: number;             // Energy level
  tension: number;            // Tension level
  label: string;              // Mood label
  description: string;
}

/** Timbre profile */
export interface TimbreProfile {
  warmth: number;             // Warmth
  brightness: number;         // Brightness
  breathiness: number;        // Breathiness
  label: string;              // Timbre label
  description: string;
}

/** Expression profile */
export interface ExpressionProfile {
  vibrato: number;            // Vibrato intensity
  dynamic_range: number;      // Dynamic range
  articulation: string;       // Articulation clarity description
  description: string;
}

/** Complete vocal profile aggregating all dimensions */
export interface VocalProfile {
  pitch: PitchProfile;
  rhythm: RhythmProfile;
  mood: MoodProfile;
  timbre: TimbreProfile;
  expression: ExpressionProfile;
  confidence: number;         // Overall analysis confidence
}

// ============================================================
// Recommendations
// ============================================================

/** Single music style recommendation */
export interface Recommendation {
  rank: number;                               // Ranking
  genre: string;                              // Music genre
  sub_style: string | null;                   // Sub-style (optional)
  tempo_range: { low: number; high: number }; // Recommended tempo range
  vocal_difficulty: number;                   // Vocal difficulty 1-5
  mood_alignment: string;                     // Mood alignment description
  match_explanation: string;                  // Match reason explanation
  confidence: 'high' | 'medium' | 'exploratory'; // Confidence level
  reference_songs: string[] | null;           // Reference tracks
  match_score: number;                        // Match score
}

/** Analysis response — contains vocal profile and recommendation list */
export interface AnalyzeResponse {
  session_id: string;
  status: 'completed' | 'processing' | 'failed';
  vocal_profile: VocalProfile;
  recommendations: Recommendation[];
}

// ============================================================
// Session Management
// ============================================================

/** Session summary — used for list display */
export interface SessionSummary {
  id: string;
  source_type: 'recording' | 'upload';
  status: string;
  audio_duration_sec: number;
  vocal_profile_summary: {
    pitch_range: string;     // e.g. "C3-A4"
    mood_label: string;      // e.g. "Warm and calm"
    timbre_label: string;    // e.g. "Bright and clear"
  };
  recommendation_count: number;
  created_at: string;        // ISO 8601 timestamp
}

/** Session list response — with pagination support */
export interface SessionListResponse {
  sessions: SessionSummary[];
  total: number;
  limit: number;
  offset: number;
}

/** Session detail response — extends analysis response with metadata */
export interface SessionDetailResponse extends AnalyzeResponse {
  source_type: 'recording' | 'upload';
  audio_duration_sec: number;
  created_at: string;
  completed_at: string | null;
}

// ============================================================
// Common Types
// ============================================================

/** Audio quality check result */
export interface QualityResult {
  passed: boolean;           // Whether the quality check passed
  issues: string[];          // List of detected issues
  score: number;             // Quality score
}

/** API error response */
export interface ApiError {
  error: string;             // Error code
  message: string;           // User-readable error message
  details?: Array<{          // Field-level error details (optional)
    field: string;
    issue: string;
  }>;
}

// ============================================================
// Authentication
// ============================================================

/** Register/Login request */
export interface AuthRequest {
  email: string;
  password: string;
  display_name?: string;     // Only used during registration
  locale?: 'en' | 'zh-CN';  // User language preference
}

/** Authentication success response */
export interface AuthResponse {
  user_id: string;
  email: string;
  display_name: string;
  token: string;             // JWT token
}
