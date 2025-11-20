from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="Nissmart Ledger API")
    environment: Literal["development", "staging", "production", "test"] = Field(
        default="development"
    )
    debug: bool = Field(default=True)

    database_url: str = Field(
        default="sqlite+aiosqlite:///./nissmart.db",
        description="SQLAlchemy database URL. Supports async drivers.",
    )
    sync_database_url: str | None = Field(
        default=None,
        description="Optional sync database URL for migrations/maintenance",
    )

    secret_key: str = Field(default="super-secret-key", description="Signing key")

    log_level: str = Field(default="INFO")
    enable_sql_echo: bool = Field(default=False)

    idempotency_ttl_seconds: int = Field(default=10 * 60, description="10 minutes")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached copy of the application settings."""

    return Settings()
