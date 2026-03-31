# Tasks: AI Music Recommendation via Vocal Analysis

**Input**: Design documents from `/specs/001-ai-music-recommend/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The constitution mandates testing (Principle II). Test tasks are included for each user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for Python FastAPI, `frontend/` for Vite React TypeScript
- Frontend source: `frontend/src/`
- Backend source: `backend/app/`
- Frontend tests: `frontend/tests/`
- Backend tests: `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, tooling, and directory structure

- [x] T001 Create frontend project with Vite 6 + React 19 + TypeScript in `frontend/` — initialize with `npm create vite@latest`, configure `tsconfig.json` with strict mode, add `vite.config.ts` with `/api` proxy to `http://localhost:8000`
- [x] T002 Create backend project in `backend/` — initialize `pyproject.toml` with Python 3.11+, create `requirements.txt` with: fastapi, uvicorn, pydantic, aiosqlite, librosa, scikit-learn, numpy, anthropic, python-multipart, python-jose[cryptography], passlib[bcrypt]
- [x] T003 [P] Install frontend dependencies: `react-router-dom@7`, `meyda`, `pitchfinder` in `frontend/package.json`
- [x] T004 [P] Configure frontend tooling: ESLint + Prettier in `frontend/.eslintrc.cjs` and `frontend/.prettierrc`; add lint/format scripts to `frontend/package.json`
- [x] T005 [P] Configure backend tooling: Ruff linter config in `backend/pyproject.toml` with `[tool.ruff]` section; add `ruff check` and `ruff format` scripts
- [x] T006 [P] Create design tokens CSS file at `frontend/src/tokens/design-tokens.css` — define CSS custom properties for colors (primary, secondary, surface, error, text), spacing scale (4px base), typography (font family, sizes, weights), border radius, shadows, and breakpoints (320px, 768px, 1024px)
- [x] T007 [P] Create shared TypeScript types at `frontend/src/types/index.ts` — define interfaces for `AudioFeatures`, `VocalProfile`, `Recommendation`, `AnalysisSession`, `AnalyzeRequest`, `AnalyzeResponse`, `SessionListResponse` matching the API contract in `contracts/api.md`
- [x] T008 [P] Create backend Pydantic schemas at `backend/app/models/schemas.py` — define request/response models for all API endpoints: `AnalyzeRequest`, `AnalyzeResponse`, `VocalProfileResponse`, `RecommendationResponse`, `SessionListResponse`, `AuthRequest`, `AuthResponse`, `ErrorResponse` matching `contracts/api.md`

**Checkpoint**: Project skeleton ready — both `npm run dev` and `uvicorn app.main:app` can start without errors

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Create SQLite database initialization module at `backend/app/db/init.py` — create tables for `users`, `analysis_sessions`, `vocal_profiles`, `recommendations` per data-model.md; use aiosqlite; enable WAL mode; create indexes on `analysis_sessions.user_id` and `analysis_sessions.created_at`
- [x] T010 Create database query module at `backend/app/db/queries.py` — implement async CRUD functions: `create_session()`, `update_session_status()`, `create_vocal_profile()`, `create_recommendations()`, `get_session_by_id()`, `get_sessions_by_user()` using aiosqlite
- [x] T011 [P] Create FastAPI app entry point at `backend/app/main.py` — configure CORS middleware (allow origins from env `CORS_ORIGINS`), mount API router at `/api/v1`, add startup event to initialize database, add health check endpoint `GET /api/v1/health` returning `{"status":"ok","version":"0.1.0"}`
- [x] T012 [P] Create backend environment config at `backend/app/config.py` — load settings from environment variables: `ANTHROPIC_API_KEY`, `DATABASE_URL` (default: `sqlite:///./tunemuse.db`), `CORS_ORIGINS`, `SECRET_KEY`; use Pydantic Settings
- [x] T013 [P] Create React app shell at `frontend/src/App.tsx` and `frontend/src/main.tsx` — set up React Router v7 with routes: `/` (HomePage), `/analysis/:sessionId` (AnalysisPage), `/history` (HistoryPage), `/compare` (ComparePage); import design tokens CSS; add responsive layout wrapper
- [x] T014 [P] Create API client service at `frontend/src/services/api.ts` — implement fetch-based functions: `submitFeatures(features)`, `uploadAudio(file)`, `getSessionHistory()`, `getSessionDetail(id)` matching the API contracts; include error handling that surfaces user-friendly messages
- [x] T015 Create song direction knowledge base JSON at `backend/app/knowledge_base/directions.json` — curate 30–35 entries covering: Ballad (classic, power, jazz), Pop (synth, dance, indie), Rock (soft, alternative), R&B (neo-soul, contemporary), Folk (singer-songwriter, acoustic), Jazz (vocal jazz, bossa nova), Country (modern, classic), Electronic (chillwave, ambient vocal), Musical Theater, Chinese Pop (C-Pop ballad, C-Pop dance), Hip-Hop/Rap (melodic). Each entry has: id, genre, sub_style, tempo_range, key_range, vocal_difficulty, mood_affinity, timbre_affinity, rhythm_requirements, expression_traits, description, example_songs, explanation_templates

