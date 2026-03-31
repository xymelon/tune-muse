"""
Vocal analyzer service: converts client-extracted audio feature vectors into structured vocal profiles.

This module receives raw feature data extracted by Meyda.js + pitchfinder (MFCC, spectral features,
fundamental frequency sequences, etc.) and generates vocal profiles across five dimensions
(pitch, rhythm, mood, timbre, expression) through a series of mapping and classification algorithms,
each dimension accompanied by natural language descriptions.
"""

from __future__ import annotations

import math

import numpy as np


# Note name lookup table: semitone -> note name
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def hz_to_note(hz: float) -> str:
    """
    Convert a frequency (Hz) to the nearest note name (e.g., "C4", "A#3").
    Based on the A4 = 440 Hz standard pitch.

    Args:
        hz: Frequency value in hertz

    Returns:
        Note name string, e.g., "C4"

    Example:
        >>> hz_to_note(261.63)
        'C4'
        >>> hz_to_note(440.0)
        'A4'
    """
    if hz <= 0:
        return "N/A"
    # Calculate semitones from A4
    semitones_from_a4 = 12 * math.log2(hz / 440.0)
    # MIDI note number (A4 = 69)
    midi_note = round(69 + semitones_from_a4)
    # Extract octave and note name
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{_NOTE_NAMES[note_index]}{octave}"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a value to the [low, high] range."""
    return max(low, min(high, value))


def _classify_timbre(features: dict) -> tuple[float, float, float, str]:
    """
    Infer timbre characteristics from spectral features: warmth, brightness, breathiness.

    Mapping logic:
    - Warmth: determined by the first MFCC coefficient (higher = warmer, indicating more low-frequency energy)
    - Brightness: determined by spectral centroid (higher = brighter, indicating more high-frequency content)
    - Breathiness: determined by spectral flatness (higher = breathier, closer to white noise characteristics)

    Args:
        features: Audio features dict

    Returns:
        (warmth, brightness, breathiness, label) tuple
    """
    mfcc_mean = features.get("mfcc_mean", [0] * 13)

    # Warmth: MFCC[0] typically ranges from -20 to +30, mapped to 0-1
    warmth_raw = mfcc_mean[0] if len(mfcc_mean) > 0 else 0
    warmth = _clamp((warmth_raw + 10) / 40)  # -10 -> 0, 30 -> 1

    # Brightness: spectral centroid typically ranges from 500-5000 Hz, mapped to 0-1
    centroid = features.get("spectral_centroid_mean", 2000)
    brightness = _clamp((centroid - 500) / 4500)

    # Breathiness: spectral flatness 0-1, used directly (slightly amplified)
    flatness = features.get("spectral_flatness_mean", 0.1)
    breathiness = _clamp(flatness * 2.5)

    # Generate label
    traits = []
    if warmth > 0.6:
        traits.append("Warm")
    elif warmth < 0.3:
        traits.append("Cool")
    if brightness > 0.6:
        traits.append("Bright")
    elif brightness < 0.3:
        traits.append("Dark")
    if breathiness > 0.5:
        traits.append("Breathy")
    elif breathiness < 0.2:
        traits.append("Clear")

    label = " & ".join(traits) if traits else "Balanced"

    return warmth, brightness, breathiness, label


def _classify_mood(features: dict) -> tuple[float, float, float, str]:
    """
    Infer mood dimensions from audio features: valence, energy, tension.

    Mapping logic:
    - Valence: inferred from chroma features (major key tendency = more positive)
    - Energy: determined by RMS mean
    - Tension: determined by pitch stability and spectral contrast

    Args:
        features: Audio features dict

    Returns:
        (valence, energy, tension, label) tuple
    """
    # Energy: RMS mean typically ranges from 0.01-0.5
    rms = features.get("rms_mean", 0.1)
    energy = _clamp(rms / 0.3)

    # Valence: use chroma features to infer tonal tendency
    # Major key chroma distribution favors notes like C, E, G
    chroma = features.get("chroma_mean", [0.5] * 12)
    if len(chroma) >= 12:
        chroma_arr = np.array(chroma[:12])
        # Simplified major/minor detection: the 3rd interval (major 3rd vs minor 3rd)
        major_energy = chroma_arr[4]  # E (major 3rd)
        minor_energy = chroma_arr[3]  # Eb (minor 3rd)
        valence = _clamp(0.5 + (major_energy - minor_energy) * 2)
    else:
        valence = 0.5

    # Tension: pitch instability + high-frequency energy = more tense
    pitch_stability = features.get("pitch_stability", 0.5)
    tension = _clamp(1.0 - pitch_stability * 0.6 + energy * 0.3)

    # Generate mood label
    if energy > 0.6 and valence > 0.6:
        label = "Upbeat & Joyful"
    elif energy > 0.6 and valence <= 0.4:
        label = "Intense & Passionate"
    elif energy <= 0.4 and valence > 0.6:
        label = "Warm & Content"
    elif energy <= 0.4 and valence <= 0.4:
        label = "Reflective & Gentle"
    elif energy > 0.5:
        label = "Energetic & Expressive"
    else:
        label = "Calm & Thoughtful"

    return valence, energy, tension, label


