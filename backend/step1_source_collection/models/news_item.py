"""Standardized NewsItem model for ESTD Step 1 Source Collection."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.utils.datetime_utils import get_utc_now_iso


class NewsItem(BaseModel):
    """Common normalized news item representation across all providers."""

    title: str = Field(
        ...,
        description="The headline or title of the news article.",
        min_length=1,
    )
    description: Optional[str] = Field(
        default=None,
        description="A short snippet, synopsis, or description of the article.",
    )
    url: str = Field(
        ...,
        description="Canonical URL to the full original news article.",
        min_length=1,
    )
    source_name: Optional[str] = Field(
        default=None,
        description="Name of the publisher or source publication.",
    )
    source_type: str = Field(
        ...,
        description="Provider identifier, e.g. 'gnews' or 'newsdata'.",
    )
    author: Optional[str] = Field(
        default=None,
        description="Author or creator of the article, if provided.",
    )
    published_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 UTC timestamp of publication.",
    )
    category: str = Field(
        ...,
        description="Normalized ESTD category name.",
    )
    subcategory: Optional[str] = Field(
        default=None,
        description="Normalized ESTD subcategory name.",
    )
    original_source_category: Optional[str] = Field(
        default=None,
        description="Raw category reported by upstream source before normalization.",
    )
    language: Optional[str] = Field(
        default="en",
        description="ISO 639-1 language code of article content.",
    )
    region: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 alpha-2 region or country code.",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL to the primary article image or thumbnail.",
    )
    collected_at: str = Field(
        default_factory=get_utc_now_iso,
        description="ISO 8601 UTC timestamp of when ESTD collected the article.",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Resolve and validate category against canonical ESTD categories."""
        from backend.common.constants.categories import resolve_canonical_category
        canonical = resolve_canonical_category(v)
        if not canonical:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        return canonical

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "example": {
                "title": "OpenAI announces new reasoning model",
                "description": "A new generation of reasoning capabilities...",
                "url": "https://example.com/news/openai-model",
                "source_name": "TechCrunch",
                "source_type": "gnews",
                "author": None,
                "published_at": "2026-09-30T10:00:00Z",
                "category": "Artificial Intelligence",
                "image_url": "https://example.com/images/model.jpg",
                "collected_at": "2026-09-30T10:15:00Z",
            }
        },
    }
