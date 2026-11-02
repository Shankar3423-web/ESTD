"""Pydantic schemas for Step 8 document records and output responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Step8DocumentRecordSchema(BaseModel):
    """Schema representing a tracked Google Document artifact record."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Primary key record ID in database")
    article_id: int = Field(..., description="Associated knowledge base article ID")
    google_document_id: Optional[str] = Field(default=None, description="Google Document ID")
    google_document_url: Optional[str] = Field(default=None, description="Web URL to Google Document")
    google_drive_root_folder_id: Optional[str] = Field(default=None, description="ESTD CONTENT folder ID")
    google_drive_category_folder_id: Optional[str] = Field(default=None, description="Category folder ID")
    google_drive_subcategory_folder_id: Optional[str] = Field(default=None, description="Subcategory folder ID")
    category: str = Field(..., description="Assigned category")
    subcategory: Optional[str] = Field(default=None, description="Assigned subcategory")
    document_title: str = Field(..., description="Document title")
    status: str = Field(..., description="Execution status: PENDING, CREATED, or FAILED")
    attempt_count: int = Field(default=0, description="Processing attempt count")
    last_error: Optional[str] = Field(default=None, description="Last recorded error if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class Step8DocumentResponse(BaseModel):
    """API response envelope for document creation and status retrieval."""

    success: bool
    status: str = Field(..., description="CREATED, PENDING, or FAILED")
    article_id: int
    data: Optional[Step8DocumentRecordSchema] = None
    is_duplicate_prevented: bool = Field(default=False, description="True if existing document was returned without recreating")
    error: Optional[str] = None
    processing_time_ms: float = Field(default=0.0)