def _describe_expression(features: dict) -> tuple[float, float, str, str]:
    """
    Infer expression characteristics from audio features: vibrato, dynamic range, articulation.

    Mapping logic:
    - Vibrato: moderate pitch stability suggests periodic vibrato
    - Dynamic range: ratio of RMS std to mean
    - Articulation: determined by zero crossing rate (low = legato, high = staccato)

    Args:
        features: Audio features dict

    Returns:
        (vibrato, dynamic_range, articulation, description) tuple
    """
    # Vibrato detection: pitch_stability in 0.4-0.7 range suggests periodic oscillation (vibrato)
    # Too stable = no vibrato, too unstable = out of tune rather than vibrato
    pitch_stability = features.get("pitch_stability", 0.5)
    if 0.3 < pitch_stability < 0.8:
        vibrato = _clamp(1.0 - abs(pitch_stability - 0.55) * 4)
    else:
        vibrato = _clamp(0.2 if pitch_stability >= 0.8 else 0.1)

    # Dynamic range: RMS std / RMS mean (coefficient of variation)
    rms_mean = features.get("rms_mean", 0.1)
    rms_std = features.get("rms_std", 0.03)
    if rms_mean > 0.001:
        dynamic_range = _clamp((rms_std / rms_mean) * 2)
    else:
        dynamic_range = 0.0

    # Articulation: zero crossing rate reflects tonal continuity
    zcr = features.get("zero_crossing_rate_mean", 0.05)
    if zcr < 0.04:
        articulation = "legato"
    elif zcr > 0.12:
        articulation = "staccato"
    else:
        articulation = "mixed"

    # Generate description
    parts = []
    if vibrato > 0.5:
        parts.append("gentle vibrato")
    elif vibrato > 0.3:
        parts.append("subtle vibrato")
    if dynamic_range > 0.6:
        parts.append("wide dynamic variation")
    elif dynamic_range < 0.3:
        parts.append("steady volume")
    parts.append(f"{articulation} phrasing")

    description = f"You use {' and '.join(parts)} with {'expressive' if dynamic_range > 0.5 else 'moderate'} dynamic variation."

    return vibrato, dynamic_range, articulation, description


