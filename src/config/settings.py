from __future__ import annotations

from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Environment
    environment: str = Field(default="development")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    log_level: str = Field(default="info")

    # Database - Postgres
    db_user: str = Field(default="proxyadmin")
    db_password: str = Field(default="secretpassword")
    db_name: str = Field(default="proxypool")
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)

    # Redis
    redis_password: str = Field(default="")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    # Security
    cors_allow_origins: List[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ])
    api_key_enabled: bool = Field(default=False)
    api_key_header: str = Field(default="X-API-Key")
    api_keys: List[str] = Field(default_factory=list)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
