"""Pydantic schemas for Step 2 extraction API requests and responses."""
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle


class ExtractionRequest(BaseModel):
    """Request payload for extracting a single news item."""

    news_item: NewsItem = Field(..., description="The normalized NewsItem from Step 1.")


class BatchExtractionRequest(BaseModel):
    """Request payload for extracting multiple news items."""

    news_items: List[NewsItem] = Field(
        ...,
        description="List of normalized NewsItems from Step 1.",
        min_length=1,
    )


class SingleExtractionResponse(BaseModel):
    """Standardized response payload for single article extraction."""

    status: str = Field(..., description="Status string: 'success' or 'failed'.")
    data: ExtractedArticle = Field(..., description="The ExtractedArticle result.")


class BatchExtractionResponse(BaseModel):
    """Standardized response payload for batch article extraction."""

    status: str = Field(..., description="Status string: 'success'.")
    count: int = Field(..., description="Total count of processed articles.")
    items: List[ExtractedArticle] = Field(
        default_factory=list,
        description="List of extracted article results.",
    )
