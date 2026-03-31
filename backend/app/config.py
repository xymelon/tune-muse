"""
Application configuration loaded from environment variables.
Uses Pydantic Settings for validation and type safety.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Anthropic API key for LLM-powered recommendation refinement
    anthropic_api_key: str = ""

    # SQLite database URL (relative to backend/ directory)
    database_url: str = "sqlite:///./tunemuse.db"

    # Comma-separated list of allowed CORS origins
    cors_origins: str = "http://localhost:5173"

    # Secret key for JWT token signing
    secret_key: str = "dev-secret-key-change-in-production"

    # JWT token expiry in days
    token_expiry_days: int = 7

    # Minimum signal quality score to accept analysis (0.0-1.0)
    min_signal_quality: float = 0.3

    # Maximum upload file size in bytes (10 MB)
    max_upload_size: int = 10 * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton instance — import this in other modules
settings = Settings()
