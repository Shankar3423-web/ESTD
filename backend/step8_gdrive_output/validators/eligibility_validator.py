"""Eligibility and contract validation for Step 8 output pipeline."""
from typing import Any, Dict, Optional

from backend.common.constants.categories import ESTDCategory
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step8_gdrive_output.config.gdrive_settings import FINAL_CATEGORIES
from backend.step8_gdrive_output.exceptions import (
    ArticleIneligibleForOutputError,
    InvalidStep8CategoryError,
    Step8ValidationError,
)


def validate_category(category_val: Any) -> str:
    """Validate that the category strictly matches or resolves to one of the 5 canonical ESTD categories."""
    if not category_val:
        raise InvalidStep8CategoryError("Empty category")

    cat_str = category_val.value if isinstance(category_val, ESTDCategory) else str(category_val).strip()

    from backend.common.constants.categories import resolve_canonical_category
    resolved = resolve_canonical_category(cat_str)
    if not resolved:
        raise InvalidStep8CategoryError(cat_str)
    return resolved


def validate_step8_eligibility(
    news: GeneratedNews,
    article_id: Optional[int] = None,
) -> None:
    """Validate that a GeneratedNews article meets all Step 8 quality, attribution, and safety criteria."""
    if not news:
        raise ArticleIneligibleForOutputError("GeneratedNews payload is missing.", article_id=article_id)

    # Validate headline
    if not news.title or not news.title.strip():
        raise ArticleIneligibleForOutputError("Article title is empty.", article_id=article_id)
    if len(news.title.strip()) < 5:
        raise ArticleIneligibleForOutputError("Article title is too short (< 5 chars).", article_id=article_id)

    # Validate content
    if not news.content or not news.content.strip():
        raise ArticleIneligibleForOutputError("Article content is empty.", article_id=article_id)
    if len(news.content.strip()) < 50:
        raise ArticleIneligibleForOutputError("Article content is too short (< 50 chars).", article_id=article_id)

    # Validate category
    validate_category(news.category)

    # Validate provenance & traceability
    if not news.source_name or not news.source_name.strip():
        raise ArticleIneligibleForOutputError("Original source publisher name is missing.", article_id=article_id)

    if not news.source_url or not str(news.source_url).strip():
        raise ArticleIneligibleForOutputError("Original source article URL is missing.", article_id=article_id)