**Checkpoint**: Foundation ready — database initializes, FastAPI serves health check, frontend renders shell with routing, API client is wired up

---

## Phase 3: User Story 1 — Record and Analyze Singing (Priority: P1)

**Goal**: Users record singing in the browser, the system extracts audio features client-side, sends them to the backend, and displays a vocal analysis profile with 4+ trait dimensions.

**Independent Test**: Record a 30-second clip → see vocal profile with melody range, rhythm stability, mood, and timbre descriptions.

### Tests for User Story 1

- [ ] T016 [P] [US1] Write unit tests for audio analyzer service in `frontend/tests/unit/audioAnalyzer.test.ts` — test MFCC extraction output shape (13 coefficients), pitch detection returns valid Hz range, RMS energy calculation, spectral features output, and signal quality score computation; mock Web Audio API AudioContext
- [x] T017 [P] [US1] Write unit tests for vocal analyzer service in `backend/tests/unit/test_vocal_analyzer.py` — test feature vector to VocalProfile mapping: pitch Hz → note names (e.g., 261.6 → "C4"), timbre classification from spectral features, mood inference from valence/energy/tension scores, confidence calculation, and edge cases (very narrow pitch range, extreme feature values)
- [x] T018 [P] [US1] Write integration test for POST /api/v1/analyze endpoint in `backend/tests/integration/test_analyze.py` — submit a valid feature vector fixture, verify 200 response with complete vocal_profile (all 5 dimensions) and 3–8 recommendations; test 400 for invalid features; test 422 for low signal_quality_score (<0.3)
- [x] T019 [P] [US1] Write contract test in `backend/tests/contract/test_analyze_contract.py` — verify POST /api/v1/analyze request schema accepts all fields from contracts/api.md; verify response schema matches AnalyzeResponse Pydantic model; validate OpenAPI spec auto-generated by FastAPI matches contract doc

### Implementation for User Story 1

