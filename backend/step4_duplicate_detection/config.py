"""Configuration settings for Step 4 Duplicate Detection & Deduplication."""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from backend.common.config.settings import get_settings
from backend.step4_duplicate_detection.exceptions.duplicate_exceptions import (
    DuplicateConfigurationError,
)


class DuplicateDetectionConfig(BaseSettings):
    """Configuration thresholds, toggles, and vectorizer parameters for Step 4."""

    # Similarity Threshold
    similarity_threshold: float = Field(
        default=0.82,
        description="Cosine similarity cutoff threshold for duplicate classification.",
        ge=0.0,
        le=1.0,
    )

    # Database
    database_url: Optional[str] = Field(
        default=None,
        description="SQLAlchemy database connection URL.",
    )

    # Search Horizons
    historical_candidate_limit: int = Field(
        default=200,
        description="Maximum recent candidate articles pulled from historical index for TF-IDF comparison.",
        ge=1,
        le=5000,
    )

    # Pipeline Stage Toggles
    enable_url_matching: bool = Field(
        default=True,
        description="Enable/disable Stage 1 URL normalization and exact match check.",
    )
    enable_exact_content_matching: bool = Field(
        default=True,
        description="Enable/disable Stage 2 SHA-256 exact content hash check.",
    )
    enable_similarity_matching: bool = Field(
        default=True,
        description="Enable/disable Stage 3 TF-IDF cosine similarity check.",
    )
    enable_batch_detection: bool = Field(
        default=True,
        description="Enable/disable checking against articles in the current batch.",
    )
    enable_historical_detection: bool = Field(
        default=True,
        description="Enable/disable checking against historical index in the database.",
    )

    # Persistence Toggles
    persist_unique_articles: bool = Field(
        default=True,
        description="Automatically index unique articles to database for future historical deduplication.",
    )
    persist_duplicate_records: bool = Field(
        default=True,
        description="Persist duplicate article decisions to database for audit and traceability.",
    )

    # TF-IDF Vectorizer Parameters
    ngram_range_min: int = Field(default=1, ge=1, le=3)
    ngram_range_max: int = Field(default=1, ge=1, le=4)
    max_features: int = Field(default=5000, ge=100, le=50000)
    stop_words: Optional[str] = Field(default="english")

    model_config = {
        "env_prefix": "DEDUPLICATION_",
        "extra": "ignore",
    }

    @field_validator("similarity_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise DuplicateConfigurationError(f"similarity_threshold must be between 0.0 and 1.0, got {v}")
        return v

    def get_effective_database_url(self) -> str:
        """Resolve effective database URL from Step 4 config or global settings."""
        if self.database_url and self.database_url.strip():
            return self.database_url.strip()
        global_settings = get_settings()
        return getattr(global_settings, "database_url", None) or "postgresql://postgres:1234@localhost:5432/estd"


duplicate_config = DuplicateDetectionConfig()
