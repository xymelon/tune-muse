/**
 * Signal quality check service.
 * Evaluates whether audio features meet the minimum requirements for reliable analysis.
 * Checks: volume too low, noise too high, sufficient pitch variation, voice detected.
 */

import type { AudioFeatures, QualityResult } from '../types'

/**
 * Check whether the extracted audio features meet the minimum signal quality required for analysis.
 *
 * Performs four checks, any failure will generate a user-friendly advice message:
 * 1. Volume check (RMS too low = recording too quiet)
 * 2. Noise check (spectrum flatness is too high = background noise is large)
 * 3. Pitch change check (too narrow range = lack of melody change)
 * 4. Vocal detection (no valid pitch = no singing voice detected)
 *
 * @param features - audio features extracted from audioAnalyzer
 * @returns Quality check results: passed or failed, problem list, overall quality score
 *
 * @example
 *   const features = analyzeAudio(audioBuffer)
 *   const quality = checkQuality(features)
 *   if (!quality.passed) {
 * showError(quality.issues[0]) // Show the first issue
 *   }
 */
export function checkQuality(features: AudioFeatures): QualityResult {
  const issues: string[] = []

  // Check 1: Volume too low
  if (features.rms_mean < 0.005) {
    issues.push(
      'Recording is too quiet. Please sing louder or move closer to the microphone.',
    )
  }

  // Check 2: Background noise is too high
  if (features.spectral_flatness_mean > 0.8) {
    issues.push(
      'Too much background noise detected. Please record in a quieter environment.',
    )
  }

  // Check 3: No vocal detected (no valid pitch)
  if (features.pitch_min_hz === 0 && features.pitch_max_hz === 0) {
    issues.push(
      'No singing voice detected. Please make sure you are singing, not speaking.',
    )
  }
  // Check 4: Insufficient pitch variation
  else if (features.pitch_max_hz - features.pitch_min_hz < 20) {
    issues.push(
      'Not enough vocal variation detected. Please sing a melody with some pitch changes.',
    )
  }

  return {
    passed: issues.length === 0,
    issues,
    score: features.signal_quality_score,
  }
}
