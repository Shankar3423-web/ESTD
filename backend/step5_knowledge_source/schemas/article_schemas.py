"""Pydantic schemas for Step 5 Knowledge Source NewsArticle API and operations."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.exceptions.custom_exceptions import InvalidCategoryError
from backend.step5_knowledge_source.schemas.common_schemas import PaginationMetadata


class ArticleCreateRequest(BaseModel):
    """Schema for persisting a new article into the knowledge source."""

    title: str = Field(..., min_length=1, description="Headline or title of the article")
    description: Optional[str] = Field(default=None, description="Short snippet or synopsis")
    content: str = Field(..., min_length=1, description="Cleaned, normalized article content")
    url: str = Field(..., min_length=1, description="Original article URL")
    source_name: Optional[str] = Field(default=None, description="Publisher or feed name")
    source_type: str = Field(default="custom", description="Provider identifier (gnews, newsdata, rss, custom)")
    author: Optional[str] = Field(default=None, description="Author if known")
    published_at: Optional[str] = Field(default=None, description="ISO 8601 publication timestamp")
    category: str = Field(..., description="One of the 5 canonical ESTD categories")
    subcategory: Optional[str] = Field(default=None, description="ESTD subcategory name")
    original_source_category: Optional[str] = Field(default=None, description="Raw source category")
    language: Optional[str] = Field(default="en", description="ISO 639-1 language code")
    region: Optional[str] = Field(default=None, description="ISO 3166-1 alpha-2 region code")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    collected_at: Optional[str] = Field(default=None, description="ISO 8601 collection timestamp")
    normalized_url: Optional[str] = Field(default=None, description="Pre-computed normalized URL")
    content_hash: Optional[str] = Field(default=None, description="Pre-computed SHA-256 content hash")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is one of the 5 canonical categories (supporting canonical resolution)."""
        from backend.common.constants.categories import resolve_canonical_category
        try:
            return resolve_canonical_category(v)
        except Exception:
            raise InvalidCategoryError(v)

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "example": {
                "title": "Autonomous Rovers Map Deep Oceanic Trenches",
                "description": "Unmanned submersibles discover new hydrothermal vents.",
                "content": "Deep sea robotic rovers have completed mapping previously unreachable tectonic fault zones...",
                "url": "https://example.com/ocean-rovers",
                "source_name": "Nature Journal",
                "source_type": "rss",
                "author": "Dr. Jane Doe",
                "published_at": "2026-10-01T08:30:00Z",
                "category": "Developments",
                "subcategory": "Science & Fundamental Discovery",
                "image_url": "https://example.com/images/ocean.jpg",
            }
        },
    }


class ArticleResponse(BaseModel):
    """Schema for returning a persisted knowledge source article."""

    id: int = Field(..., description="Unique knowledge source article ID")
    title: str = Field(..., description="Headline of article")
    description: Optional[str] = Field(default=None, description="Short snippet or synopsis")
    content: str = Field(..., description="Cleaned article content")
    url: str = Field(..., description="Original article URL")
    normalized_url: str = Field(..., description="Normalized canonical URL")
    content_hash: str = Field(..., description="SHA-256 fingerprint hex digest")
    source_name: Optional[str] = Field(default=None, description="Source publisher name")
    source_type: str = Field(..., description="Provider identifier")
    author: Optional[str] = Field(default=None, description="Author")
    published_at: Optional[datetime] = Field(default=None, description="UTC publication timestamp")
    category: str = Field(..., description="Canonical category name")
    category_id: int = Field(..., description="Foreign key to categories table")
    subcategory: Optional[str] = Field(default=None, description="Canonical subcategory name")
    subcategory_id: Optional[int] = Field(default=None, description="Foreign key to subcategories table")
    original_source_category: Optional[str] = Field(default=None, description="Raw source category")
    language: Optional[str] = Field(default="en", description="Language code")
    region: Optional[str] = Field(default=None, description="Region code")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    collected_at: datetime = Field(..., description="UTC collection timestamp")
    created_at: datetime = Field(..., description="UTC persistence timestamp")
    updated_at: datetime = Field(..., description="UTC last updated timestamp")

    model_config = ConfigDict(from_attributes=True)


class ArticleListPayload(BaseModel):
    """Payload containing list of articles and pagination metadata."""

    items: List[ArticleResponse] = Field(default_factory=list, description="List of articles")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")


class ArticleListResponse(BaseModel):
    """Standardized API response for paginated article queries."""

    status: str = Field(default="success")
    data: ArticleListPayload = Field(..., description="Paginated articles payload")


class SingleArticleResponse(BaseModel):
    """Standardized API response for single article retrieval or creation."""

    status: str = Field(default="success")
    data: ArticleResponse = Field(..., description="Article record")


class DeleteArticleResponse(BaseModel):
    """Response payload for article deletion."""

    status: str = Field(default="success")
    message: str = Field(..., description="Deletion status message")
    article_id: int = Field(..., description="ID of deleted article")
