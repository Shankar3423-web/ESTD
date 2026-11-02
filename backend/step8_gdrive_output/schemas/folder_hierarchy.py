"""Pydantic schema for Google Drive folder hierarchy representation."""
from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class FolderItemSchema(BaseModel):
    """Details of an individual Google Drive folder."""

    name: str
    folder_id: str
    parent_id: Optional[str] = None
    web_view_link: Optional[str] = None


class FolderHierarchySchema(BaseModel):
    """Structure representing the ESTD CONTENT folder and its 5 category subfolders."""

    root_folder: FolderItemSchema = Field(..., description="Root ESTD CONTENT folder")
    category_folders: Dict[str, FolderItemSchema] = Field(
        ...,
        description="Map of category name to its corresponding Google Drive folder details",
    )
    subcategory_folders: Optional[Dict[str, Dict[str, FolderItemSchema]]] = Field(
        default=None,
        description="Nested map of category name to subcategory name to folder details",
    )
    is_fully_initialized: bool = Field(
        ...,
        description="True if root and all 5 category folders exist",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of discovery/initialization",
    )
