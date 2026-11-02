"""Configuration settings for Step 7 Gemini AI Content Generation."""
from functools import lru_cache
import re
from typing import Any, Dict, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.common.config.settings import ENV_FILE_PATH
from backend.step7_content_generation.exceptions import GeminiConfigurationError


class GeminiSettings(BaseSettings):
    """Centralized configuration for Google Gemini AI generation."""

    # Gemini API Key loaded from backend/.env
    gemini_api_key: Optional[SecretStr] = Field(default=None, alias="GEMINI_API_KEY")

    # Selected Model Name (defaulting to verified gemini-2.5-flash)
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # Temperature for generation (lower temperature = higher factual adherence)
    gemini_temperature: float = Field(
        default=0.2,
        alias="GEMINI_TEMPERATURE",
        ge=0.0,
        le=2.0,
    )

    # Maximum token count for output
    gemini_max_output_tokens: int = Field(
        default=8192,
        alias="GEMINI_MAX_OUTPUT_TOKENS",
        ge=512,
        le=8192,
    )

    # Maximum client retries for transient failures
    gemini_max_retries: int = Field(
        default=2,
        alias="GEMINI_MAX_RETRIES",
        ge=0,
        le=5,
    )

    # Timeout in seconds for API calls
    gemini_timeout_seconds: float = Field(
        default=30.0,
        alias="GEMINI_TIMEOUT_SECONDS",
        gt=0.0,
        le=120.0,
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_gemini_api_key(self) -> str:
        """Return raw Gemini API key or raise GeminiConfigurationError if absent.
        
        Note: The returned secret must never be logged or serialized.
        """
        if not self.gemini_api_key or not self.gemini_api_key.get_secret_value().strip():
            raise GeminiConfigurationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env"
            )
        return self.gemini_api_key.get_secret_value().strip()

    def has_api_key(self) -> bool:
        """Check if an API key is configured without exposing it."""
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())

    def mask_secret(self, text: str) -> str:
        """Sanitize any occurrence of the API key from a string or log message."""
        if not text:
            return ""
        if self.gemini_api_key:
            raw_key = self.gemini_api_key.get_secret_value().strip()
            if raw_key and len(raw_key) > 4:
                text = text.replace(raw_key, "[REDACTED_API_KEY]")
        # Generic API key pattern matching
        text = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)
        return text

    def get_safe_config_summary(self) -> Dict[str, Any]:
        """Return non-sensitive configuration summary suitable for health checks and logs."""
        return {
            "api_key_configured": self.has_api_key(),
            "model": self.gemini_model,
            "temperature": self.gemini_temperature,
            "max_retries": self.gemini_max_retries,
            "timeout_seconds": self.gemini_timeout_seconds,
            "max_output_tokens": self.gemini_max_output_tokens,
        }


@lru_cache()
def get_gemini_settings() -> GeminiSettings:
    """Return cached singleton instance of GeminiSettings."""
    return GeminiSettings()
