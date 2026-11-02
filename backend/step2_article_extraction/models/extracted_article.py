"""ExtractedArticle model preserving Step 1 metadata with Step 2 extracted content."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.utils.datetime_utils import get_utc_now_iso
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models.extraction_enums import (
    ExtractionMethod,
    ExtractionStatus,
)


class ExtractedArticle(BaseModel):
    """Normalized article representation containing Step 1 metadata and Step 2 extracted content."""

    # Preserved Step 1 Fields
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
        description="Original article URL from Step 1 collection.",
        min_length=1,
    )
    source_name: Optional[str] = Field(
        default=None,
        description="Name of the publisher or source publication.",
    )
    source_type: str = Field(
        ...,
        description="Provider identifier from Step 1, e.g. 'gnews', 'newsdata', 'rss'.",
    )
    author: Optional[str] = Field(
        default=None,
        description="Author or creator of the article, if identified.",
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
        ...,
        description="ISO 8601 UTC timestamp of when ESTD collected the article in Step 1.",
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

    # Step 2 Specific Fields
    content: Optional[str] = Field(
        default=None,
        description="Full extracted article body text.",
    )
    canonical_url: Optional[str] = Field(
        default=None,
        description="Canonical URL discovered during extraction (or original URL fallback).",
    )
    extraction_status: ExtractionStatus = Field(
        ...,
        description="Outcome status of the Step 2 extraction process.",
    )
    extraction_method: Optional[ExtractionMethod] = Field(
        default=None,
        description="Method used to obtain the content (existing_source_content or article_web_extraction).",
    )
    extracted_at: str = Field(
        default_factory=get_utc_now_iso,
        description="ISO 8601 UTC timestamp of when Step 2 processed the article.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Descriptive failure details if extraction failed; None on success.",
    )

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "example": {
                "title": "OpenAI announces new reasoning model",
                "description": "A new generation of reasoning capabilities...",
                "url": "https://example.com/news/openai-model",
                "source_name": "TechCrunch",
                "source_type": "gnews",
                "author": "Jane Doe",
                "published_at": "2026-09-30T10:00:00Z",
                "category": "Artificial Intelligence",
                "image_url": "https://example.com/images/model.jpg",
                "collected_at": "2026-09-30T10:15:00Z",
                "content": "Full article text detailing the reasoning architecture...",
                "canonical_url": "https://techcrunch.com/2026/09/30/openai-model",
                "extraction_status": "EXTRACTED",
                "extraction_method": "article_web_extraction",
                "extracted_at": "2026-09-30T10:15:05Z",
                "error_message": None,
            }
        },
    }

    @classmethod
    def from_existing_content(
        cls,
        news_item: NewsItem,
        content: str,
    ) -> "ExtractedArticle":
        """Factory for when the incoming NewsItem already contained sufficient content."""
        return cls(
            title=news_item.title,
            description=news_item.description,
            url=news_item.url,
            source_name=news_item.source_name,
            source_type=news_item.source_type,
            author=news_item.author,
            published_at=news_item.published_at,
            category=news_item.category,
            subcategory=getattr(news_item, "subcategory", None),
            original_source_category=getattr(news_item, "original_source_category", None),
            language=getattr(news_item, "language", "en"),
            region=getattr(news_item, "region", None),
            image_url=news_item.image_url,
            collected_at=news_item.collected_at,
            content=content,
            canonical_url=news_item.url,
            extraction_status=ExtractionStatus.CONTENT_ALREADY_AVAILABLE,
            extraction_method=ExtractionMethod.EXISTING_SOURCE_CONTENT,
            error_message=None,
        )

    @classmethod
    def from_extracted(
        cls,
        news_item: NewsItem,
        content: str,
        title: Optional[str] = None,
        canonical_url: Optional[str] = None,
        author: Optional[str] = None,
        published_at: Optional[str] = None,
        image_url: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> "ExtractedArticle":
        """Factory for successfully fetched and extracted web content."""
        return cls(
            title=title or news_item.title,
            description=news_item.description,
            url=news_item.url,
            source_name=source_name or news_item.source_name,
            source_type=news_item.source_type,
            author=author or news_item.author,
            published_at=published_at or news_item.published_at,
            category=news_item.category,
            subcategory=getattr(news_item, "subcategory", None),
            original_source_category=getattr(news_item, "original_source_category", None),
            language=getattr(news_item, "language", "en"),
            region=getattr(news_item, "region", None),
            image_url=image_url or news_item.image_url,
            collected_at=news_item.collected_at,
            content=content,
            canonical_url=canonical_url or news_item.url,
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
            error_message=None,
        )

    @classmethod
    def from_failure(
        cls,
        news_item: NewsItem,
        error_message: str,
    ) -> "ExtractedArticle":
        """Factory for handling extraction failure gracefully without data loss."""
        return cls(
            title=news_item.title,
            description=news_item.description,
            url=news_item.url,
            source_name=news_item.source_name,
            source_type=news_item.source_type,
            author=news_item.author,
            published_at=news_item.published_at,
            category=news_item.category,
            subcategory=getattr(news_item, "subcategory", None),
            original_source_category=getattr(news_item, "original_source_category", None),
            language=getattr(news_item, "language", "en"),
            region=getattr(news_item, "region", None),
            image_url=news_item.image_url,
            collected_at=news_item.collected_at,
            content=None,
            canonical_url=news_item.url,
            extraction_status=ExtractionStatus.EXTRACTION_FAILED,
            extraction_method=None,
            error_message=error_message,
        )