- [x] T020 [P] [US1] Create audio recorder service at `frontend/src/services/audioRecorder.ts` — implement `AudioRecorderService` class wrapping MediaRecorder API: `startRecording()` (request microphone via getUserMedia, create MediaRecorder with audio/webm), `stopRecording()` (return AudioBuffer), `getRecordingDuration()`, `isRecording()` state; handle microphone permission denial with clear error; detect unsupported browsers and suggest upload path
- [x] T021 [P] [US1] Create audio analyzer service at `frontend/src/services/audioAnalyzer.ts` — implement `analyzeAudio(audioBuffer: AudioBuffer): AudioFeatures` using Meyda.js for MFCC (13 coefficients), spectral centroid, spectral flatness, spectral rolloff, ZCR, RMS, chroma; use pitchfinder (YIN algorithm) for pitch detection (min/max/median/stability from pitch contour); compute rhythm regularity from onset detection; compute signal_quality_score from RMS mean and spectral flatness
- [x] T022 [P] [US1] Create signal quality checker at `frontend/src/services/qualityChecker.ts` — implement `checkQuality(features: AudioFeatures): QualityResult` that evaluates: RMS below threshold → "too quiet", spectral flatness too high → "too noisy", pitch range too narrow → "insufficient vocal variation"; return `{passed: boolean, issues: string[], score: number}`
- [x] T023 [US1] Create vocal analyzer service at `backend/app/services/vocal_analyzer.py` — implement `analyze_features(features: AnalyzeRequest) -> VocalProfile`: map pitch Hz to musical note names (using frequency-to-note formula), classify timbre from MFCC/spectral features (warmth from low MFCC energy, brightness from spectral centroid, breathiness from spectral flatness), infer mood from chroma + energy + spectral features (valence, energy, tension on 0-1 scale), assess expression (vibrato from pitch stability variance, dynamic range from RMS std, articulation from ZCR patterns); generate plain-language descriptions for each trait dimension using template strings
- [x] T024 [US1] Create recommendation service at `backend/app/services/recommendation.py` — implement hybrid rule engine: `get_recommendations(profile: VocalProfile) -> list[Recommendation]`: (1) load directions.json knowledge base, (2) score each direction against profile using weighted matching: pitch range overlap (30%), timbre affinity (25%), mood alignment (20%), rhythm fit (15%), expression match (10%), (3) sort by score, take top 8-12 candidates, (4) assign confidence levels (score>0.75 → "high", >0.55 → "medium", else → "exploratory"), (5) generate explanation from templates referencing specific profile traits; return top 3-8 results
- [x] T025 [US1] Create LLM client service at `backend/app/services/llm_client.py` — implement `refine_recommendations(profile: VocalProfile, candidates: list[Recommendation]) -> list[Recommendation]` using Anthropic Python SDK: send vocal profile + rule engine candidates to Claude Sonnet, ask LLM to re-rank, generate natural language explanations referencing specific traits, suggest any missing directions; implement fallback that returns rule-engine results with template explanations if LLM call fails or times out (5s timeout)
- [x] T026 [US1] Create analyze API route at `backend/app/api/analyze.py` — implement `POST /api/v1/analyze`: validate request with Pydantic schema, check signal_quality_score >= 0.3 (return 422 if below), call vocal_analyzer.analyze_features(), call recommendation.get_recommendations(), call llm_client.refine_recommendations(), save session + profile + recommendations to database, return AnalyzeResponse; handle all errors with user-friendly messages per error response schemas in contracts/api.md
- [x] T027 [US1] Create AudioRecorder component at `frontend/src/components/AudioRecorder/AudioRecorder.tsx` — implement recording UI: large "Record" button (tap to start/stop), real-time waveform visualization using Web Audio API AnalyserNode, recording timer display (seconds elapsed), recording state indicator (idle/recording/processing), microphone permission prompt handling; use design tokens for all styling; mobile-responsive layout; keyboard accessible (Space to start/stop)
- [x] T028 [US1] Create VocalProfile display component at `frontend/src/components/VocalProfile/VocalProfile.tsx` — implement 4-dimension trait card layout: Pitch (range display as note names + visual range bar), Rhythm (tempo + regularity description), Mood (valence/energy/tension as descriptive labels + mood icon), Timbre (warmth/brightness/breathiness as visual meters + description), Expression (vibrato/dynamic range + articulation); each card shows plain-language description; overall confidence indicator; responsive grid (1 col mobile, 2 col tablet, 4 col desktop); use design tokens
- [x] T029 [US1] Create HomePage at `frontend/src/pages/HomePage.tsx` — implement landing page with: hero section explaining the product (record singing → get song recommendations), AudioRecorder component, processing state (spinner + "Analyzing your voice..." message), quality error state (show re-record suggestion), navigation to AnalysisPage on successful analysis; store analysis result in React state; mobile-first responsive layout
- [x] T030 [US1] Create AnalysisPage at `frontend/src/pages/AnalysisPage.tsx` — implement results page with: VocalProfile component showing full trait breakdown, Recommendations section (to be fully implemented in US3 but show placeholder "Recommendations loading..." for now), "Record Again" button to return to HomePage; receive analysis data via route state or session storage; handle missing data gracefully (redirect to home)

**Checkpoint**: User Story 1 fully functional — user can record singing, see vocal profile with 4 trait dimensions and plain-language descriptions. Recommendations section shows placeholder.

---

## Phase 4: User Story 3 — Receive Personalized Song Recommendations (Priority: P1)

**Goal**: After vocal analysis completes, display 3–8 explainable song direction recommendations with confidence levels.

**Independent Test**: Complete a vocal analysis → see 3–8 recommendation cards each with genre, tempo range, difficulty, mood alignment, explanation, and confidence badge.

### Tests for User Story 3

