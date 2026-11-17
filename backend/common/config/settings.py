"""Configuration and environment settings for ESTD."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.common.exceptions.custom_exceptions import ConfigurationError

# Base directory for backend (where .env resides)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Centralized application settings loaded from environment or backend/.env."""

    # GNews API Key
    gnews_api_key: Optional[SecretStr] = Field(default=None, alias="GNEWS_API_KEY")

    # NewsData.io API Key
    newsdata_api_key: Optional[SecretStr] = Field(default=None, alias="NEWSDATA_API_KEY")

    # HTTP Client Configuration Defaults
    http_timeout_seconds: float = Field(default=15.0, alias="HTTP_TIMEOUT_SECONDS")
    http_max_retries: int = Field(default=2, alias="HTTP_MAX_RETRIES")

    # App Environment
    app_env: str = Field(default="development", alias="APP_ENV")

    # API Security & Documentation Control
    admin_api_key: Optional[SecretStr] = Field(default=None, alias="ADMIN_API_KEY")
    enable_docs: bool = Field(default=False, alias="ENABLE_DOCS")

    # Pipeline Feature Toggles
    enable_gdrive_export: bool = Field(default=False, alias="ENABLE_GDRIVE_EXPORT")
    enable_scheduler: bool = Field(default=False, alias="ENABLE_SCHEDULER")
    scheduler_interval_hours: int = Field(default=2, alias="SCHEDULER_INTERVAL_HOURS")
    scheduler_articles_per_category: int = Field(default=3, alias="SCHEDULER_ARTICLES_PER_CATEGORY")

    # Plan C Daily Category Digest Toggles
    enable_daily_digest: bool = Field(default=True, alias="ENABLE_DAILY_DIGEST")
    daily_digest_time: str = Field(default="23:59", alias="DAILY_DIGEST_TIME")

    @field_validator("enable_scheduler", "enable_docs", "enable_gdrive_export", "enable_daily_digest", mode="before")
    @classmethod
    def parse_bool_env(cls, v):
        """Parse boolean env variables supporting true/false/on/off/1/0/enabled/disabled."""
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in ("true", "1", "on", "yes", "enabled"):
                return True
            if clean in ("false", "0", "off", "no", "disabled", ""):
                return False
        return bool(v)

    # Browser frontend origin(s) allowed by the backend CORS middleware.
    frontend_url: str = Field(default="", alias="FRONTEND_URL")

    # Database Configuration (Step 4 & Step 5)
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5433, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: Optional[SecretStr] = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="estd_knowledge", alias="POSTGRES_DB")
    database_url: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL",
    )

    # Step 4 Similarity Threshold
    similarity_threshold: float = Field(
        default=0.82,
        alias="SIMILARITY_THRESHOLD",
        ge=0.0,
        le=1.0,
    )

    def get_database_url(self) -> str:
        """Return the effective database connection URL."""
        if self.database_url and self.database_url.strip():
            url = self.database_url.strip()
            if url.startswith("DATABASE_URL="):
                url = url[len("DATABASE_URL="):].strip()
            if url.startswith("postgres://"):
                url = "postgresql://" + url[len("postgres://"):]
            return url
        pwd = self.postgres_password.get_secret_value() if self.postgres_password else "root"
        return f"postgresql://{self.postgres_user}:{pwd}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    def get_server_connection_url(self, dbname: str = "postgres") -> str:
        """Return connection URL to PostgreSQL server maintenance DB for admin tasks."""
        pwd = self.postgres_password.get_secret_value() if self.postgres_password else "root"
        return f"postgresql://{self.postgres_user}:{pwd}@{self.postgres_host}:{self.postgres_port}/{dbname}"

    def get_safe_database_url(self) -> str:
        """Return database URL with password masked for safe logging."""
        import re
        raw_url = self.get_database_url()
        return re.sub(r":([^@]+)@", ":***@", raw_url)


    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_gnews_api_key(self) -> str:
        """Return the unmasked GNews API key or raise ConfigurationError if absent."""
        if not self.gnews_api_key or not self.gnews_api_key.get_secret_value().strip():
            raise ConfigurationError(
                "GNews API key is not configured. Set GNEWS_API_KEY in backend/.env"
            )
        return self.gnews_api_key.get_secret_value().strip()

    def get_newsdata_api_key(self) -> str:
        """Return the unmasked NewsData.io API key or raise ConfigurationError if absent."""
        if not self.newsdata_api_key or not self.newsdata_api_key.get_secret_value().strip():
            raise ConfigurationError(
                "NewsData.io API key is not configured. Set NEWSDATA_API_KEY in backend/.env"
            )
        return self.newsdata_api_key.get_secret_value().strip()

    def get_admin_api_key(self) -> str:
        """Return configured admin API key or a secure default."""
        if self.admin_api_key and self.admin_api_key.get_secret_value().strip():
            return self.admin_api_key.get_secret_value().strip()
        return "estd-secure-admin-key-2026"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
