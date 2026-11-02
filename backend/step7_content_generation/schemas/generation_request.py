"""Request and response schemas for Step 7 content generation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.schemas.generated_news import GeneratedNews


class ArticleGenerationRequest(BaseModel):
    """Request to generate ESTD news from an existing knowledge source article via MCP."""

    article_id: int = Field(
        ...,
        gt=0,
        description="Unique identifier of the news article stored in PostgreSQL.",
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional editorial focus or guidance (must not contradict source facts).",
    )


class DirectGenerationRequest(BaseModel):
    """Request to generate news directly from a provided structured article payload."""

    title: str = Field(..., min_length=3, max_length=500, description="Source article title")
    content: str = Field(..., min_length=50, description="Cleaned article body text")
    category: ESTDCategory = Field(..., description="Canonical category")
    subcategory: Optional[str] = Field(default=None, description="ESTD subcategory")
    source_name: Optional[str] = Field(default="Unknown", description="Source publication name")
    source_url: str = Field(..., min_length=5, description="Source URL")
    author: Optional[str] = Field(default=None, description="Article author")
    published_at: Optional[datetime] = Field(default=None, description="Original publication timestamp")
    description: Optional[str] = Field(default=None, description="Article synopsis/description")
    custom_instructions: Optional[str] = Field(default=None, max_length=500, description="Editorial guidance")


class GenerationResponse(BaseModel):
    """Unified API response envelope for content generation requests."""

    success: bool
    article_id: Optional[int] = None
    data: Optional[GeneratedNews] = None
    error: Optional[str] = None
    generation_time_ms: float
    model_used: str


class EligibleArticleSummary(BaseModel):
    """Summary of an article in PostgreSQL eligible for AI generation."""

    id: int
    title: str
    category: str
    subcategory: Optional[str] = None
    source_name: Optional[str]
    content_length: int
    published_at: Optional[str]
    url: str