- [x] T031 [P] [US3] Write unit tests for recommendation service in `backend/tests/unit/test_recommendation.py` — test rule engine scoring: warm timbre profile scores high for ballad direction, fast rhythm profile scores high for dance-pop direction; test 3-8 recommendation count constraint; test confidence level assignment (high/medium/exploratory thresholds); test explanation templates populate with correct profile values; test fallback behavior when LLM client raises exception
- [ ] T032 [P] [US3] Write unit test for Recommendations component in `frontend/tests/unit/Recommendations.test.ts` — test rendering 5 recommendation cards with all required fields (genre, tempo, difficulty, mood, explanation); test confidence badge colors (high=green, medium=yellow, exploratory=blue); test empty state; test reference songs display

### Implementation for User Story 3

- [x] T033 [US3] Create Recommendations display component at `frontend/src/components/Recommendations/Recommendations.tsx` — implement recommendation card list: each card shows genre/sub_style as header, tempo range (e.g., "60–85 BPM"), vocal difficulty level (1-5 stars or scale), mood alignment text, match explanation paragraph referencing vocal traits, confidence badge ("High Match" / "Good Match" / "Worth Exploring" with distinct colors), reference songs list (collapsible); cards sorted by rank; responsive grid (1 col mobile, 2 col desktop); use design tokens for all styling
- [x] T034 [US3] Update AnalysisPage to show full recommendations at `frontend/src/pages/AnalysisPage.tsx` — replace placeholder with Recommendations component; pass recommendations data from analysis response; add section header "Song Directions For You" with count indicator; add scroll-to-recommendations after profile section

**Checkpoint**: User Stories 1 + 3 fully functional — record singing → see vocal profile → see 3–8 explainable recommendation cards. This is the MVP.

---

## Phase 5: User Story 2 — Upload Audio for Analysis (Priority: P2)

**Goal**: Users upload a pre-recorded audio file (MP3, WAV, M4A, OGG) as an alternative to live recording, receiving the same vocal profile and recommendations.

**Independent Test**: Upload a 30-second MP3 file → see the same type of vocal profile and recommendations as the recording flow.

### Tests for User Story 2

- [ ] T035 [P] [US2] Write unit tests for audio extractor service in `backend/tests/unit/test_audio_extractor.py` — test librosa feature extraction from WAV buffer: verify MFCC shape (13 coefficients), pitch range extraction, tempo estimation, spectral feature computation; test audio segment trimming (>3 min → first 60s); test unsupported format detection; test corrupt file handling
- [ ] T036 [P] [US2] Write integration test for POST /api/v1/upload endpoint in `backend/tests/integration/test_upload.py` — upload a valid WAV test fixture, verify 200 response with vocal_profile and recommendations matching analyze response schema; test 400 for non-audio file; test 413 for file >10 MB; test 422 for instrumental-only audio (no vocals detected)

### Implementation for User Story 2

- [x] T037 [US2] Create audio extractor service at `backend/app/services/audio_extractor.py` — implement `extract_features(file_bytes: bytes, content_type: str) -> AudioFeatures`: validate file format (MP3, WAV, M4A, OGG) and size (≤10 MB), load audio with librosa, trim to first 60 seconds if longer, extract same feature set as client-side (MFCC mean/std, pitch min/max/median/stability via librosa.pyin, tempo via librosa.beat.beat_track, spectral centroid/flatness/rolloff, ZCR, RMS, chroma), detect vocal presence (energy threshold + spectral analysis, return error if no vocals), compute signal quality score, return AudioFeatures matching AnalyzeRequest.features schema; delete temporary file after processing
- [x] T038 [US2] Create upload API route at `backend/app/api/analyze.py` (extend existing file) — add `POST /api/v1/upload` endpoint: accept multipart/form-data file upload, validate file type and size, call audio_extractor.extract_features(), then follow same pipeline as /analyze (vocal_analyzer → recommendation → llm_client → save to DB → return response); return appropriate error responses (400 unsupported format, 413 too large, 422 no vocals) per contracts/api.md
- [x] T039 [US2] Create AudioUploader component at `frontend/src/components/AudioUploader/AudioUploader.tsx` — implement file upload UI: drag-and-drop zone + file picker button, accepted formats display (MP3, WAV, M4A, OGG), file size limit display (max 10 MB), upload progress indicator, file validation (type + size) before upload, error display for invalid files with clear messages; use design tokens; keyboard accessible
- [x] T040 [US2] Update HomePage to support both recording and upload at `frontend/src/pages/HomePage.tsx` — add tab or toggle between "Record" and "Upload" modes; show AudioRecorder in record mode, AudioUploader in upload mode; both flows navigate to AnalysisPage on success; persist selected mode in session

