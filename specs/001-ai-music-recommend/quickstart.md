# Quickstart: AI Music Recommendation

**Feature**: 001-ai-music-recommend
**Date**: 2026-03-29

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- An Anthropic API key (for the recommendation LLM layer)

## Setup

### 1. Clone and install frontend

```bash
cd frontend
npm install
```

### 2. Set up backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///./tunemuse.db
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=your-secret-key-here
```

### 4. Initialize database

```bash
cd backend
python -m app.db.init
```

### 5. Start development servers

**Terminal 1 — Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

The app is available at `http://localhost:5173`. The Vite dev server proxies
`/api/*` requests to the FastAPI backend at `http://localhost:8000`.

## Verify Setup

1. Open `http://localhost:5173` in Chrome/Firefox/Safari.
2. Click "Record" and sing for 10–15 seconds.
3. Click "Stop" — you should see a processing indicator.
4. Within 30 seconds, a vocal profile and 3–8 song direction recommendations
   should appear.

**Backend health check:**
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","version":"0.1.0"}
```

## Project Structure

```
frontend/                    # Vite + React + TypeScript
├── src/
│   ├── components/          # UI components
│   │   ├── AudioRecorder/   # Recording interface
│   │   ├── VocalProfile/    # Analysis result display
│   │   └── Recommendations/ # Song direction cards
│   ├── pages/               # Page components (Home, History, Compare)
│   ├── services/            # API client, audio feature extraction
│   │   ├── audioAnalyzer.ts # Meyda.js + pitchfinder integration
│   │   └── api.ts           # Backend API calls
│   └── types/               # TypeScript type definitions
└── tests/

backend/                     # FastAPI + Python
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/                 # Route handlers
│   │   ├── analyze.py       # POST /analyze, POST /upload
│   │   ├── sessions.py      # GET /sessions, GET /sessions/:id
│   │   └── auth.py          # POST /auth/register, POST /auth/login
│   ├── services/            # Business logic
│   │   ├── vocal_analyzer.py    # Feature → VocalProfile mapping
│   │   ├── recommendation.py    # Rule engine + LLM recommendation
│   │   └── audio_extractor.py   # Server-side feature extraction (librosa)
│   ├── models/              # Pydantic models + DB schemas
│   ├── db/                  # Database setup and queries
│   └── knowledge_base/      # Song direction JSON data
└── tests/
```

## Common Tasks

### Run tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && pytest
```

### Add a new song direction to the knowledge base

Edit `backend/app/knowledge_base/directions.json` and add a new entry
following the existing schema. No database migration needed.

### Check API documentation

Visit `http://localhost:8000/docs` for the auto-generated Swagger UI
(provided by FastAPI).
