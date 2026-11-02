"""Pydantic request schemas for Step 4 Duplicate Detection API."""
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle


class DuplicateCheckRequest(BaseModel):
    """Request payload for evaluating duplicate status of a single CleanedArticle."""

    article: CleanedArticle = Field(
        ...,
        description="The CleanedArticle produced by Step 3 Content Cleaning.",
    )


class BatchDuplicateCheckRequest(BaseModel):
    """Request payload for evaluating duplicate status of a batch of CleanedArticles."""

    articles: List[CleanedArticle] = Field(
        ...,
        description="List of CleanedArticle models produced by Step 3.",
        min_length=1,
    )