**Checkpoint**: User Stories 1, 2, and 3 all functional — users can record OR upload → see vocal profile → see recommendations

---

## Phase 6: User Story 4 — View and Compare Analysis History (Priority: P3)

**Goal**: Registered users can view past analysis sessions and compare vocal profiles side by side to track progress.

**Independent Test**: Register an account, complete 2 analyses, view history page showing both sessions, select 2 to compare and see trait changes highlighted.

### Tests for User Story 4

- [x] T041 [P] [US4] Write unit tests for auth service in `backend/tests/unit/test_auth.py` — test password hashing and verification, JWT token generation and validation, token expiry handling, duplicate email registration rejection
- [x] T042 [P] [US4] Write integration tests for auth and sessions endpoints in `backend/tests/integration/test_sessions.py` — test POST /auth/register (201 + token), POST /auth/login (200 + token, 401 for bad creds), GET /sessions (returns user's sessions, 401 without token), GET /sessions/:id (returns full session, 404 for other user's session)

### Implementation for User Story 4

- [x] T043 [P] [US4] Create auth service at `backend/app/services/auth.py` — implement `register_user(email, password, display_name, locale)`, `login_user(email, password)`, `verify_token(token) -> user_id`; use passlib[bcrypt] for password hashing, python-jose for JWT tokens with SECRET_KEY from config; tokens expire in 7 days
- [x] T044 [P] [US4] Create auth API routes at `backend/app/api/auth.py` — implement `POST /api/v1/auth/register` (create user, return token), `POST /api/v1/auth/login` (verify credentials, return token); validate with Pydantic schemas; return 409 for duplicate email, 401 for invalid credentials
- [x] T045 [US4] Create sessions API routes at `backend/app/api/sessions.py` — implement `GET /api/v1/sessions` (list user's sessions with pagination: limit, offset, sort params; return session summaries with vocal_profile_summary), `GET /api/v1/sessions/:id` (return full session with vocal_profile and recommendations); both require Bearer token authentication via auth.verify_token(); return 401 without token, 404 for non-existent or other user's sessions
- [x] T046 [US4] Update analyze API to associate sessions with authenticated users at `backend/app/api/analyze.py` — if Authorization header present, extract user_id from JWT token and set on the AnalysisSession; anonymous sessions (no token) continue to work but user_id stays null
- [x] T047 [P] [US4] Create HistoryPage at `frontend/src/pages/HistoryPage.tsx` — implement session history list: fetch sessions from GET /api/v1/sessions, display each as a card with date, source type icon (mic/upload), vocal profile summary (pitch range, mood label, timbre label), recommendation count; paginated list (load more button); select 2 sessions to compare (checkbox + "Compare" button enabled when exactly 2 selected); handle unauthenticated state (prompt to register/login); mobile responsive
- [x] T048 [US4] Create ComparePage at `frontend/src/pages/ComparePage.tsx` — implement side-by-side comparison view: fetch full details for 2 selected sessions from GET /api/v1/sessions/:id, display vocal profiles side by side with change indicators (arrows up/down, delta values, e.g., "Range expanded from C3–G4 to C3–A4"), highlight improved/changed traits with color coding (green for improvement, neutral for same, yellow for change); show recommendation differences; responsive layout (stacked on mobile, side-by-side on desktop)
- [x] T049 [US4] Add auth UI to frontend — create LoginModal component at `frontend/src/components/common/LoginModal.tsx` with email/password form for login and registration toggle; add auth state management to App.tsx using React Context (AuthContext: user, token, login, register, logout); persist token in localStorage; add login/register button to navigation; show user display name when authenticated

**Checkpoint**: All user stories functional — record/upload → analyze → recommend → history → compare

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T050 [P] Add loading states across all pages — HomePage: waveform animation during recording, processing spinner during analysis; AnalysisPage: skeleton cards for profile and recommendations; HistoryPage: skeleton list while loading; ComparePage: skeleton comparison while loading; all states use design token colors and consistent animation patterns
- [x] T051 [P] Add error boundary and error states — create ErrorBoundary component at `frontend/src/components/common/ErrorBoundary.tsx`; add error display states to all pages: network error (retry button), analysis failure (re-record/re-upload suggestion), server error (generic message without technical details); all error messages in plain language per constitution Principle III
- [ ] T052 [P] Add responsive design polish — audit all pages and components at 320px, 768px, 1024px breakpoints; fix any overflow, touch target, or readability issues; ensure AudioRecorder works well on mobile (larger tap targets, no hover-dependent interactions)
- [ ] T053 [P] Add accessibility audit — verify WCAG 2.1 AA compliance: keyboard navigation through all interactive elements, screen reader labels for audio controls and chart visualizations, sufficient color contrast (4.5:1 for text), focus indicators visible, ARIA attributes on custom components (recorder, profile charts, recommendation cards)
- [x] T054 [P] Add backend request logging middleware at `backend/app/main.py` — log request method, path, response status, and duration for every API call; log errors with stack traces at ERROR level; use Python logging module with structured format
- [x] T055 Run frontend and backend test suites, verify all tests pass, and confirm test coverage meets 80% threshold for new code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 3 (Phase 4)**: Depends on User Story 1 (Phase 3) — needs vocal profile data to generate recommendations
- **User Story 2 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US1 if staffed, but logically depends on the analyze pipeline from US1
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can run in parallel with other stories for auth/sessions, but full flow needs US1+US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Record + Analyze)**: BLOCKS US3 (recommendations need a vocal profile to display)
- **US3 (Recommendations)**: Depends on US1 for the analysis pipeline; its backend services (recommendation.py, llm_client.py) are built in US1 but the frontend display is US3
- **US2 (Upload)**: Independent of US1 for backend (audio_extractor.py is new), but reuses US1's analyze pipeline and US3's recommendations display
- **US4 (History + Compare)**: Independent auth/sessions backend, but the full user flow depends on US1+US3 being complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/schemas before services
- Services before API routes
- Backend before frontend (frontend calls backend API)
- Core implementation before UI polish

