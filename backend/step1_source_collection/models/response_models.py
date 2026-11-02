"""Response models for ESTD Step 1 API collection endpoints."""
from typing import List
from pydantic import BaseModel, Field

from backend.step1_source_collection.models.news_item import NewsItem


class CollectionResponse(BaseModel):
    """Standardized response payload for news collection endpoints."""

    provider: str = Field(..., description="Provider that collected the news (e.g., 'gnews', 'newsdata').")
    category: str = Field(..., description="Requested ESTD category.")
    count: int = Field(..., description="Number of news items returned.")
    items: List[NewsItem] = Field(default_factory=list, description="List of normalized NewsItem objects.")


class ErrorDetail(BaseModel):
    """Standardized error detail."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error description.")


class ErrorResponse(BaseModel):
    """Standardized API error response format."""

    error: ErrorDetail = Field(..., description="Error detail container.")
