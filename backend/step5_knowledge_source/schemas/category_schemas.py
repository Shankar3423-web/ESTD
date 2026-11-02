"""Pydantic schemas for Category reference data."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    """Canonical category response representation."""

    id: int = Field(..., description="Unique category primary key ID")
    code: Optional[str] = Field(default=None, description="Category code, e.g. ENT, TECH")
    name: str = Field(..., description="Canonical category display name")
    slug: str = Field(..., description="URL-safe slug")
    is_active: bool = Field(default=True, description="Whether category is active")
    created_at: datetime = Field(..., description="Timestamp when category was created")

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    """API response container for category listing."""

    status: str = Field(default="success")
    total: int = Field(..., description="Total categories available")
    items: List[CategoryResponse] = Field(..., description="List of category records")


class SubcategoryResponse(BaseModel):
    """Canonical subcategory response representation."""

    id: int = Field(..., description="Unique subcategory primary key ID")
    category_id: int = Field(..., description="Foreign key to parent category")
    code: str = Field(..., description="Canonical unique code, e.g. ENT_MOVIES")
    name: str = Field(..., description="Display name")
    slug: str = Field(..., description="URL slug")
    description: Optional[str] = Field(default=None, description="Scope description")
    is_active: bool = Field(default=True, description="Whether subcategory is active")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class SubcategoryListResponse(BaseModel):
    """API response container for subcategory listing."""

    status: str = Field(default="success")
    total: int = Field(..., description="Total subcategories available")
    items: List[SubcategoryResponse] = Field(..., description="List of subcategory records")
