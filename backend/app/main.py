"""
FastAPI application entry point.
Configures CORS middleware, route registration, database initialization, and health check endpoint.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import init_database

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tunemuse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management: initialize database on startup, clean up resources on shutdown.
    """
    logger.info("Initializing database...")
    await init_database(settings.database_url)
    logger.info("Database initialized successfully")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="TuneMuse API",
    description="AI Music Recommendation via Vocal Analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration: allow cross-origin requests from frontend dev server
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Request logging middleware: logs method, path, status code, and duration of each request.
    """
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "%s %s → %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint for monitoring and deployment verification.

    Returns:
        {"status": "ok", "version": "0.1.0"}
    """
    return {"status": "ok", "version": "0.1.0"}


# Lazy import and register routes to avoid circular dependencies
# Routes will be implemented in their respective Phases; mount points are reserved here
def register_routes():
    """Register all API routes. Uncomment after route modules are implemented."""
    try:
        from app.api.analyze import router as analyze_router
        app.include_router(analyze_router, prefix="/api/v1")
    except ImportError:
        logger.warning("Analyze routes not yet implemented")

    try:
        from app.api.sessions import router as sessions_router
        app.include_router(sessions_router, prefix="/api/v1")
    except ImportError:
        logger.warning("Sessions routes not yet implemented")

    try:
        from app.api.auth import router as auth_router
        app.include_router(auth_router, prefix="/api/v1")
    except ImportError:
        logger.warning("Auth routes not yet implemented")


register_routes()
