"""Centralized application settings using Pydantic BaseSettings.

Consolidates environment-driven configuration (API keys, database, feature
toggles) to avoid scattered os.getenv usage and accidental hardcoding.

Usage:
    from config.settings import settings
    print(settings.environment)

Override values by exporting environment variables or creating a `.env` file
based on `env.example`.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    # Environment / runtime
    environment: str = "development"
    debug: bool = True

    # API keys (never commit real keys)
    proxyscrape_api_key: Optional[str] = None
    github_token: Optional[str] = None
    shodan_api_key: Optional[str] = None
    censys_api_id: Optional[str] = None
    censys_api_secret: Optional[str] = None
    brave_api_key: Optional[str] = None
    context7_api_key: Optional[str] = None

    # Data / storage
    database_url: str = "postgresql://postgres:password@localhost:5432/proxy_manager"
    redis_url: str = "redis://localhost:6379/0"

    # Feature toggles
    enable_metrics: bool = True
    enable_scan: bool = True
    enable_html2md: bool = True
    enable_etl: bool = True

    # Concurrency / rate limiting
    max_concurrent_fetch_tasks: int = 1

    # CORS / security
    allowed_origins: List[str] = []

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:  # pragma: no cover - trivial accessor
    return Settings()


settings = get_settings()
