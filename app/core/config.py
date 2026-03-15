from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="TenderHack Backend")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost/dbname")
    search_service_url: str = Field(default="https://simple.k.larek.tech")
    ollama_base_url: str = Field(default="http://larek.tech:55300")
    ollama_model: str = Field(default="qwen3-embedding:0.6b")
    qdrant_url: str = Field(default="https://qdrant.larek.tech")
    qdrant_collection: str = Field(default="cte_name")
    log_level: str = Field(default="INFO")

    # Search DB (asyncpg direct connection for full-text search)
    # These can be set explicitly via PG_* env vars; if not set they are
    # derived from DATABASE_URL at validation time.
    pg_host: str = Field(default="")
    pg_port: int = Field(default=0)
    pg_database: str = Field(default="")
    pg_user: str = Field(default="")
    pg_password: str = Field(default="")
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="cte_products")
    cte_search_score_threshold: float = Field(default=0.53)
    ollama_url: str = Field(default="http://larek.tech:55300")
    ollama_model: str = Field(default="qwen3-embedding:0.6b")
    ollama_batch_size: int = Field(default=256)

    redis_url: str = Field(default="redis://localhost:6379/0")
    cache_ttl_seconds: int = Field(default=3600)

    pool_min_size: int = Field(default=2)
    pool_max_size: int = Field(default=5)
    pool_timeout: int = Field(default=30)

    @model_validator(mode="after")
    def _fill_pg_from_database_url(self) -> "Settings":
        """Derive pg_* fields from DATABASE_URL when not explicitly provided."""
        if self.pg_host and self.pg_port and self.pg_database and self.pg_user:
            return self  # explicit values take priority
        parsed = urlparse(self.database_url)
        if not self.pg_host:
            self.pg_host = parsed.hostname or "localhost"
        if not self.pg_port:
            self.pg_port = parsed.port or 5432
        if not self.pg_database:
            self.pg_database = (parsed.path or "/").lstrip("/") or "postgres"
        if not self.pg_user:
            self.pg_user = parsed.username or ""
        if not self.pg_password:
            self.pg_password = parsed.password or ""
        return self

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        raise ValueError("DEBUG should be one of: true/false, debug/release, dev/prod.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