### Parallel Opportunities

- **Phase 1**: T003, T004, T005, T006, T007, T008 all in parallel after T001+T002
- **Phase 2**: T011, T012, T013, T014 in parallel after T009+T010; T015 independent
- **Phase 3**: T016, T017, T018, T019 (tests) in parallel; T020, T021, T022 (frontend services) in parallel; T027, T028 (components) after services
- **Phase 4**: T031, T032 (tests) in parallel
- **Phase 5**: T035, T036 (tests) in parallel; T039 (uploader component) parallel with T037 (backend extractor)
- **Phase 6**: T041, T042 (tests) in parallel; T043, T044 (auth) parallel with T047 (history page)
- **Phase 7**: T050, T051, T052, T053, T054 all in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task: T016 "Unit tests for audioAnalyzer in frontend/tests/unit/audioAnalyzer.test.ts"
Task: T017 "Unit tests for vocal_analyzer in backend/tests/unit/test_vocal_analyzer.py"
Task: T018 "Integration test for POST /analyze in backend/tests/integration/test_analyze.py"
Task: T019 "Contract test for analyze in backend/tests/contract/test_analyze_contract.py"

# Launch frontend services together (after tests written):
Task: T020 "AudioRecorder service in frontend/src/services/audioRecorder.ts"
Task: T021 "AudioAnalyzer service in frontend/src/services/audioAnalyzer.ts"
Task: T022 "QualityChecker service in frontend/src/services/qualityChecker.ts"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Record + Analyze)
4. Complete Phase 4: User Story 3 (Recommendations)
5. **STOP and VALIDATE**: Record a song, see vocal profile + 3-8 recommendations with explanations
6. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Record + Analyze) → Test vocal profile display → First demo
3. Add US3 (Recommendations) → Test full pipeline → **MVP Deploy**
4. Add US2 (Upload) → Test upload flow → Deploy
5. Add US4 (History + Compare) → Test registered user flow → Deploy
6. Polish phase → Final QA → Production release

### Parallel Team Strategy

With 2 developers:

1. Both complete Setup + Foundational together
2. After Phase 2:
   - **Dev A**: US1 backend (T023-T026) → US3 backend (T024 already done) → US2 backend (T037-T038) → US4 backend (T043-T046)
   - **Dev B**: US1 frontend (T020-T022, T027-T030) → US3 frontend (T033-T034) → US2 frontend (T039-T040) → US4 frontend (T047-T049)
3. Both converge on Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No raw audio persisted on server (SC-007) — temporary files deleted immediately after feature extraction
- Knowledge base (directions.json) is a curated static file, not database-managed for v1
