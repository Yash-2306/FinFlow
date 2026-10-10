"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/finflow.db"

    # Application
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # CORS – comma-separated list of allowed origins (beyond the hardcoded ones)
    CORS_ORIGINS: str = ""

    @property
    def extra_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS_ORIGINS env var into a list."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
