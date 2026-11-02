"""Request schemas for Step 8 document processing."""
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.step7_content_generation.schemas.generated_news import GeneratedNews


class ProcessArticleRequest(BaseModel):
    """Request to process a single article by ID through Step 8."""

    article_id: int = Field(..., gt=0, description="Article ID in PostgreSQL knowledge base")
    force_recreate: bool = Field(
        default=False,
        description="If True, bypasses idempotency cache and recreates document (use with caution)",
    )


class ProcessDirectRequest(BaseModel):
    """Request to output a directly supplied validated GeneratedNews payload into Google Docs."""

    article_id: Optional[int] = Field(default=None, description="Optional article ID to link for persistence")
    news: GeneratedNews = Field(..., description="Validated GeneratedNews output from Step 7")


class BatchProcessRequest(BaseModel):
    """Request to process multiple approved articles."""

    article_ids: Optional[List[int]] = Field(default=None, description="Explicit list of article IDs to process")
    category: Optional[str] = Field(default=None, description="Process all eligible articles in category")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of articles to process")


class BatchProcessSummaryItem(BaseModel):
    """Summary of a single article result in a batch processing run."""

    article_id: int
    success: bool
    status: str
    document_id: Optional[str] = None
    document_url: Optional[str] = None
    error: Optional[str] = None


class BatchProcessResponse(BaseModel):
    """Result envelope for batch document creation operations."""

    total_requested: int
    successful_count: int
    failed_count: int
    skipped_count: int
    items: List[BatchProcessSummaryItem]
