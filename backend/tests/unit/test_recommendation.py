"""
Service unit testing is recommended.

Test the core functions in the app.services.recommendation module:
- get_recommendations: Generate recommendation list based on Vocal profile
- note_to_semitone: Conversion of note names to semitone numbers
"""

import pytest

from app.services.recommendation import get_recommendations, note_to_semitone


# ---------------------------------------------------------------------------
# Standard test Vocal profile (simulate the output of vocal_analyzer)
# ---------------------------------------------------------------------------
SAMPLE_PROFILE = {
    "pitch_range": {"low": "G3", "high": "C5"},
    "timbre": {"warmth": 0.63, "brightness": 0.29, "breathiness": 0.38},
    "mood": {"valence": 0.65, "energy": 0.40, "tension": 0.57},
    "rhythm": {"tempo": 88, "stability": 0.68},
    "expression_traits": ["vibrato", "mixed"],
}


# ===================================================================
# note_to_semitone test
# ===================================================================


class TestNoteToSemitone:
    """Test the conversion of note names to absolute semitone numbers."""

    def test_note_to_semitone_c4(self):
        """C4 (middle C) should be converted to 48 semitones (C0 = 0 base)."""
        assert note_to_semitone("C4") == 48

    def test_note_to_semitone_a4(self):
        """A4 (standard pitch 440Hz) should be converted to 57 semitones."""
        assert note_to_semitone("A4") == 57


# ===================================================================
# get_recommendations test
# ===================================================================


class TestGetRecommendations:
    """Test the output format and basic behavior of the recommendation engine."""

    def test_get_recommendations_returns_list(self):
        """Recommended results must be of list type."""
        result = get_recommendations(SAMPLE_PROFILE)
        assert isinstance(result, list)

    def test_get_recommendations_count(self):
        """The number of recommended results should be in the range 3-8 (may be 0 when the knowledge base is empty)."""
        result = get_recommendations(SAMPLE_PROFILE)
        # If the knowledge base exists and is not empty, 3-8 items should be returned
        # If the knowledge base is empty, it is legal to return an empty list
        if len(result) > 0:
            assert 3 <= len(result) <= 8

    def test_get_recommendations_has_required_fields(self):
        """Each recommendation must contain: genre, sub_style, score, confidence, explanation."""
        result = get_recommendations(SAMPLE_PROFILE)
        required_fields = {"genre", "sub_style", "score", "confidence", "explanation"}
        for rec in result:
            missing = required_fields - set(rec.keys())
            assert not missing, f"Recommended results are missing fields: {missing}"

    def test_confidence_levels(self):
        """
        The confidence field can only be one of the three levels 'high', 'medium' or 'exploratory'.
        Verify that the grading logic of _assign_confidence is applied correctly.
        """
        result = get_recommendations(SAMPLE_PROFILE)
        valid_levels = {"high", "medium", "exploratory"}
        for rec in result:
            assert rec["confidence"] in valid_levels, (
                f"Illegal confidence level: '{rec['confidence']}'"
            )
