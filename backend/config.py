"""
config.py — PathFinder AI
Loads and validates all environment variables using pydantic-settings.
Import `settings` anywhere in the app: from config import settings
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    All configuration is read from the .env file (or real environment variables).
    Pydantic validates types and raises clear errors if anything is missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unknown env vars
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = Field(default="development", description="development | production")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    secret_key: str = Field(default="change-me-in-production")

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated origins, e.g. "http://localhost:3000,https://myapp.com"
    allowed_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")

    @property
    def cors_origins(self) -> list[str]:
        """Return ALLOWED_ORIGINS as a Python list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="pathfinder_ai")

    # ── Google Gemini API ─────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.5-flash")

    # ── GitHub API ────────────────────────────────────────────────────────────
    github_token: str = Field(default="")

    # ── YouTube Data API v3 ───────────────────────────────────────────────────
    youtube_api_key: str = Field(default="")

    # ── NLP / ML ──────────────────────────────────────────────────────────────
    spacy_model: str = Field(default="en_core_web_sm")
    sbert_model: str = Field(default="all-MiniLM-L6-v2")

    # ── File Upload ───────────────────────────────────────────────────────────
    max_upload_size_mb: int = Field(default=5)
    upload_dir: str = Field(default="uploads")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached singleton Settings instance.
    Using lru_cache means the .env file is only parsed once per process.
    """
    return Settings()


# Convenience shortcut — use `from config import settings` anywhere
settings: Settings = get_settings()