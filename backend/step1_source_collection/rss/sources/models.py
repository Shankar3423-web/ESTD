"""Data models for RSS Source configuration and registry."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from backend.common.constants.categories import (
    VALID_CATEGORIES,
    resolve_canonical_category,
    resolve_subcategory,
)


class RSSSource(BaseModel):
    """Configuration schema for a single RSS/Atom feed source."""

    source_id: str = Field(
        ...,
        description="Unique identifier for the feed (e.g., 'variety_film').",
        min_length=1,
    )
    source_name: str = Field(
        ...,
        description="Human-readable publication or source name (e.g., 'Variety').",
        min_length=1,
    )
    publisher: str = Field(
        ...,
        description="Publishing entity or parent organization (e.g., 'Penske Media Corporation').",
        min_length=1,
    )
    feed_url: str = Field(
        ...,
        description="Fully-qualified HTTP/HTTPS URL of the RSS or Atom feed.",
        min_length=1,
    )
    category: str = Field(
        ...,
        description="Associated ESTD standardized parent category name.",
    )
    subcategory: Optional[str] = Field(
        default=None,
        description="Optional canonical subcategory name if feed is topic-specific.",
    )
    language: str = Field(
        default="en",
        description="ISO language code of feed content (e.g. 'en', 'te', 'hi').",
    )
    region: str = Field(
        default="international",
        description="Target geographic scope: 'international', 'national', 'regional'.",
    )
    access_method: str = Field(
        default="rss",
        description="Access protocol: 'rss', 'atom', 'api', 'official_newsroom'.",
    )
    validation_status: str = Field(
        default="VERIFIED",
        description="Verification state: 'VERIFIED', 'PENDING_VALIDATION', 'DISABLED'.",
    )
    poll_interval_seconds: int = Field(
        default=300,
        description="Recommended collection poll interval in seconds.",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this feed source is active for collection.",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category matches one of the 5 canonical ESTD categories."""
        canonical = resolve_canonical_category(v)
        if not canonical:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        return canonical

    @field_validator("subcategory")
    @classmethod
    def validate_subcategory_field(cls, v: Optional[str], info) -> Optional[str]:
        """Validate subcategory if provided."""
        if not v:
            return None
        cat = info.data.get("category")
        if cat:
            resolved = resolve_subcategory(v, cat)
            if resolved:
                return resolved
        return v

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "example": {
                "source_id": "variety_entertainment",
                "source_name": "Variety",
                "publisher": "Penske Media",
                "feed_url": "https://variety.com/feed/",
                "category": "Entertainment",
                "subcategory": "Movies & Cinema",
                "language": "en",
                "region": "international",
                "enabled": True,
            }
        },
    }

