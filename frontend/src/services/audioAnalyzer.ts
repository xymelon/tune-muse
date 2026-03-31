/**
 * Audio feature extraction service: uses Meyda.js and pitchfinder to extract features from AudioBuffer.
 *
 * Extracted features include:
 * - MFCC (13 coefficients): Mel-frequency cepstral coefficients, describing timbre
 * - Spectral features: centroid, flatness, rolloff frequency, zero crossing rate
 * - RMS energy: loudness indicator
 * - Chroma features: energy distribution across 12 pitch classes
 * - Fundamental frequency (F0): pitch detection using YIN algorithm
 * - Rhythm features: BPM and rhythm regularity estimated from energy envelope
 */

import Meyda from 'meyda'
import { YIN } from 'pitchfinder'
import type { AudioFeatures } from '../types'

/** Meyda analysis frame size (number of samples) */
const FRAME_SIZE = 2048
/** Frame hop size */
const HOP_SIZE = 512

/**
 * Calculate the mean of an array.
 */
function mean(arr: number[]): number {
  if (arr.length === 0) return 0
  return arr.reduce((a, b) => a + b, 0) / arr.length
}

/**
 * Calculate the standard deviation of an array.
 */
function std(arr: number[]): number {
  if (arr.length < 2) return 0
  const m = mean(arr)
  const variance = arr.reduce((sum, x) => sum + (x - m) ** 2, 0) / arr.length
  return Math.sqrt(variance)
}

/**
 * Calculate the median of an array.
 */
function median(arr: number[]): number {
  if (arr.length === 0) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
}

/**
 * Calculate a quantile of an array.
 */
function quantile(arr: number[], q: number): number {
  if (arr.length === 0) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const pos = (sorted.length - 1) * q
  const base = Math.floor(pos)
  const rest = pos - base
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base])
  }
  return sorted[base]
}

/**
 * Extract a complete audio feature vector from an AudioBuffer.
 *
 * Uses Meyda.js to extract spectral features and MFCC frame by frame, and
 * pitchfinder's YIN algorithm to detect fundamental frequency (pitch) per frame.
 * All frame-level features are aggregated into statistical summaries (mean, std).
 *
 * @param audioBuffer - Web Audio API AudioBuffer object
 * @returns Extracted AudioFeatures object, ready to submit to the backend /analyze endpoint
 *
 * @example
 *   const audioCtx = new AudioContext()
 *   const buffer = await audioCtx.decodeAudioData(arrayBuffer)
 *   const features = analyzeAudio(buffer)
 *   // features.mfcc_mean, features.pitch_min_hz, etc.
 */
