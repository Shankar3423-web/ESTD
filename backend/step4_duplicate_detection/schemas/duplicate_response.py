"""Pydantic response schemas for Step 4 Duplicate Detection API."""
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step4_duplicate_detection.models.duplicate_record import DuplicateDecision


class DuplicateCheckResult(BaseModel):
    """Container pairing an evaluated CleanedArticle with its DuplicateDecision."""

    status: str = Field(
        ...,
        description="Lowercase status indicator: 'unique' or 'duplicate'.",
    )
    decision: DuplicateDecision = Field(
        ...,
        description="Comprehensive audit decision containing reason, matched ID, similarity score.",
    )
    article: CleanedArticle = Field(
        ...,
        description="The CleanedArticle that was evaluated.",
    )


class SingleDuplicateResponse(BaseModel):
    """Standardized response payload for a single article duplicate evaluation."""

    status: str = Field(
        ...,
        description="Overall API status: 'success'.",
    )
    data: DuplicateCheckResult = Field(
        ...,
        description="The duplicate detection result for the submitted article.",
    )


class BatchDuplicateResponse(BaseModel):
    """Standardized response payload for a batch duplicate evaluation."""

    status: str = Field(
        default="success",
        description="Overall API status: 'success'.",
    )
    total_count: int = Field(
        ...,
        description="Total number of articles evaluated in this batch.",
    )
    unique_count: int = Field(
        ...,
        description="Count of articles classified as UNIQUE (safe for Step 5 Knowledge Source).",
    )
    duplicate_count: int = Field(
        ...,
        description="Count of articles classified as DUPLICATE.",
    )
    items: List[DuplicateCheckResult] = Field(
        default_factory=list,
        description="List of individual evaluation results in identical order to input.",
    )


class DuplicateIndexStatsResponse(BaseModel):
    """Response payload for index inspection and health statistics."""

    status: str = Field(default="success")
    total_indexed: int = Field(..., description="Total records in duplicate index.")
    unique_articles: int = Field(..., description="Unique articles indexed.")
    duplicate_records: int = Field(..., description="Duplicate records indexed.")
