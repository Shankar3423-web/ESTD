"""Pydantic schemas for Step 3 Cleaning API requests and responses."""
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle


class CleaningRequest(BaseModel):
    """Request payload for cleaning a single extracted article."""

    article: ExtractedArticle = Field(
        ...,
        description="The ExtractedArticle model produced by Step 2.",
    )


class BatchCleaningRequest(BaseModel):
    """Request payload for cleaning a batch of extracted articles."""

    articles: List[ExtractedArticle] = Field(
        ...,
        description="List of ExtractedArticle objects produced by Step 2.",
        min_length=1,
    )


class SingleCleaningResponse(BaseModel):
    """Standardized response payload for single article cleaning."""

    status: str = Field(..., description="Status string: 'success' or 'failed'.")
    data: CleanedArticle = Field(..., description="The CleanedArticle result.")


class BatchCleaningResponse(BaseModel):
    """Standardized response payload for batch article cleaning."""

    status: str = Field(..., description="Status string: 'success'.")
    count: int = Field(..., description="Total count of processed articles.")
    items: List[CleanedArticle] = Field(
        default_factory=list,
        description="List of CleanedArticle results.",
    )
