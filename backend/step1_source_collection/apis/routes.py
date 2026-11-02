"""FastAPI routes for Step 1 Source Collection APIs."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from backend.common.constants.categories import ESTDCategory, VALID_CATEGORIES
from backend.common.exceptions.custom_exceptions import InvalidCategoryError
from backend.step1_source_collection.models.response_models import (
    CollectionResponse,
    ErrorResponse,
)
from backend.step1_source_collection.services.source_collection_service import (
    SourceCollectionService,
)

router = APIRouter(
    prefix="/api/v1/source-collection",
    tags=["Step 1 - Source Collection"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
        status.HTTP_504_GATEWAY_TIMEOUT: {"model": ErrorResponse},
    },
)


def get_service() -> SourceCollectionService:
    """Dependency injection provider for SourceCollectionService."""
    return SourceCollectionService()


def validate_category_query(category: str) -> str:
    """Validate requested category query parameter against valid ESTD categories."""
    from backend.common.constants.categories import resolve_canonical_category
    resolved = resolve_canonical_category(category)
    if resolved:
        return resolved

    raise InvalidCategoryError(category)


@router.get(
    "/gnews",
    response_model=CollectionResponse,
    summary="Collect news from GNews API",
    description="Fetch and normalize news articles from GNews for a supported ESTD category.",
)
async def get_gnews_news(
    category: str = Query(
        ...,
        description=f"ESTD category. Must be one of: {', '.join(VALID_CATEGORIES)}",
        examples=["Technology"],
    ),
    limit: Optional[int] = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of articles to return (1-50).",
    ),
    service: SourceCollectionService = Depends(get_service),
) -> CollectionResponse:
    """Collect news from GNews."""
    normalized_category = validate_category_query(category)
    return await service.collect_from_gnews(category=normalized_category, limit=limit or 10)


@router.get(
    "/newsdata",
    response_model=CollectionResponse,
    summary="Collect news from NewsData.io API",
    description="Fetch and normalize news articles from NewsData.io for a supported ESTD category.",
)
async def get_newsdata_news(
    category: str = Query(
        ...,
        description=f"ESTD category. Must be one of: {', '.join(VALID_CATEGORIES)}",
        examples=["Science"],
    ),
    limit: Optional[int] = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of articles to return (1-50).",
    ),
    service: SourceCollectionService = Depends(get_service),
) -> CollectionResponse:
    """Collect news from NewsData.io."""
    normalized_category = validate_category_query(category)
    return await service.collect_from_newsdata(category=normalized_category, limit=limit or 10)


@router.get(
    "/rss",
    response_model=CollectionResponse,
    summary="Collect news from curated RSS/Atom feeds",
    description="Fetch and normalize news articles from verified public RSS/Atom feeds for a supported ESTD category.",
)
async def get_rss_news(
    category: Optional[str] = Query(
        default=None,
        description=f"ESTD category. Must be one of: {', '.join(VALID_CATEGORIES)}. If omitted, collects from all categories.",
        examples=["Technology"],
    ),
    limit: Optional[int] = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of articles to return (1-50).",
    ),
    service: SourceCollectionService = Depends(get_service),
) -> CollectionResponse:
    """Collect news from RSS feeds."""
    if category is not None:
        normalized_category = validate_category_query(category)
        return await service.collect_from_rss(category=normalized_category, limit=limit or 10)

    # When category is omitted, collect from all categories
    all_responses = await service.rss_service.collect_all(limit_per_category=limit or 10)
    all_items = []
    for resp in all_responses:
        all_items.extend(resp.items)

    safe_limit = limit or 10
    clamped_items = all_items[:safe_limit]

    return CollectionResponse(
        provider="rss",
        category="All",
        count=len(clamped_items),
        items=clamped_items,
    )

