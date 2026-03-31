# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (run from `backend/`)
```bash
# Dev server
uvicorn app.main:app --reload --port 8000

# Tests
pytest                          # all tests
pytest tests/unit/              # unit only
pytest tests/integration/       # integration only
pytest tests/contract/          # contract only
pytest -k test_analyze          # single test by name

# Lint
ruff check .
```

### Frontend (run from `frontend/`)
```bash
npm run dev -- --host 0.0.0.0   # dev server at :5173
npm run build                   # typecheck + production build
npm run lint                    # eslint
```

## Architecture

Full-stack app: React 19 frontend + FastAPI backend. Frontend proxies `/api/*` to backend via Vite dev server.

### Backend (`backend/app/`)
- **`api/`** — Route handlers: `analyze.py` (audio analysis), `sessions.py` (history), `auth.py` (JWT auth)
- **`services/`** — Business logic: `vocal_analyzer.py` (5-dimension extraction), `recommendation.py` (hybrid rule engine + Claude LLM refinement), `audio_extractor.py` (librosa), `llm_client.py` (Anthropic API), `auth.py` (JWT/bcrypt)
- **`db/`** — Async SQLite via aiosqlite (`database.py` init, `queries.py` CRUD)
- **`models/schemas.py`** — Pydantic request/response models
- **`knowledge_base/directions.json`** — Music genre/style database used by recommendation engine
- **`config.py`** — Pydantic Settings from `.env` (API key, DB URL, CORS, secret key)

### Frontend (`frontend/src/`)
- **`pages/`** — 4 lazy-loaded routes: Home (record/upload), Analysis (results), History, Compare
- **`services/`** — `api.ts` (REST client, JWT in localStorage), `audioAnalyzer.ts` (Meyda + pitchfinder client-side extraction), `qualityChecker.ts`
- **`components/`** — AudioRecorder, AudioUploader, VocalProfile, Recommendations
- **`types/index.ts`** — Shared TypeScript types mirroring backend schemas

### Data Flow
1. User records/uploads audio on HomePage
2. Frontend extracts audio features client-side (Meyda/pitchfinder)
3. Quality check runs locally, then features POST to `/api/v1/analyze`
4. Backend: vocal analysis → recommendation engine → optional Claude refinement
5. Results stored in SQLite, returned as `AnalyzeResponse`

## Code Style
- **Python**: Ruff with 100-char lines, rules: E, F, W, I, N, UP, B, A, SIM
- **TypeScript**: ESLint with strict TS rules; unused args prefixed `_` are allowed
- **Backend tests**: pytest with `asyncio_mode = "auto"`