export function analyzeAudio(audioBuffer: AudioBuffer): AudioFeatures {
  const sampleRate = audioBuffer.sampleRate
  const channelData = audioBuffer.getChannelData(0) // Use the first channel

  // Initialize pitchfinder YIN algorithm
  const detectPitch = YIN({ sampleRate })

  // Frame-level feature collectors
  const allMfcc: number[][] = []
  const allCentroid: number[] = []
  const allFlatness: number[] = []
  const allRolloff: number[] = []
  const allZcr: number[] = []
  const allRms: number[] = []
  const allChroma: number[][] = []
  const allPitches: number[] = []

  // Frame-by-frame analysis
  const totalFrames = Math.floor((channelData.length - FRAME_SIZE) / HOP_SIZE)
  for (let i = 0; i < totalFrames; i++) {
    const start = i * HOP_SIZE
    const frame = channelData.slice(start, start + FRAME_SIZE)

    // Extract spectral features using Meyda
    // Meyda.extract accepts a feature name array and a signal array
    const meydaFeatures = Meyda.extract(
      ['mfcc', 'spectralCentroid', 'spectralFlatness', 'spectralRolloff', 'zcr', 'rms', 'chroma'],
      frame,
    )

    if (meydaFeatures) {
      if (meydaFeatures.mfcc) allMfcc.push(meydaFeatures.mfcc as number[])
      if (typeof meydaFeatures.spectralCentroid === 'number')
        allCentroid.push(meydaFeatures.spectralCentroid)
      if (typeof meydaFeatures.spectralFlatness === 'number')
        allFlatness.push(meydaFeatures.spectralFlatness)
      if (typeof meydaFeatures.spectralRolloff === 'number')
        allRolloff.push(meydaFeatures.spectralRolloff)
      if (typeof meydaFeatures.zcr === 'number') allZcr.push(meydaFeatures.zcr)
      if (typeof meydaFeatures.rms === 'number') allRms.push(meydaFeatures.rms)
      if (meydaFeatures.chroma) allChroma.push(meydaFeatures.chroma as number[])
    }

    // Detect pitch using pitchfinder
    const pitch = detectPitch(frame as unknown as Float32Array)
    if (pitch !== null && pitch > 50 && pitch < 2000) {
      allPitches.push(pitch)
    }
  }

  // Aggregate MFCC (mean and std of 13 coefficients)
  const numCoeffs = allMfcc.length > 0 ? allMfcc[0].length : 13
  const mfccMean: number[] = []
  const mfccStd: number[] = []
  for (let c = 0; c < numCoeffs; c++) {
    const coeffValues = allMfcc.map((frame) => frame[c] || 0)
    mfccMean.push(mean(coeffValues))
    mfccStd.push(std(coeffValues))
  }

  // Aggregate chroma features
  const numPitchClasses = allChroma.length > 0 ? allChroma[0].length : 12
  const chromaMean: number[] = []
  for (let c = 0; c < numPitchClasses; c++) {
    const values = allChroma.map((frame) => frame[c] || 0)
    chromaMean.push(mean(values))
  }

  // Pitch statistics
  const pitchMinHz = allPitches.length > 0 ? Math.min(...allPitches) : 0
  const pitchMaxHz = allPitches.length > 0 ? Math.max(...allPitches) : 0
  const pitchMedianHz = median(allPitches)

  // Pitch stability: derived from coefficient of variation of pitch sequence (lower = more stable)
  const pitchStd = std(allPitches)
  const pitchMean = mean(allPitches)
  const pitchStability =
    pitchMean > 0 ? Math.max(0, Math.min(1, 1 - pitchStd / pitchMean)) : 0

  // Tempo estimation: derived from autocorrelation of RMS energy envelope
  let tempoBpm: number | null = null
  let rhythmRegularity = 0.5

  if (allRms.length > 10) {
    // Simplified onset detection: find peaks in RMS energy
    const onsetTimes: number[] = []
    const rmsThreshold = mean(allRms) * 1.3
    for (let i = 1; i < allRms.length - 1; i++) {
      if (allRms[i] > rmsThreshold && allRms[i] > allRms[i - 1] && allRms[i] >= allRms[i + 1]) {
        onsetTimes.push((i * HOP_SIZE) / sampleRate)
      }
    }

    if (onsetTimes.length >= 3) {
      // Compute inter-onset intervals
      const intervals: number[] = []
      for (let i = 1; i < onsetTimes.length; i++) {
        intervals.push(onsetTimes[i] - onsetTimes[i - 1])
      }

      const meanInterval = mean(intervals)
      if (meanInterval > 0.2 && meanInterval < 2.0) {
        tempoBpm = 60 / meanInterval
        // Rhythm regularity: lower coefficient of variation of intervals = more regular
        const intervalCv = std(intervals) / meanInterval
        rhythmRegularity = Math.max(0, Math.min(1, 1 - intervalCv))
      }
    }
  }

  // Signal quality score
  const rmsMean = mean(allRms)
  const flatnessMean = mean(allFlatness)
  // Too quiet (rmsMean < 0.005) or too noisy (flatness > 0.8) lowers the quality score
  let signalQuality = 1.0
  if (rmsMean < 0.005) signalQuality -= 0.5
  else if (rmsMean < 0.015) signalQuality -= 0.2
  if (flatnessMean > 0.8) signalQuality -= 0.4
  else if (flatnessMean > 0.5) signalQuality -= 0.1
  if (allPitches.length < 5) signalQuality -= 0.3
  signalQuality = Math.max(0, Math.min(1, signalQuality))

  return {
    mfcc_mean: mfccMean,
    mfcc_std: mfccStd,
    pitch_min_hz: pitchMinHz,
    pitch_max_hz: pitchMaxHz,
    pitch_median_hz: pitchMedianHz,
    pitch_stability: pitchStability,
    pitch_contour_stats: {
      mean: pitchMean,
      std: pitchStd,
      quartile_25: quantile(allPitches, 0.25),
      quartile_75: quantile(allPitches, 0.75),
    },
    tempo_bpm: tempoBpm,
    rhythm_regularity: rhythmRegularity,
    spectral_centroid_mean: mean(allCentroid),
    spectral_centroid_std: std(allCentroid),
    spectral_flatness_mean: flatnessMean,
    spectral_rolloff_mean: mean(allRolloff),
    zero_crossing_rate_mean: mean(allZcr),
    rms_mean: rmsMean,
    rms_std: std(allRms),
    chroma_mean: chromaMean,
    signal_quality_score: signalQuality,
  }
}
