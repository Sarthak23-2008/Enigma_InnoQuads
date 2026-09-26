"""Application settings, loaded from environment variables (never hard-coded secrets)."""
from __future__ import annotations

import logging
import secrets
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("safebite.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"  # development | production | test
    DATABASE_URL: str = "sqlite:///./safebite.db"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    EXTRA_CORS_ORIGINS: str = ""

    # OCR: tesseract (default, open source) | gemini | demo
    OCR_PROVIDER: str = "tesseract"
    OCR_API_KEY: str = ""
    OCR_LANG: str = "eng"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    TESSERACT_CMD: str = ""

    MAX_UPLOAD_MB: int = 8
    STORE_UPLOADS: bool = False
    UPLOAD_DIR: str = "./uploads"

    NOTIFICATION_PROVIDER: str = "mock"  # mock | resend
    RESEND_API_KEY: str = ""
    REPORT_FROM_EMAIL: str = "SafeBite <reports@example.com>"

    DEMO_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    @field_validator("DATABASE_URL")
    @classmethod
    def _fix_pg_scheme(cls, v: str) -> str:
        # Render/Supabase/Heroku give postgres:// — SQLAlchemy needs postgresql+psycopg2://
        if v.startswith("postgres://"):
            v = "postgresql+psycopg2://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+psycopg2://" + v[len("postgresql://"):]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.FRONTEND_URL.split(",") if o.strip()]
        origins += [o.strip().rstrip("/") for o in self.EXTRA_CORS_ORIGINS.split(",") if o.strip()]
        if not self.is_production:
            origins += ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"]
        return sorted(set(origins))


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.JWT_SECRET:
        if s.is_production:
            raise RuntimeError("JWT_SECRET must be set in production.")
        # Development only: ephemeral secret. Tokens are invalidated on restart.
        s.JWT_SECRET = secrets.token_urlsafe(48)
        log.warning("JWT_SECRET not set; using an ephemeral development secret.")
    return s
