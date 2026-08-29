"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    All values are read from environment variables (or a .env file).
    Never hardcode secrets here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Google AI ─────────────────────────────────────────────────────────────
    google_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model identifier",
    )

    # ── Agent mode ─────────────────────────────────────────────────────────────
    agent_mode: str = Field(
        default="mock",
        description="'gemini' for real Gemini calls, 'mock' for deterministic dev responses",
    )

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database URL",
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    # ── App metadata ───────────────────────────────────────────────────────────
    app_name: str = "Collaborative Partner API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Enable debug mode")

    # ── Input limits ───────────────────────────────────────────────────────────
    max_message_length: int = Field(
        default=4000,
        description="Maximum allowed characters in a single chat message",
    )

    @field_validator("agent_mode")
    @classmethod
    def validate_agent_mode(cls, v: str) -> str:
        allowed = {"gemini", "mock"}
        if v not in allowed:
            raise ValueError(f"agent_mode must be one of {allowed}, got '{v}'")
        return v

    def get_cors_origins(self) -> List[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