def analyze_features(features: dict) -> dict:
    """
    Convert raw audio feature vectors into a structured vocal profile.

    This is the main entry point for vocal analysis. Receives client-extracted feature data,
    and through four steps — pitch mapping, timbre classification, mood inference, and expression analysis —
    generates a complete vocal profile with five dimensions.

    Args:
        features: Audio features dict, containing mfcc_mean, pitch_min_hz,
                  pitch_max_hz, spectral_centroid_mean, and other fields
                  (see contracts/api.md for the complete field list)

    Returns:
        Vocal profile dict with the following structure:
        {
            "pitch": {"range_low": "C3", "range_high": "A4", ...},
            "rhythm": {"tempo_bpm": 92, "regularity": 0.75, ...},
            "mood": {"valence": 0.4, "energy": 0.35, ...},
            "timbre": {"warmth": 0.78, "brightness": 0.35, ...},
            "expression": {"vibrato": 0.6, "dynamic_range": 0.5, ...},
            "confidence": 0.85
        }
    """
    # === Pitch analysis ===
    pitch_min = features.get("pitch_min_hz", 0)
    pitch_max = features.get("pitch_max_hz", 0)
    pitch_median = features.get("pitch_median_hz", 0)
    pitch_stability = features.get("pitch_stability", 0.5)

    pitch_min_note = hz_to_note(pitch_min)
    pitch_max_note = hz_to_note(pitch_max)

    # Comfortable range: from 25th to 75th percentile of pitch distribution
    contour_stats = features.get("pitch_contour_stats", {})
    q25 = contour_stats.get("quartile_25", pitch_min)
    q75 = contour_stats.get("quartile_75", pitch_max)
    comfortable_zone = f"{hz_to_note(q25)}–{hz_to_note(q75)}"

    # Pitch description
    range_semitones = 0
    if pitch_min > 0 and pitch_max > 0:
        range_semitones = round(12 * math.log2(pitch_max / pitch_min))

    if range_semitones > 18:
        pitch_desc = f"Your voice spans an impressive range of about {range_semitones} semitones with {'excellent' if pitch_stability > 0.7 else 'good'} pitch control."
    elif range_semitones > 12:
        pitch_desc = f"Your voice comfortably spans about {range_semitones} semitones with {'good' if pitch_stability > 0.6 else 'moderate'} pitch control."
    else:
        pitch_desc = f"Your singing stays within a focused range of about {range_semitones} semitones, showing {'steady' if pitch_stability > 0.7 else 'developing'} pitch control."

    # === Rhythm analysis ===
    tempo = features.get("tempo_bpm")
    regularity = features.get("rhythm_regularity", 0.5)

    if tempo and tempo > 0:
        if tempo < 80:
            rhythm_desc = f"You naturally gravitate toward slower tempos around {int(tempo)} BPM with a {'steady' if regularity > 0.7 else 'relaxed'} rhythmic feel."
        elif tempo < 120:
            rhythm_desc = f"You naturally gravitate toward moderate tempos around {int(tempo)} BPM with a {'steady' if regularity > 0.7 else 'relaxed'} rhythmic feel."
        else:
            rhythm_desc = f"You gravitate toward upbeat tempos around {int(tempo)} BPM with {'strong' if regularity > 0.7 else 'spirited'} rhythmic drive."
    else:
        rhythm_desc = "Your singing follows a free, unmetered rhythmic approach."

    # === Timbre analysis ===
    warmth, brightness, breathiness, timbre_label = _classify_timbre(features)

    timbre_traits = []
    if warmth > 0.5:
        timbre_traits.append("warm")
    if breathiness > 0.4:
        timbre_traits.append("slightly breathy")
    if brightness > 0.6:
        timbre_traits.append("bright")
    timbre_desc = f"Your voice has a {', '.join(timbre_traits) if timbre_traits else 'balanced'} quality that creates {'an intimate, personal' if breathiness > 0.4 else 'a clear, resonant'} feel."

    # === Mood analysis ===
    valence, energy, tension, mood_label = _classify_mood(features)

    mood_desc_map = {
        "Upbeat & Joyful": "Your singing conveys a bright, positive energy that lifts the mood.",
        "Intense & Passionate": "Your singing conveys powerful emotional intensity and passion.",
        "Warm & Content": "Your singing conveys warmth and a sense of gentle contentment.",
        "Reflective & Gentle": "Your singing conveys a thoughtful, introspective quality with gentle emotional depth.",
        "Energetic & Expressive": "Your singing is energetic and emotionally expressive.",
        "Calm & Thoughtful": "Your singing conveys a calm, contemplative atmosphere.",
    }
    mood_desc = mood_desc_map.get(mood_label, "Your singing has a distinctive emotional character.")

    # === Expression analysis ===
    vibrato, dynamic_range, articulation, expr_desc = _describe_expression(features)

    # === Confidence calculation ===
    signal_quality = features.get("signal_quality_score", 0.5)
    # Combine signal quality and feature completeness
    has_pitch = 1.0 if pitch_min > 0 and pitch_max > 0 else 0.3
    has_spectral = 1.0 if features.get("spectral_centroid_mean", 0) > 0 else 0.5
    confidence = _clamp(signal_quality * 0.5 + has_pitch * 0.3 + has_spectral * 0.2)

    return {
        "pitch": {
            "range_low": pitch_min_note,
            "range_high": pitch_max_note,
            "comfortable_zone": comfortable_zone,
            "stability": round(pitch_stability, 2),
            "description": pitch_desc,
        },
        "rhythm": {
            "tempo_bpm": round(tempo, 1) if tempo else None,
            "regularity": round(regularity, 2),
            "description": rhythm_desc,
        },
        "mood": {
            "valence": round(valence, 2),
            "energy": round(energy, 2),
            "tension": round(tension, 2),
            "label": mood_label,
            "description": mood_desc,
        },
        "timbre": {
            "warmth": round(warmth, 2),
            "brightness": round(brightness, 2),
            "breathiness": round(breathiness, 2),
            "label": timbre_label,
            "description": timbre_desc,
        },
        "expression": {
            "vibrato": round(vibrato, 2),
            "dynamic_range": round(dynamic_range, 2),
            "articulation": articulation,
            "description": expr_desc,
        },
        "confidence": round(confidence, 2),
    }
