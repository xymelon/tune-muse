"""
LLM client service: uses Anthropic Python SDK (Claude Sonnet) for intelligent recommendation refinement.

This module encapsulates the interaction logic with Claude API and receives candidate recommendations from Vocal profile and rule engine.
Reorder and generate natural language explanations via LLM. The design adopts an elegant downgrade strategy——
When the LLM call fails (timeout, API error, parsing error), the original candidate result is returned directly.
Ensure that the referral process is not interrupted due to LLM unavailability.

How to use:
    from app.services.llm_client import refine_recommendations

    refined = await refine_recommendations(vocal_profile, candidates)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger("tunemuse.llm_client")

# Claude Sonnet model identifier
MODEL_ID = "claude-sonnet-4-20250514"

# LLM call timeout (seconds)
LLM_TIMEOUT_SECONDS = 10.0

# Recommended quantity range returned by LLM
MIN_RECOMMENDATIONS = 5
MAX_RECOMMENDATIONS = 8


def _build_system_prompt() -> str:
    """
    Build system prompt words to guide Claude as a music recommendation expert.

    Returns:
        System prompt word string, which defines Claude's role and output format requirements
    """
    return (
        "You are a professional music recommendation expert. Your task is based on the user's Vocal profile (VocalProfile)"
        "and a candidate recommendation list, intelligently reorder the recommendation results, and generate a natural language explanation for each recommendation.\n\n"
        "You must return strictly JSON format, without any markdown code block tags or extra text."
    )


def _format_vocal_profile(profile: dict) -> str:
    """
    Format the Vocal profile dictionary into a structured text description for easy understanding by LLM.

    Args:
        profile: Vocal profile dictionary, including pitch, rhythm, mood, timbre, expression and other sub-items.
                 Can be a nested dictionary (from VocalProfileResponse) or a flat dictionary (from database).

    Returns:
        Formatted Vocal profile text description

    Example:
        profile = {
            "pitch": {"range_min_hz": 130, "range_max_hz": 520, ...},
            "mood": {"primary_mood": "melancholic", "valence": 0.3, ...},
            ...
        }
        text = _format_vocal_profile(profile)
    """
    lines = ["=== Vocal profile (Vocal Profile) ==="]

    # Supports nested structures (from VocalProfileResponse) and flat structures (from database rows)
    if "pitch" in profile and isinstance(profile["pitch"], dict):
        # Nested format
        pitch = profile["pitch"]
        lines.append(f"[pitch] range: {pitch.get('range_min_hz', '?')}Hz - "
                     f"{pitch.get('range_max_hz', '?')}Hz, "
                     f"Classification: {pitch.get('vocal_classification', '?')}, "
                     f"Stability: {pitch.get('stability_score', '?')}")

        rhythm = profile.get("rhythm", {})
        lines.append(f"[Rhythm] BPM: {rhythm.get('tempo_bpm', '?')}, "
                     f"beat accuracy: {rhythm.get('timing_accuracy', '?')}")

        mood = profile.get("mood", {})
        lines.append(f"[mood] Primary mood: {mood.get('primary_mood', '?')}, "
                     f"Valence: {mood.get('valence', '?')}, "
                     f"Energy: {mood.get('energy', '?')}")

        timbre = profile.get("timbre", {})
        lines.append(f"[timbre] brightness: {timbre.get('brightness', '?')}, "
                     f"Warmth: {timbre.get('warmth', '?')}, "
                     f"Breathiness: {timbre.get('breathiness', '?')}")

        expression = profile.get("expression", {})
        lines.append(f"[Expressiveness] vibrato: {expression.get('vibrato_extent', '?')}, "
                     f"Dynamic range: {expression.get('dynamic_range', '?')}, "
                     f"Expressiveness: {expression.get('expressiveness', '?')}")
    else:
        # Flat format (database rows)
        lines.append(f"[pitch] range: {profile.get('pitch_min_hz', '?')}Hz - "
                     f"{profile.get('pitch_max_hz', '?')}Hz, "
                     f"Stability: {profile.get('pitch_stability', '?')}")
        lines.append(f"[Mood] {profile.get('mood_label', '?')}, "
                     f"Valence: {profile.get('mood_valence', '?')}, "
                     f"Energy: {profile.get('mood_energy', '?')}")
        lines.append(f"[timbre] {profile.get('timbre_label', '?')}, "
                     f"Brightness: {profile.get('timbre_brightness', '?')}, "
                     f"Warmth: {profile.get('timbre_warmth', '?')}")
        lines.append(f"[expression] vibrato: {profile.get('expression_vibrato', '?')}, "
                     f"Dynamic range: {profile.get('expression_dynamic_range', '?')}")

    return "\n".join(lines)


def _format_candidates(candidates: list[dict]) -> str:
    """
    Format candidate recommendation lists as numbered text for easy LLM reference and citation.

    Args:
        candidates: candidate recommendation list output by the rule engine, each candidate contains
                    Fields such as genre, match_score, confidence, match_explanation, etc.

    Returns:
        Formatted candidate list text
    """
    lines = ["=== Candidate recommendation list ==="]
    for i, c in enumerate(candidates, 1):
        lines.append(
            f"{i}. Genre: {c.get('genre', '?')} | "
            f"Match score: {c.get('match_score', '?')} | "
            f"Confidence: {c.get('confidence', '?')} | "
            f"BPM Range: {c.get('tempo_range_low', '?')}-{c.get('tempo_range_high', '?')} | "
            f"Difficulty: {c.get('vocal_difficulty', '?')}/5 | "
            f"Explanation: {c.get('match_explanation', c.get('mood_alignment', '?'))}"
        )
    return "\n".join(lines)


def _build_user_prompt(profile: dict, candidates: list[dict]) -> str:
    """
    Construct user prompt words, including Vocal profile and candidate list, as well as output format requirements.

    Args:
        profile: Vocal profile dictionary
        candidates: candidate recommendation list

    Returns:
        Complete user prompt word string
    """
    profile_text = _format_vocal_profile(profile)
    candidates_text = _format_candidates(candidates)

    return (
        f"{profile_text}\n\n"
        f"{candidates_text}\n\n"
        "Please reorder the candidate recommendations based on the above Vocal profile and select the best 5-8 recommendations.\n"
        "For each recommendation, please:\n"
        "1. Recalculate match_score (0.0-1.0) according to the feature matching degree of Vocal profile\n"
        "2. To generate a natural language match_explanation, you need to specifically reference the features in the Vocal profile"
        "(eg "Your voice has high warmth (0.8), which is very suitable for...")\n"
        "3. Evaluate confidence level: high / medium / exploratory\n\n"
        "Return strictly in the following JSON format (do not include markdown tags):\n"
        "[\n"
        '  {\n'
        ' "genre": "Genre name",\n'
        ' "sub_style": "Sub style (optional)",\n'
        '    "match_score": 0.85,\n'
        '    "confidence": "high",\n'
        ' "match_explanation": "A detailed explanation based on the characteristics of your voice...",\n'
        '    "tempo_range_low": 80,\n'
        '    "tempo_range_high": 120,\n'
        '    "vocal_difficulty": 3,\n'
        '    "mood_alignment": "Mood alignment description"\n'
        "  }\n"
        "]"
    )


def _parse_llm_response(response_text: str) -> list[dict] | None:
    """
    Parse the JSON text returned by LLM into a list of recommendations.

    Support for handling markdown code block tags that may be added by LLM.
    When parsing fails, None is returned instead of throwing an exception, which facilitates downgrade processing by the caller.

    Args:
        response_text: the original text returned by LLM

    Returns:
        The parsed recommended dictionary list, returns None if the parsing fails.
    """
    text = response_text.strip()

    # Remove possible markdown code block tags
    if text.startswith("```"):
        # Find the content after the first newline
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Parsing of JSON returned by LLM failed: %s", exc)
        return None

    # Verify that the returned list contains a reasonable number of recommendations
    if not isinstance(parsed, list) or len(parsed) == 0:
        logger.warning("The data format returned by LLM is not as expected (not a list or empty)")
        return None

    return parsed


async def refine_recommendations(
    profile: dict,
    candidates: list[dict],
) -> list[dict]:
    """
    Use Claude Sonnet to intelligently refine candidate recommendations from the rule engine.

    Workflow:
    1. Check whether the API key is configured. If not configured, return the original candidate directly.
    2. Format Vocal profile and candidate list into prompt words
    3. Call Claude API for reordering and interpretation generation
    4. Parse the JSON results returned by LLM
    5. Gracefully degrade when any link fails and return to the original candidate.

    Args:
        profile: Vocal profile dictionary, which can be a nested structure (VocalProfileResponse.model_dump())
                 or flat structure (database query results).
                 Nested example: {"pitch": {"range_min_hz": 130, ...}, "mood": {...}, ...}
                 Flat example: {"pitch_min_hz": 130, "mood_label": "joyful", ...}
        candidates: candidate recommendation list output by the rule engine, each candidate is a dictionary,
                    Contains genre, match_score, confidence, match_explanation and other fields

    Returns:
        Refined recommendation list (when LLM is successful) or original candidate list (when downgraded).
        Each recommended dictionary contains:
        - genre: genre name
        - sub_style: sub style (optional)
        - match_score: match score (0.0-1.0)
        - confidence: confidence level (high/medium/exploratory)
        - match_explanation: natural language explanation
        - tempo_range_low / tempo_range_high: BPM Range
        - vocal_difficulty: singing difficulty (1-5)
        - mood_alignment: Mood alignment description

    Example:
        profile = {
            "pitch": {"range_min_hz": 130, "range_max_hz": 520,
                      "vocal_classification": "tenor", "stability_score": 0.75},
            "mood": {"primary_mood": "melancholic", "valence": 0.3, "energy": 0.4},
            "timbre": {"brightness": 0.6, "warmth": 0.8, "breathiness": 0.3},
            ...
        }
        candidates = [
            {"genre": "R&B", "match_score": 0.82, "confidence": "high", ...},
            {"genre": "Jazz", "match_score": 0.75, "confidence": "medium", ...},
        ]
        refined = await refine_recommendations(profile, candidates)
    """
    # ── Guard condition: skip LLM call when API key is not configured ──
    if not settings.anthropic_api_key:
        logger.info("Anthropic API key is not configured, skip LLM refinement, return original candidate")
        return candidates

    # ── Guard condition: No need to call LLM when the candidate list is empty ──
    if not candidates:
        logger.info("The candidate recommendation list is empty, skip LLM fine ranking")
        return candidates

    # ── Build prompt words ──
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(profile, candidates)

    #──Call Claude API──
    try:
        client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=LLM_TIMEOUT_SECONDS,
        )

        logger.info("Calling Claude Sonnet for recommendation refinement (number of candidates: %d)...", len(candidates))

        message = await client.messages.create(
            model=MODEL_ID,
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        # Extract text response
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        logger.info(
            "Claude response completed (token usage: input=%d, output=%d)",
            message.usage.input_tokens,
            message.usage.output_tokens,
        )

    except anthropic.APITimeoutError:
        logger.warning("Claude API call timed out (>%.0fs), downgraded to return to original candidate", LLM_TIMEOUT_SECONDS)
        return candidates
    except anthropic.APIError as exc:
        logger.warning("Claude API call failed: %s, downgraded to original candidate", exc)
        return candidates
    except Exception as exc:
        #Catch all unexpected exceptions to ensure that the recommendation process is not interrupted
        logger.error("Unexpected error in LLM call: %s, downgrade to return to original candidate", exc, exc_info=True)
        return candidates

    # ── Parse LLM response ──
    refined = _parse_llm_response(response_text)
    if refined is None:
        logger.warning("LLM response parsing failed, downgraded to return to original candidate")
        return candidates

    # ── Limit the returned quantity to a reasonable range ──
    if len(refined) > MAX_RECOMMENDATIONS:
        refined = refined[:MAX_RECOMMENDATIONS]

    logger.info("LLM refinement completed, %d recommendations returned", len(refined))
    return refined
