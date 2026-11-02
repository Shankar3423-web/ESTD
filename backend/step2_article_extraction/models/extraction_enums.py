"""Enums defining Step 2 extraction status and methods."""
from enum import Enum


class ExtractionStatus(str, Enum):
    """Status indicating the outcome of Step 2 article extraction."""

    CONTENT_ALREADY_AVAILABLE = "CONTENT_ALREADY_AVAILABLE"
    EXTRACTED = "EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class ExtractionMethod(str, Enum):
    """Method utilized to obtain the article content."""

    EXISTING_SOURCE_CONTENT = "existing_source_content"
    ARTICLE_WEB_EXTRACTION = "article_web_extraction"
