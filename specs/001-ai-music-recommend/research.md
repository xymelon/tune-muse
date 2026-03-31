# Research: AI Music Recommendation via Vocal Analysis

**Feature**: 001-ai-music-recommend
**Date**: 2026-03-29

## 1. Audio Analysis Libraries

### Decision: Client-side feature extraction with Meyda.js + pitchfinder

**Rationale**: Meyda.js (~15KB gzipped) provides real-time extraction of 26+
audio features (MFCC, spectral centroid, spectral flatness, RMS, chroma, ZCR)
via Web Audio API integration. It is lightweight, well-documented, and aligns
with the "minimal libraries" constraint. For pitch detection, pitchfinder
(~5KB) provides multiple algorithms (YIN, AMDF, autocorrelation) in a tiny
package.

**Alternatives considered**:
- **Essentia.js (WASM)**: More comprehensive (pitch, rhythm, spectral features,
  pre-trained ML models), but ~2MB bundle size violates the minimal dependency
  principle. Considered as a future upgrade path if Meyda.js proves
  insufficient.
- **Pure Web Audio API**: Requires implementing FFT, MFCC, and pitch algorithms
  from scratch — violates the "Library-first" constitution principle.
- **TensorFlow.js + Spotify Basic Pitch**: Heavy dependency (~3MB+), overkill
  for feature extraction.

### Decision: Server-side analysis with librosa + scikit-learn

**Rationale**: librosa (8K+ GitHub stars, active as of 2026-03) is the Python
audio analysis standard. It provides pyin pitch tracking, beat_track, MFCC,
mel spectrogram, and spectral features. For the upload path (User Story 2),
server-side feature extraction via librosa ensures consistency with client-side
features. scikit-learn handles classification tasks (timbre clustering, mood
classification) without requiring GPU or heavy deep learning frameworks.

**Alternatives considered**:
- **Essentia Python**: Comprehensive but heavier installation, less widely
  adopted in Python ML ecosystem than librosa.
- **PyTorch/TensorFlow**: Overkill for v1 where feature vectors are classified
  via traditional ML. Reserved for v2 if deep learning models are needed.
- **openSMILE**: Excellent for emotion/formant analysis but complex setup
  and less active community. Consider for v2 if emotion detection needs
  improvement.

---

## 2. Recommendation Engine Architecture

### Decision: Hybrid approach — Rule-based knowledge base + LLM explanation

**Rationale**: A two-layer architecture provides the best balance of
explainability, quality, cost, and resilience:

1. **Layer 1 — Rule engine** (<50ms): A curated knowledge base of 30-40 song
   directions (genre/style entries with vocal trait affinity ranges) is matched
   against the user's vocal profile using weighted scoring. This provides
   deterministic, consistent baseline recommendations.

2. **Layer 2 — LLM refinement** (2-5s): The top 8-12 candidates from Layer 1
   are sent to Claude Sonnet API along with the vocal profile. The LLM
   re-ranks, generates natural language explanations referencing specific vocal
   traits, assigns confidence labels, and may suggest directions the rule
   engine missed.

**Fallback**: If the LLM is unavailable, Layer 1 operates independently using
template-based explanations. This ensures the 30-second response time
requirement (SC-002) is always met.

**Cost estimate**: ~$0.006/request with Claude Sonnet (~1000 input + 800 output
tokens). At 1000 requests/day = ~$180/month.

**Alternatives considered**:
- **Pure LLM**: Simpler implementation but inconsistent results (same input →
  different output), higher cost per request ($0.01-0.05), no fallback if API
  is down, and harder to validate recommendation quality systematically.
- **Pure rule engine**: Lowest cost and latency, but explanations feel
  mechanical and template-like. Lacks nuance for edge cases where a user's
  profile spans multiple styles.
- **Embedding-based (CLAP/MERT)**: Highest potential quality but requires
  curating reference audio collections, GPU inference, and produces
  unexplainable "vector similarity" matches — fundamentally incompatible with
  the spec's explainability requirement (FR-006).

---

## 3. Backend Framework

### Decision: FastAPI + Uvicorn

**Rationale**: FastAPI provides native async support (essential for concurrent
audio analysis requests), automatic OpenAPI schema generation (satisfies the
constitution's "Shared contracts" requirement), built-in Pydantic validation
(type safety), and is the highest-performance Python web framework. A single
FastAPI process handles both API serving and ML inference — no need for
separate model serving infrastructure in v1.

**Alternatives considered**:
- **Flask**: Synchronous WSGI model requires additional worker configuration
  for concurrent requests. No built-in validation or OpenAPI generation.
- **Django REST Framework**: Too heavy for this project scope. Brings ORM,
  admin panel, middleware stack that we don't need.

---

## 4. Storage

### Decision: SQLite (WAL mode) via aiosqlite

**Rationale**: The data model is simple (3-4 tables), the target scale is 500
concurrent sessions (SC-006), and SQLite in WAL mode handles unlimited read
concurrency with thousands of write TPS. Zero operational overhead — no
database server process to manage. Python's `sqlite3` is in the standard
library; `aiosqlite` adds async compatibility for FastAPI.

**Migration path**: If scale exceeds SQLite's limits, migrate to PostgreSQL
by replacing the database driver and connection string. Data model stays
identical.

**Alternatives considered**:
- **PostgreSQL**: Production-grade but requires running a database server,
  connection pooling, and migrations infrastructure. Overkill for v1.
- **File-based JSON**: Too fragile for concurrent access, no query
  capabilities.

---

## 5. Client-Side Audio Recording

### Decision: Web Audio API (native) + MediaRecorder API

**Rationale**: Modern browsers provide MediaRecorder for audio capture and
Web Audio API (AudioContext, AnalyserNode) for real-time processing. No
additional library needed for the recording flow itself. Meyda.js hooks
directly into Web Audio API's AudioContext for feature extraction during
or after recording.

**Browser compatibility**: Chrome 49+, Firefox 25+, Safari 14.1+, Edge 79+.
All modern browsers as required by FR-014.

---

## 6. Frontend Framework and Routing

### Decision: Vite 6 + React 19 + TypeScript + React Router v7

**Rationale**: User specified Vite. React Router v7 is the only UI library
dependency needed for page navigation. State management uses React Context +
useReducer (zero additional dependencies). HTTP requests use native fetch API.

**Key frontend libraries** (total: 3 npm dependencies beyond React):
- react-router-dom v7: Page routing
- meyda: Audio feature extraction
- pitchfinder: Pitch detection

---

## 7. LLM Integration

### Decision: Anthropic Claude Sonnet via official SDK

**Rationale**: Claude Sonnet offers the best cost/quality ratio for the
recommendation refinement and explanation generation task. The Anthropic
Python SDK integrates cleanly with FastAPI's async model.

**Alternatives considered**:
- **OpenAI GPT-4o-mini**: Similar capability and price point, but Claude's
  structured output handling and longer context window better suit the
  detailed vocal profile + candidate list prompts.
- **Local LLM (Ollama/vLLM)**: Eliminates API cost but requires GPU
  infrastructure and produces lower quality explanations. Not viable for v1.

---

## 8. Voice Activity Detection

### Decision: Client-side energy threshold + spectral flatness check

**Rationale**: For v1, simple signal-level checks (RMS energy > threshold +
spectral flatness < threshold) are sufficient to detect whether the audio
contains vocal content. These features are already extracted by Meyda.js, so
no additional library is needed.

**Future upgrade**: If detection accuracy needs improvement, integrate
@ricky0123/vad (Silero VAD model via ONNX Runtime Web, ~1.8K GitHub stars)
for neural network-based voice activity detection in the browser.
