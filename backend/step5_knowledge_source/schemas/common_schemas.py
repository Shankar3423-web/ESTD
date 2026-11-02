"""Common schemas for pagination and database health status."""
from typing import Optional
from pydantic import BaseModel, Field


class PaginationMetadata(BaseModel):
    """Metadata describing a paginated collection of results."""

    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total matching items across all pages")
    total_pages: int = Field(..., ge=0, description="Total pages available")
    has_next: bool = Field(..., description="True if next page exists")
    has_prev: bool = Field(..., description="True if previous page exists")


class DatabaseHealthResponse(BaseModel):
    """Response payload for knowledge source database health check."""

    status: str = Field(default="healthy", description="Health status string")
    database: str = Field(default="connected", description="Database connection state")
    database_name: str = Field(..., description="Target database name, e.g. estd_knowledge")
    server_version: Optional[str] = Field(default=None, description="PostgreSQL server version")
