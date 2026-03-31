"""
Recommendation Service—Hybrid Rules Engine

This module implements a hybrid rule engine based on weighted matching, which is used to profile the user's vocal characteristics.
(vocal profile) is matched with the song direction knowledge base and outputs top-N recommendation results.

The core idea of ​​the algorithm:
    1. Load all active song directions in the knowledge base
    2. For each direction, score based on 5 dimensions:
       - Pitch range overlap (30%) — whether the user's range covers the tonal range of the direction
       - Timbre affinity (25%) — Whether the user’s timbre parameters fall within the direction’s preferred range
       - Mood alignment (20%) — the Euclidean distance between the user’s emotion vector and the directional emotion portrait
       - Rhythm fit (15%) – whether the beat speed and rhythm stability are compatible
       - Expressive Match (10%) — The intersection of the user’s expressive characteristics and directional requirements
    3. Sort by comprehensive score in descending order, take top 3-8 items
    4. Generate natural language explanations for each recommendation

How to use:
    from app.services.recommendation import get_recommendations

    profile = {
        "pitch_range": {"low": "C3", "high": "G4"},
        "timbre": {"warmth": 0.7, "brightness": 0.4, "breathiness": 0.5},
        "mood": {"valence": 0.3, "energy": 0.2, "tension": 0.5},
        "rhythm": {"tempo": 78, "stability": 0.6},
        "expression_traits": ["vibrato", "legato"],
    }
    results = get_recommendations(profile)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#Knowledge base cache - resident in memory after first load to avoid repeated IO
# ---------------------------------------------------------------------------
_directions_cache: list[dict] | None = None

# Knowledge base file path (two levels up from this file to app/knowledge_base/)
_KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "directions.json"

# ---------------------------------------------------------------------------
# Rating weight configuration
# ---------------------------------------------------------------------------
WEIGHT_PITCH = 0.30 # Overlapping pitch ranges
WEIGHT_TIMBRE = 0.25 # Timbre affinity
WEIGHT_MOOD = 0.20    # Mood alignment
WEIGHT_RHYTHM = 0.15 # Rhythm fit
WEIGHT_EXPRESSION = 0.10 # Expressive matching

# Recommended quantity range
MIN_RECOMMENDATIONS = 3
MAX_RECOMMENDATIONS = 8

# ---------------------------------------------------------------------------
# note → semitone number mapping table
# ---------------------------------------------------------------------------
# Basic note name to semitone offset (with C as 0)
_NOTE_BASE: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}


def note_to_semitone(note: str) -> int:
    """
    Convert note names to absolute semitone numbers (based on C0 = 0).

    Supported formats:
        - Basic note name + octave: C4, G3, A2
        - With sharp sign (#/♯): C#4, F#3
        - With flat (b/♭): Bb2, Eb4

    Conversion rules:
        Number of semitones = basic note offset + sharp and flat correction + number of octaves * 12

    Example:
        >>> note_to_semitone("C4") # Center C
        48
        >>> note_to_semitone("A4") # Standard pitch 440Hz
        57
        >>> note_to_semitone("Bb2") # B flat, 2nd octave
        34

    Args:
        note: note string, such as "C4", "Bb2", "F#3"

    Returns:
        Corresponding absolute semitone number (integer)

    Raises:
        ValueError: thrown when the note format cannot be parsed
    """
    if not note or len(note) < 2:
        raise ValueError(f"Unable to parse note: '{note}'")

    # Extract the basic sound name (first character)
    base_name = note[0].upper()
    if base_name not in _NOTE_BASE:
        raise ValueError(f"Unknown note name: '{base_name}' (Full input: '{note}')")

    base_semitone = _NOTE_BASE[base_name]

    # Parse sharps and flats and octaves
    # Note format: [A-G][#/b/♯/♭]*[0-9]
    modifier = 0
    octave_str = ""

    for char in note[1:]:
        if char in ("#", "♯"):
            modifier += 1
        elif char in ("b", "♭"):
            modifier -= 1
        elif char.isdigit() or (char == "-" and not octave_str):
            octave_str += char
        else:
            raise ValueError(f"The note contains illegal characters '{char}': '{note}'")

    if not octave_str:
        raise ValueError(f"Note missing octave: '{note}'")

    octave = int(octave_str)
    return octave * 12 + base_semitone + modifier


def _load_knowledge_base() -> list[dict]:
    """
    Loads the song direction knowledge base, returning only entries with active=true.

    Behavior description:
        - Read the JSON file from disk and cache it into module-level variables when called for the first time
        - Subsequent calls directly return cached data, with zero IO overhead
        - When the file does not exist or the JSON format is incorrect, log a warning and return an empty list

    Returns:
        Active state direction dictionary list
    """
    global _directions_cache

    if _directions_cache is not None:
        return _directions_cache

    try:
        raw = _KB_PATH.read_text(encoding="utf-8")
        all_directions: list[dict] = json.loads(raw)
        # Keep only enabled directions
        _directions_cache = [d for d in all_directions if d.get("active", False)]
        logger.info("Knowledge base loaded successfully, total %d valid directions", len(_directions_cache))
    except FileNotFoundError:
        logger.warning("Knowledge base file does not exist: %s - will return empty recommendations", _KB_PATH)
        _directions_cache = []
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Knowledge base JSON parsing failed: %s — will return empty recommendations", exc)
        _directions_cache = []

    return _directions_cache


# ---------------------------------------------------------------------------
# Sub-scoring function of five dimensions
# ---------------------------------------------------------------------------

def score_pitch_overlap(profile: dict, direction: dict) -> float:
    """
    Calculate the degree of overlap between the user's vocal range and the directional tonal range.

    Algorithm logic:
        1. Convert the upper and lower limits of the user's vocal range and the tonal range of the direction into semitone numbers.
        2. Calculate the intersection length of two intervals
        3. Divide the intersection length by the direction interval length to obtain the coverage rate
        4. Extra bonus: If the user's vocal range completely covers the directional range, full points will be given

    Calculation formula:
        overlap = max(0, min(user_high, dir_high) - max(user_low, dir_low))
        score   = overlap / dir_range_size

    Example:
        User range C3-G4 (48-67), directional range A2-F4 (33-65)
        overlap = min(67,65) - max(48,33) = 65 - 48 = 17
        dir_range = 65 - 33 = 32
        score = 17 / 32 = 0.53

    Args:
        profile: user's vocal portrait, which must include profile["pitch_range"]["low/high"]
        direction: direction dictionary, must contain direction["key_range"]["low/high"]

    Returns:
        Floating point number from 0.0 ~ 1.0, 1.0 means perfect coverage
    """
    try:
        pitch_range = profile.get("pitch_range", {})
        user_low = note_to_semitone(pitch_range.get("low", "C3"))
        user_high = note_to_semitone(pitch_range.get("high", "C4"))

        key_range = direction.get("key_range", {})
        dir_low = note_to_semitone(key_range.get("low", "C3"))
        dir_high = note_to_semitone(key_range.get("high", "C4"))
    except (ValueError, TypeError) as exc:
        logger.debug("Pitch parsing failed, returning to default score 0.5: %s", exc)
        return 0.5

    # Direction interval size (to avoid division by zero)
    dir_range = dir_high - dir_low
    if dir_range <= 0:
        return 0.5

    # Calculate intersection
    overlap_low = max(user_low, dir_low)
    overlap_high = min(user_high, dir_high)
    overlap = max(0, overlap_high - overlap_low)

    score = overlap / dir_range

    # Limit to [0.0, 1.0]
    return max(0.0, min(1.0, score))


def score_timbre(profile: dict, direction: dict) -> float:
    """
    Calculate the matching degree between the user's timbre parameters and the direction preference interval.

    Algorithm logic:
        Calculate the three dimensions of warmth, brightness, and breathiness respectively:
        1. If the user value falls within the direction preference interval [low, high] → this dimension gets 1.0
        2. If it is outside the interval → linearly attenuates according to the deviation distance, the score is 0.0 when the furthest deviation is 0.5
        3. The average of the three dimensions is taken as the final timbre score.

    Attenuation formula (outside the interval):
        distance = min(|value - low|, |value - high|) # Get the distance to the nearest boundary
        sub_score = max(0, 1.0 - distance / 0.5)

    Args:
        profile: user portrait, must include profile["timbre"]["warmth/brightness/breathiness"]
        direction: direction dictionary, which must contain direction["timbre_affinity"]

    Returns:
        Floating point number from 0.0 ~ 1.0
    """
    timbre = profile.get("timbre", {})
    affinity = direction.get("timbre_affinity", {})

    dimensions = ["warmth", "brightness", "breathiness"]
    scores: list[float] = []

    for dim in dimensions:
        value = timbre.get(dim, 0.5) # Default is the middle value
        dim_range = affinity.get(dim, {})
        low = dim_range.get("low", 0.0)
        high = dim_range.get("high", 1.0)

        if low <= value <= high:
            # The user value falls within the preference range, full score
            scores.append(1.0)
        else:
            # Calculate the distance to the nearest boundary, linear attenuation
            distance = min(abs(value - low), abs(value - high))
            # Maximum tolerated deviation is 0.5, if exceeded, 0 points will be awarded
            sub_score = max(0.0, 1.0 - distance / 0.5)
            scores.append(sub_score)

    if not scores:
        return 0.5

    result = sum(scores) / len(scores)
    return max(0.0, min(1.0, result))


def score_mood(profile: dict, direction: dict) -> float:
    """
    Calculate the matching degree between the user's emotion vector and the directional emotion portrait.

    Algorithm logic:
        1. For the three dimensions of valence, energy, and tension:
           - Take the center point of the direction emotion range as the target value
           - Calculate the difference between the user value and the center point
        2. Use Euclidean distance to measure the overall deviation
        3. Map the distance to the score of [0, 1]. The score is 0 when the maximum distance sqrt(3) ≈ 1.73

    Distance formula:
        center_i = (low_i + high_i) / 2
        distance = sqrt(sum((user_i - center_i)^2))
        score = max(0, 1 - distance / max_distance)

    where max_distance = sqrt(3) ≈ 1.732 (diagonal length of three-dimensional unit space)

    Args:
        profile: user portrait, must include profile["mood"]["valence/energy/tension"]
        direction: direction dictionary, which must contain direction["mood_affinity"]

    Returns:
        Floating point number from 0.0 to 1.0, 1.0 indicates a perfect emotional match
    """
    mood = profile.get("mood", {})
    affinity = direction.get("mood_affinity", {})

    dimensions = ["valence", "energy", "tension"]
    squared_diffs: list[float] = []

    for dim in dimensions:
        user_val = mood.get(dim, 0.5)
        dim_range = affinity.get(dim, {})
        low = dim_range.get("low", 0.0)
        high = dim_range.get("high", 1.0)

        # If the user value is within the interval, the difference is 0; otherwise, the distance to the nearest boundary is taken
        if low <= user_val <= high:
            squared_diffs.append(0.0)
        else:
            dist = min(abs(user_val - low), abs(user_val - high))
            squared_diffs.append(dist ** 2)

    # Euclidean distance
    distance = math.sqrt(sum(squared_diffs))

    # Maximum possible distance: Maximum deviation in each dimension 1.0 → sqrt(3) ≈ 1.732
    max_distance = math.sqrt(len(dimensions))
    score = max(0.0, 1.0 - distance / max_distance)

    return max(0.0, min(1.0, score))


def score_rhythm(profile: dict, direction: dict) -> float:
    """
    Calculate the matching degree between the user's rhythm characteristics and the directional rhythm requirements.

    Algorithm logic:
        Combining the two sub-dimensions, each accounting for 50%:

        (a) Tempo matching (tempo_score):
            - If user tempo falls within [low, high] interval of direction → 1.0
            - If outside the range → linear decay based on the deviated BPM number
            - Maximum tolerated deviation is 40 BPM, beyond which tempo_score = 0

        (b) Rhythm stability matching (stability_score):
            - if user stability >= stability_min → 1.0 in direction
            - Otherwise, linear attenuation according to the difference, with a maximum tolerance of 0.5

    Args:
        profile: user portrait, must include profile["rhythm"]["tempo", "stability"]
        direction: direction dictionary, which must contain direction["tempo_range"] and
                   direction["rhythm_requirements"]["stability_min"]

    Returns:
        Floating point number from 0.0 ~ 1.0
    """
    rhythm = profile.get("rhythm", {})
    user_tempo = rhythm.get("tempo", 100)
    user_stability = rhythm.get("stability", 0.5)

    # --- Beat tempo matching ---
    tempo_range = direction.get("tempo_range", {})
    tempo_low = tempo_range.get("low", 60)
    tempo_high = tempo_range.get("high", 180)

    if tempo_low <= user_tempo <= tempo_high:
        tempo_score = 1.0
    else:
        # Distance to the nearest boundary
        distance = min(abs(user_tempo - tempo_low), abs(user_tempo - tempo_high))
        # Maximum tolerance deviation 40 BPM
        tempo_score = max(0.0, 1.0 - distance / 40.0)

    # --- Rhythm stability matching ---
    rhythm_req = direction.get("rhythm_requirements", {})
    stability_min = rhythm_req.get("stability_min", 0.0)

    if user_stability >= stability_min:
        stability_score = 1.0
    else:
        gap = stability_min - user_stability
        # Maximum tolerance deviation 0.5
        stability_score = max(0.0, 1.0 - gap / 0.5)

    # Each of the two sub-dimensions accounts for 50%
    score = 0.5 * tempo_score + 0.5 * stability_score
    return max(0.0, min(1.0, score))


def score_expression(profile: dict, direction: dict) -> float:
    """
    Calculate the matching degree of user expressiveness characteristics and direction requirements.

    Algorithm logic:
        1. Get the set of expressive characteristics owned by the user (user_traits)
        2. Set of expressive features required for taking directions (dir_traits)
        3. Calculate the proportion of intersection to direction requirements

    Calculation formula:
        score = |user_traits ∩ dir_traits| / |dir_traits|

    Special circumstances:
        - Direction does not require any features → returns 1.0 (no threshold)
        - user characteristics is empty → return 0.0

    Args:
        profile: user portrait, must include profile["expression_traits"] (list[str])
        direction: direction dictionary, must contain direction["expression_traits"] (list[str])

    Returns:
        Floating point number from 0.0 ~ 1.0
    """
    user_traits = set(profile.get("expression_traits", []))
    dir_traits = set(direction.get("expression_traits", []))

    if not dir_traits:
        # The direction has no feature requirements and is considered to have no threshold.
        return 1.0

    if not user_traits:
        return 0.0

    intersection = user_traits & dir_traits
    score = len(intersection) / len(dir_traits)

    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Confidence and explanation generation
# ---------------------------------------------------------------------------

def _assign_confidence(score: float) -> str:
    """
    Assign a confidence level based on the composite score.

    Grading rules:
        - score > 0.75 → "high" Highly recommended, excellent matching
        - score > 0.55 → "medium" Moderately recommended, with a certain degree of agreement
        - else → "exploratory" exploratory recommendation, you can try new styles

    Args:
        score: comprehensive matching score (0.0 ~ 1.0)

    Returns:
        Confidence string: "high" | "medium" | "exploratory"
    """
    if score > 0.75:
        return "high"
    elif score > 0.55:
        return "medium"
    else:
        return "exploratory"


def _get_mood_label(mood: dict) -> str:
    """
    Generate short emotion labels based on emotion vectors for template filling.

    Strategy:
        Find the dimension with the highest value in valence / energy / tension,
        Map to the corresponding emotion descriptor.

    Args:
        mood: mood dictionary, including valence, energy, tension

    Returns:
        Emotional descriptors such as "uplifting", "energetic", "intense"
    """
    valence = mood.get("valence", 0.5)
    energy = mood.get("energy", 0.5)
    tension = mood.get("tension", 0.5)

    # Select labels based on dominant dimensions
    labels = {
        "valence": "uplifting" if valence > 0.5 else "melancholic",
        "energy": "energetic" if energy > 0.5 else "gentle",
        "tension": "intense" if tension > 0.5 else "relaxed",
    }

    # Select the dimension with the highest value as the dominant emotion
    dominant = max(
        [("valence", valence), ("energy", energy), ("tension", tension)],
        key=lambda x: x[1],
    )
    return labels[dominant[0]]


def _generate_explanation(profile: dict, direction: dict) -> str:
    """
    Generate personalized recommendation explanations using template strings from the knowledge base.

    Template variable substitution rules:
        {pitch_low} → User range lower limit note name
        {pitch_high} → Note name of the upper limit of user range
        {warmth} → user warmth (float, formatted as percentage using :.0%)
        {brightness} → user brightness (float)
        {breathiness} → user's breath (float)
        {tempo_low} → directional speed lower limit
        {tempo_high} → directional speed upper limit
        {mood_label} → Mood descriptor generated by _get_mood_label

    Args:
        profile: User vocal portrait
        direction: direction dictionary (including explanation_templates)

    Returns:
        Formatted explanation string; returns direction description when template is missing
    """
    templates = direction.get("explanation_templates", [])
    if not templates:
        return direction.get("description", "")

    # Prepare template variables
    pitch_range = profile.get("pitch_range", {})
    timbre = profile.get("timbre", {})
    mood = profile.get("mood", {})
    tempo_range = direction.get("tempo_range", {})

    template_vars: dict[str, Any] = {
        "pitch_low": pitch_range.get("low", "N/A"),
        "pitch_high": pitch_range.get("high", "N/A"),
        "warmth": timbre.get("warmth", 0.5),
        "brightness": timbre.get("brightness", 0.5),
        "breathiness": timbre.get("breathiness", 0.5),
        "tempo_low": tempo_range.get("low", "?"),
        "tempo_high": tempo_range.get("high", "?"),
        "mood_label": _get_mood_label(mood),
    }

    # Select the first template for rendering (can be expanded to random selection or multi-template splicing)
    template = templates[0]
    try:
        return template.format(**template_vars)
    except (KeyError, ValueError, IndexError) as exc:
        logger.debug("Template rendering failed (%s), falling back to description: %s", template, exc)
        return direction.get("description", "")


# ---------------------------------------------------------------------------
# Main entry function
# ---------------------------------------------------------------------------

def get_recommendations(profile: dict) -> list[dict]:
    """
    Based on the user's vocal profile, the most appropriate song direction is matched from the knowledge base.

    Complete process:
        1. Load the knowledge base (with memory cache, O(1) after first load)
        2. For each active direction, calculate the weighted comprehensive score of 5 dimensions:
           pitch(30%) + timbre(25%) + mood(20%) + rhythm(15%) + expression(10%)
        3. Sort by overall score in descending order
        4. Take top 3~8 items (at least 3 items, at most 8 items)
        5. Attach a confidence level and personalized explanation to each recommendation

    Input format (profile):
        {
            "pitch_range": {"low": "C3", "high": "G4"},
            "timbre": {"warmth": 0.7, "brightness": 0.4, "breathiness": 0.5},
            "mood": {"valence": 0.3, "energy": 0.2, "tension": 0.5},
            "rhythm": {"tempo": 78, "stability": 0.6},
            "expression_traits": ["vibrato", "legato"]
        }

    Output format (list[dict]):
        [
            {
                "direction_id": "classic_ballad",
                "genre": "Ballad",
                "sub_style": "Classic Ballad",
                "score": 0.82,
                "confidence": "high",
                "explanation": "Your warm timbre (warmth: 70%) and ...",
                "description": "Emotional, slow-tempo songs ...",
                "example_songs": ["Someone Like You – Adele", ...],
                "score_breakdown": {
                    "pitch_overlap": 0.75,
                    "timbre": 0.90,
                    "mood": 0.85,
                    "rhythm": 0.80,
                    "expression": 0.67,
                }
            },
            ...
        ]

    Exception handling:
        - The knowledge base file does not exist → returns an empty list
        - There is an error in scoring a single direction → skip this direction and record a warning
        - profile field is missing → default values ​​are used internally in each sub-scoring function

    Args:
        profile: Dictionary of user vocal characteristics portrait

    Returns:
        List of recommended results, sorted in descending order by matching score, length 3~8
    """
    directions = _load_knowledge_base()
    if not directions:
        logger.warning("The knowledge base is empty and recommendations cannot be generated")
        return []

    scored_results: list[dict] = []

    for direction in directions:
        try:
            # Calculate sub-scores in 5 dimensions
            pitch_score = score_pitch_overlap(profile, direction)
            timbre_score = score_timbre(profile, direction)
            mood_score = score_mood(profile, direction)
            rhythm_score = score_rhythm(profile, direction)
            expression_score = score_expression(profile, direction)

            # Weighted overall score
            total = (
                WEIGHT_PITCH * pitch_score
                + WEIGHT_TIMBRE * timbre_score
                + WEIGHT_MOOD * mood_score
                + WEIGHT_RHYTHM * rhythm_score
                + WEIGHT_EXPRESSION * expression_score
            )
            # Make sure the overall score is in [0.0, 1.0]
            total = max(0.0, min(1.0, total))

            scored_results.append({
                "direction_id": direction.get("id", "unknown"),
                "genre": direction.get("genre", ""),
                "sub_style": direction.get("sub_style", ""),
                "score": round(total, 4),
                "confidence": _assign_confidence(total),
                "explanation": _generate_explanation(profile, direction),
                "description": direction.get("description", ""),
                "example_songs": direction.get("example_songs", []),
                "score_breakdown": {
                    "pitch_overlap": round(pitch_score, 4),
                    "timbre": round(timbre_score, 4),
                    "mood": round(mood_score, 4),
                    "rhythm": round(rhythm_score, 4),
                    "expression": round(expression_score, 4),
                },
            })
        except Exception as exc:
            # Failure to score in a single direction should not interrupt the overall recommendation process
            logger.warning(
                "Scoring failed for direction '%s', skipped: %s",
                direction.get("id", "unknown"),
                exc,
            )
            continue

    # Sort by overall score in descending order
    scored_results.sort(key=lambda r: r["score"], reverse=True)

    # Take top 3~8 items
    # Rules: Return at least 3 items (if the total is less than 3, return all), and at most 8 items
    count = max(MIN_RECOMMENDATIONS, min(MAX_RECOMMENDATIONS, len(scored_results)))
    return scored_results[:count]
