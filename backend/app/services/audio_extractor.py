"""
Server-side audio feature extraction service (for the file upload path).

When a user uploads an audio file instead of recording live, the server uses librosa to extract
the same feature set as client-side Meyda.js + pitchfinder. After extraction, the temporary
file is immediately deleted to ensure raw audio is not persisted (SC-007).
"""

from __future__ import annotations

import logging
import os
import tempfile

import librosa
import numpy as np

logger = logging.getLogger("tunemuse.services.audio_extractor")


def extract_features(file_bytes: bytes, file_ext: str) -> dict:
    """
    Extract feature vectors from audio file bytes.

    Extracts the same feature set as the client: MFCCs, pitch, rhythm, spectral features,
    RMS, and chroma. Also detects vocal presence — if no valid pitches are detected, raises
    ValueError so the caller can return a 422 error.

    Args:
        file_bytes: Raw bytes of the audio file
        file_ext: File extension (e.g., ".mp3", ".wav")

    Returns:
        Feature dict matching AnalyzeRequest.features structure,
        plus an additional "duration_seconds" field

    Raises:
        ValueError: When no vocals are detected in the audio, message is "no_vocal_content"
    """
    tmp_path = None
    try:
        # Write to temp file (librosa requires a file path)
        suffix = file_ext if file_ext.startswith(".") else f".{file_ext}"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.write(fd, file_bytes)
        os.close(fd)

        # Load audio, unified sample rate 22050Hz, mono
        y, sr = librosa.load(tmp_path, sr=22050, mono=True)

        # Trim to first 60 seconds (if exceeds 180 seconds)
        max_samples = sr * 60
        if len(y) > sr * 180:
            y = y[:max_samples]
            logger.info("Audio exceeds 3 minutes, trimmed to first 60 seconds for analysis")

        duration = len(y) / sr

        # === MFCC (13 coefficients) ===
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1).tolist()
        mfcc_std = np.std(mfcc, axis=1).tolist()

        # === Pitch detection (pyin algorithm) ===
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=50, fmax=2000, sr=sr
        )
        # Filter invalid frames (NaN = frames with no detected pitch)
        valid_pitches = f0[~np.isnan(f0)]

        if len(valid_pitches) < 3:
            raise ValueError("no_vocal_content")

        pitch_min = float(np.min(valid_pitches))
        pitch_max = float(np.max(valid_pitches))
        pitch_median = float(np.median(valid_pitches))
        pitch_mean = float(np.mean(valid_pitches))
        pitch_std_val = float(np.std(valid_pitches))

        # Pitch stability: inverse of coefficient of variation (lower CV = more stable)
        pitch_stability = max(0.0, min(1.0, 1.0 - pitch_std_val / pitch_mean)) if pitch_mean > 0 else 0.0

        # Pitch quartiles
        q25 = float(np.percentile(valid_pitches, 25))
        q75 = float(np.percentile(valid_pitches, 75))

        # === Rhythm/BPM ===
        tempo, _beats = librosa.beat.beat_track(y=y, sr=sr)
        # tempo can be a scalar or a 1D array depending on librosa/numpy version
        tempo_val = float(tempo[0]) if isinstance(tempo, np.ndarray) and tempo.ndim > 0 else float(tempo)
        tempo_bpm = tempo_val if tempo_val > 0 else None

        # Rhythm regularity: estimated from coefficient of variation of beat intervals
        rhythm_regularity = 0.5
        if len(_beats) >= 3:
            beat_times = librosa.frames_to_time(_beats, sr=sr)
            intervals = np.diff(beat_times)
            if len(intervals) > 1 and np.mean(intervals) > 0:
                cv = float(np.std(intervals) / np.mean(intervals))
                rhythm_regularity = max(0.0, min(1.0, 1.0 - cv))

        # === Spectral features ===
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]

        # === RMS energy ===
        rms = librosa.feature.rms(y=y)[0]

        # === Chroma features ===
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1).tolist()

        # === Signal quality score ===
        rms_mean_val = float(np.mean(rms))
        flatness_mean_val = float(np.mean(flatness))
        signal_quality = 1.0
        if rms_mean_val < 0.005:
            signal_quality -= 0.5
        elif rms_mean_val < 0.015:
            signal_quality -= 0.2
        if flatness_mean_val > 0.8:
            signal_quality -= 0.4
        if len(valid_pitches) < 10:
            signal_quality -= 0.2
        signal_quality = max(0.0, min(1.0, signal_quality))

        return {
            "mfcc_mean": mfcc_mean,
            "mfcc_std": mfcc_std,
            "pitch_min_hz": pitch_min,
            "pitch_max_hz": pitch_max,
            "pitch_median_hz": pitch_median,
            "pitch_stability": round(pitch_stability, 4),
            "pitch_contour_stats": {
                "mean": round(pitch_mean, 2),
                "std": round(pitch_std_val, 2),
                "quartile_25": round(q25, 2),
                "quartile_75": round(q75, 2),
            },
            "tempo_bpm": round(tempo_bpm, 1) if tempo_bpm else None,
            "rhythm_regularity": round(rhythm_regularity, 4),
            "spectral_centroid_mean": float(np.mean(centroid)),
            "spectral_centroid_std": float(np.std(centroid)),
            "spectral_flatness_mean": flatness_mean_val,
            "spectral_rolloff_mean": float(np.mean(rolloff)),
            "zero_crossing_rate_mean": float(np.mean(zcr)),
            "rms_mean": rms_mean_val,
            "rms_std": float(np.std(rms)),
            "chroma_mean": chroma_mean,
            "signal_quality_score": round(signal_quality, 2),
            "duration_seconds": round(duration, 1),
        }

    finally:
        # Ensure temp file is deleted (SC-007: do not persist raw audio)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
