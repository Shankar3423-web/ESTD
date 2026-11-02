"""CleanedArticle model preserving Step 1 & Step 2 provenance with Step 3 cleaned content."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.utils.datetime_utils import get_utc_now_iso
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus


class CleanedArticle(BaseModel):
    """Canonical Step 3 cleaned and normalized article representation."""

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

    # Preserved Step 2 Fields
    canonical_url: Optional[str] = Field(
        default=None,
        description="Canonical URL discovered during extraction (or original URL fallback).",
    )
    extraction_status: Optional[str] = Field(
        default=None,
        description="Outcome status of the Step 2 extraction process.",
    )
    extraction_method: Optional[str] = Field(
        default=None,
        description="Method used by Step 2 to obtain the content.",
    )
    extracted_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 UTC timestamp of when Step 2 processed the article.",
    )

    # Step 3 Specific Fields
    original_content: Optional[str] = Field(
        default=None,
        description="Original extracted content from Step 2 preserved for audit and debugging.",
    )
    cleaned_content: Optional[str] = Field(
        default=None,
        description="Cleaned, normalized, and validated article body text.",
    )
    content: Optional[str] = Field(
        default=None,
        description="Primary content field containing cleaned content for downstream pipeline stages.",
    )
    cleaning_status: CleaningStatus = Field(
        ...,
        description="Outcome status of Step 3 content cleaning.",
    )
    cleaned_at: str = Field(
        default_factory=get_utc_now_iso,
        description="ISO 8601 UTC timestamp of when Step 3 cleaned the article.",
    )
    original_content_length: int = Field(
        default=0,
        description="Character count of the original extracted content.",
    )
    cleaned_content_length: int = Field(
        default=0,
        description="Character count of the cleaned article content.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Failure details if cleaning failed; None on success.",
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
                "author": "Jane Doe",
                "published_at": "2026-09-30T10:00:00Z",
                "category": "Artificial Intelligence",
                "image_url": "https://example.com/images/model.jpg",
                "collected_at": "2026-09-30T10:15:00Z",
                "canonical_url": "https://techcrunch.com/2026/09/30/openai-model",
                "extraction_status": "EXTRACTED",
                "extraction_method": "article_web_extraction",
                "extracted_at": "2026-09-30T10:15:05Z",
                "original_content": "Full article text with <p>markup</p> and ads...",
                "cleaned_content": "Full article text with markup and clean paragraphs...",
                "content": "Full article text with markup and clean paragraphs...",
                "cleaning_status": "SUCCESS",
                "cleaned_at": "2026-09-30T10:15:07Z",
                "original_content_length": 1500,
                "cleaned_content_length": 1420,
                "error_message": None,
            }
        },
    }

    @classmethod
    def from_extracted_article(
        cls,
        extracted: ExtractedArticle,
        cleaned_text: str,
    ) -> "CleanedArticle":
        """Factory for successfully cleaned and normalized article content."""
        orig_content = extracted.content or ""
        return cls(
            title=extracted.title,
            description=extracted.description,
            url=extracted.url,
            source_name=extracted.source_name,
            source_type=extracted.source_type,
            author=extracted.author,
            published_at=extracted.published_at,
            category=extracted.category,
            subcategory=getattr(extracted, "subcategory", None),
            original_source_category=getattr(extracted, "original_source_category", None),
            language=getattr(extracted, "language", "en"),
            region=getattr(extracted, "region", None),
            image_url=extracted.image_url,
            collected_at=extracted.collected_at,
            canonical_url=extracted.canonical_url,
            extraction_status=str(extracted.extraction_status.value)
            if hasattr(extracted.extraction_status, "value")
            else str(extracted.extraction_status)
            if extracted.extraction_status
            else None,
            extraction_method=str(extracted.extraction_method.value)
            if hasattr(extracted.extraction_method, "value")
            else str(extracted.extraction_method)
            if extracted.extraction_method
            else None,
            extracted_at=extracted.extracted_at,
            original_content=extracted.content,
            cleaned_content=cleaned_text,
            content=cleaned_text,
            cleaning_status=CleaningStatus.SUCCESS,
            original_content_length=len(orig_content),
            cleaned_content_length=len(cleaned_text),
            error_message=None,
        )

    @classmethod
    def from_failure(
        cls,
        extracted: ExtractedArticle,
        error_message: str,
    ) -> "CleanedArticle":
        """Factory for handling cleaning failure safely without pipeline crash."""
        orig_content = extracted.content or ""
        return cls(
            title=extracted.title,
            description=extracted.description,
            url=extracted.url,
            source_name=extracted.source_name,
            source_type=extracted.source_type,
            author=extracted.author,
            published_at=extracted.published_at,
            category=extracted.category,
            subcategory=getattr(extracted, "subcategory", None),
            original_source_category=getattr(extracted, "original_source_category", None),
            language=getattr(extracted, "language", "en"),
            region=getattr(extracted, "region", None),
            image_url=extracted.image_url,
            collected_at=extracted.collected_at,
            canonical_url=extracted.canonical_url,
            extraction_status=str(extracted.extraction_status.value)
            if hasattr(extracted.extraction_status, "value")
            else str(extracted.extraction_status)
            if extracted.extraction_status
            else None,
            extraction_method=str(extracted.extraction_method.value)
            if hasattr(extracted.extraction_method, "value")
            else str(extracted.extraction_method)
            if extracted.extraction_method
            else None,
            extracted_at=extracted.extracted_at,
            original_content=extracted.content,
            cleaned_content=None,
            content=None,
            cleaning_status=CleaningStatus.CLEANING_FAILED,
            original_content_length=len(orig_content),
            cleaned_content_length=0,
            error_message=error_message,
        )
