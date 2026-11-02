"""Configuration settings for ESTD Step 2 Article Extraction."""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.common.config.settings import ENV_FILE_PATH


class ExtractionConfig(BaseSettings):
    """Configuration specific to article fetching, extraction, and sufficiency determination."""

    # HTTP Fetching settings
    fetch_timeout_seconds: float = Field(
        default=10.0,
        alias="EXTRACTION_FETCH_TIMEOUT_SECONDS",
        description="Timeout in seconds for external article web page requests.",
    )
    max_redirects: int = Field(
        default=5,
        alias="EXTRACTION_MAX_REDIRECTS",
        description="Maximum HTTP redirects to follow.",
    )
    user_agent: str = Field(
        default="ESTD-ArticleExtractor/1.0 (Mozilla/5.0 compatible; +https://estd.ai/bot)",
        alias="EXTRACTION_USER_AGENT",
        description="User-Agent header sent during article web page retrieval.",
    )
    max_response_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5 MB
        alias="EXTRACTION_MAX_RESPONSE_BYTES",
        description="Maximum allowed webpage payload size in bytes to prevent DoS.",
    )

    # Content sufficiency thresholds
    # Reason: News snippets are typically 50-150 characters (1-2 sentences).
    # Full articles or substantive content contain sustained prose of at least 250 characters
    # and at least 40 words without truncation indicators.
    min_content_chars: int = Field(
        default=250,
        alias="EXTRACTION_MIN_CONTENT_CHARS",
        description="Minimum character length for text to be considered a sufficient article body.",
    )
    min_content_words: int = Field(
        default=40,
        alias="EXTRACTION_MIN_CONTENT_WORDS",
        description="Minimum word count for text to be considered a sufficient article body.",
    )

    # SSRF Protection
    allow_private_ips: bool = Field(
        default=False,
        alias="EXTRACTION_ALLOW_PRIVATE_IPS",
        description="Whether to permit fetching from private/loopback IP addresses (default False for security).",
    )

    prefer_scrape_for_news_feeds: bool = Field(
        default=False,
        alias="EXTRACTION_PREFER_SCRAPE_FOR_FEEDS",
        description="Whether to prioritize scraping webpage content over brief feed summaries.",
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Module-level default configuration
extraction_config = ExtractionConfig()
