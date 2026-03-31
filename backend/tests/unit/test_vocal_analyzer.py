"""
Vocal analyzer service unit tests.

Tests core functions in the app.services.vocal_analyzer module:
- hz_to_note: frequency to note name conversion
- analyze_features: Conversion of original feature vectors to structured Vocal profile
"""

import pytest

from app.services.vocal_analyzer import analyze_features, hz_to_note


# ---------------------------------------------------------------------------
# Standard test feature data (audio feature vector extracted by the simulation client)
# ---------------------------------------------------------------------------
SAMPLE_FEATURES = {
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
}


# ===================================================================
# hz_to_note test
# ===================================================================


class TestHzToNote:
    """Test frequency to note name conversion."""

    def test_hz_to_note_a4(self):
        """A4 = 440 Hz is the international standard pitch and should be converted accurately."""
        assert hz_to_note(440.0) == "A4"

    def test_hz_to_note_c4(self):
        """C4 (Middle C) ≈ 261.63 Hz, one of the most common reference notes."""
        assert hz_to_note(261.63) == "C4"

    def test_hz_to_note_zero(self):
        """A frequency of 0 should return 'N/A', indicating that a valid pitch cannot be detected."""
        assert hz_to_note(0) == "N/A"


# ===================================================================
# analyze_features test
# ===================================================================


class TestAnalyzeFeatures:
    """Test the complete conversion process from original feature vector to Vocal profile."""

    def test_analyze_features_returns_all_dimensions(self):
        """
        Vocal profile should contain all 6 top-level keys:
        The five dimensions of pitch, rhythm, mood, timbre, expression + confidence.
        """
        result = analyze_features(SAMPLE_FEATURES)
        expected_keys = {"pitch", "rhythm", "mood", "timbre", "expression", "confidence"}
        assert expected_keys == set(result.keys())

    def test_analyze_features_pitch_notes(self):
        """
        Verify that Hz values ​​in the pitch dimension are correctly converted to note names.
        pitch_min_hz=196.0 -> G3, pitch_max_hz=523.25 -> C5
        """
        result = analyze_features(SAMPLE_FEATURES)
        pitch = result["pitch"]
        # 196 Hz ≈ G3
        assert pitch["range_low"] == hz_to_note(196.0)
        # 523.25 Hz ≈ C5
        assert pitch["range_high"] == hz_to_note(523.25)

    def test_analyze_features_timbre_classification(self):
        """
        A high warmth MFCC (mfcc_mean[0] = 15.0) should produce warmth > 0.5.

        Warmth mapping formula: warmth = clamp((mfcc[0] + 10) / 40)
        mfcc[0] = 15.0 -> (15 + 10) / 40 = 0.625 > 0.5
        """
        result = analyze_features(SAMPLE_FEATURES)
        assert result["timbre"]["warmth"] > 0.5

    def test_analyze_features_confidence_range(self):
        """The confidence level must be in the range [0, 1] to ensure that the normalization logic is correct."""
        result = analyze_features(SAMPLE_FEATURES)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_analyze_features_edge_case_narrow_range(self):
        """
        When pitch_min_hz is very close to pitch_max_hz,
        The analysis should not crash and should return results normally (reduced to a very narrow range).
        """
        narrow_features = {**SAMPLE_FEATURES, "pitch_min_hz": 440.0, "pitch_max_hz": 441.0}
        result = analyze_features(narrow_features)
        # Pass without crashing and returning the complete structure
        assert "pitch" in result
        assert "confidence" in result
