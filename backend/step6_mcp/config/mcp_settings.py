"""Centralized settings and security configuration for Step 6 MCP Integration."""
from functools import lru_cache
import os
from pathlib import Path
import re
from typing import Optional, Set

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.common.config.settings import ENV_FILE_PATH, get_settings
from backend.step6_mcp.exceptions import MCPSecurityError

# Default paths for Google Drive OAuth
DEFAULT_GDRIVE_OAUTH_PATH = ENV_FILE_PATH.parent / "credentials" / "gcp-oauth.keys.json"
DEFAULT_GDRIVE_CREDENTIALS_PATH = ENV_FILE_PATH.parent / "credentials" / "gdrive-server-credentials.json"


class MCPSettings(BaseSettings):
    """Configuration for PostgreSQL and Google Drive/Docs MCP servers."""

    # PostgreSQL MCP Server Settings (reused from core settings)
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5433, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: Optional[SecretStr] = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="estd_knowledge", alias="POSTGRES_DB")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # Google Drive / Docs MCP Server Settings
    gdrive_oauth_path: str = Field(
        default=str(DEFAULT_GDRIVE_OAUTH_PATH),
        alias="GDRIVE_OAUTH_PATH",
    )
    gdrive_credentials_path: str = Field(
        default=str(DEFAULT_GDRIVE_CREDENTIALS_PATH),
        alias="GDRIVE_CREDENTIALS_PATH",
    )

    # General MCP Client Timeouts and Retries
    mcp_timeout_seconds: float = Field(default=20.0, alias="MCP_TIMEOUT_SECONDS")
    mcp_init_timeout_seconds: float = Field(default=15.0, alias="MCP_INIT_TIMEOUT_SECONDS")

    # Security Constraints
    read_only_enforced: bool = Field(default=True, alias="MCP_READ_ONLY_ENFORCED")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **values):
        super().__init__(**values)
        core_settings = get_settings()
        if not self.postgres_password and core_settings.postgres_password:
            self.postgres_password = core_settings.postgres_password

        passed_keys = {k.lower() for k in values.keys()}
        has_custom_conn = bool(
            {"postgres_host", "postgres_port", "postgres_user", "postgres_db"} & passed_keys
        )

        if "postgres_host" not in passed_keys and core_settings.postgres_host:
            self.postgres_host = core_settings.postgres_host
        if "postgres_port" not in passed_keys and core_settings.postgres_port:
            self.postgres_port = core_settings.postgres_port
        if "postgres_user" not in passed_keys and core_settings.postgres_user:
            self.postgres_user = core_settings.postgres_user
        if "postgres_db" not in passed_keys and core_settings.postgres_db:
            self.postgres_db = core_settings.postgres_db

        if "database_url" not in passed_keys:
            if has_custom_conn:
                self.database_url = None
            elif core_settings.database_url:
                self.database_url = core_settings.database_url

    def get_postgres_connection_url(self) -> str:
        """Return the raw PostgreSQL database URL (used only for server execution)."""
        if self.database_url and self.database_url.strip():
            return self.database_url.strip()
        pwd = self.postgres_password.get_secret_value() if self.postgres_password else "root"
        return f"postgresql://{self.postgres_user}:{pwd}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    def get_safe_postgres_url(self) -> str:
        """Return connection URL with password securely masked for safe logging and status reporting."""
        raw_url = self.get_postgres_connection_url()
        return re.sub(r"(://[^:]+):([^@]+)@", r"\1:***@", raw_url)

    @property
    def allowed_sql_verbs(self) -> Set[str]:
        """Allowed starting verbs for safe read-only queries."""
        return {"SELECT", "WITH", "EXPLAIN"}

    @property
    def forbidden_sql_keywords(self) -> Set[str]:
        """Destructive and administrative SQL operations that must be strictly rejected."""
        return {
            "DROP",
            "TRUNCATE",
            "ALTER",
            "DELETE",
            "UPDATE",
            "INSERT",
            "GRANT",
            "REVOKE",
            "CREATE",
            "REPLACE",
            "EXECUTE",
            "VACUUM",
            "REINDEX",
            "SET",
            "COPY",
        }

    def validate_sql_safety(self, sql: str) -> None:
        """Validate that a SQL statement is strictly read-only and safe for MCP execution.

        Raises:
            MCPSecurityError: If the SQL contains destructive, administrative, or chained statements.
        """
        if not sql or not sql.strip():
            raise MCPSecurityError("SQL query cannot be empty.")

        cleaned = sql.strip()

        # Check for multi-statement execution via semicolons
        # Allow trailing semicolon, but disallow statements chained with semicolon
        without_trailing_semi = re.sub(r";\s*$", "", cleaned)
        if ";" in without_trailing_semi:
            raise MCPSecurityError(
                "Multi-statement SQL queries separated by semicolons are strictly forbidden in MCP."
            )

        # Normalize whitespace and tokenize
        tokens = re.findall(r"[A-Za-z_]+", cleaned.upper())
        if not tokens:
            raise MCPSecurityError("Invalid SQL query: No recognizable tokens found.")

        first_verb = tokens[0]
        if first_verb not in self.allowed_sql_verbs:
            raise MCPSecurityError(
                f"SQL statement must begin with an allowed read-only verb ({', '.join(sorted(self.allowed_sql_verbs))}). "
                f"Attempted: '{first_verb}'"
            )

        # Inspect for forbidden destructive keywords in any token position
        # (e.g. WITH ... DELETE FROM ... or SELECT ... INTO ...)
        for token in tokens:
            if token in self.forbidden_sql_keywords:
                raise MCPSecurityError(
                    f"Destructive or administrative SQL keyword '{token}' is strictly forbidden in MCP queries."
                )

    def resolve_path(self, path_str: str) -> Path:
        """Resolve a path relative to backend directory or workspace root if not absolute."""
        p = Path(path_str)
        if p.is_absolute():
            return p
        # Check relative to backend/
        backend_p = (ENV_FILE_PATH.parent / p).resolve()
        if backend_p.exists():
            return backend_p
        # Check relative to workspace root (parent of backend)
        root_p = (ENV_FILE_PATH.parent.parent / p).resolve()
        if root_p.exists():
            return root_p
        # Check relative to cwd
        cwd_p = Path(p).resolve()
        if cwd_p.exists():
            return cwd_p
        return backend_p

    def get_oauth_path(self) -> Path:
        """Return the resolved Path to the Google OAuth keys file."""
        return self.resolve_path(self.gdrive_oauth_path)

    def get_credentials_path(self) -> Path:
        """Return the resolved Path to the authorized Google Drive credentials file."""
        return self.resolve_path(self.gdrive_credentials_path)

    def get_google_auth_status(self) -> dict:
        """Check whether Google OAuth client secrets and user credentials files exist."""
        oauth_path = self.get_oauth_path()
        creds_path = self.get_credentials_path()

        return {
            "oauth_keys_configured": oauth_path.exists() and oauth_path.is_file(),
            "oauth_keys_path": str(oauth_path),
            "credentials_authorized": creds_path.exists() and creds_path.is_file(),
            "credentials_path": str(creds_path),
        }

    def __repr__(self) -> str:
        return (
            f"<MCPSettings(postgres={self.get_safe_postgres_url()}, "
            f"gdrive_oauth_configured={Path(self.gdrive_oauth_path).exists()})>"
        )

    def __str__(self) -> str:
        return self.__repr__()


@lru_cache()
def get_mcp_settings() -> MCPSettings:
    """Return singleton cached instance of MCPSettings."""
    return MCPSettings()
