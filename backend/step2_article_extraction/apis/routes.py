"""FastAPI routes for Step 2 Article Extraction API."""
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.common.logging.logger import logger
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.models.response_models import ErrorResponse
from backend.step2_article_extraction.exceptions.extraction_exceptions import (
    InvalidURLError,
    SSRFSecurityError,
)
from backend.step2_article_extraction.fetchers.url_validator import URLValidator
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step2_article_extraction.schemas.api_schemas import (
    BatchExtractionRequest,
    BatchExtractionResponse,
    ExtractionRequest,
    SingleExtractionResponse,
)
from backend.step2_article_extraction.services.extraction_service import (
    ExtractionService,
)

router = APIRouter(
    prefix="/api/v1/article-extraction",
    tags=["Step 2 - Article Extraction"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)


def get_extraction_service() -> ExtractionService:
    """Dependency injection provider for ExtractionService."""
    return ExtractionService()


@router.post(
    "/extract",
    response_model=SingleExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract article content from a NewsItem",
    description=(
        "Takes a normalized NewsItem from Step 1. Evaluates content sufficiency: if sufficient "
        "content exists, avoids external fetch; otherwise fetches the article URL and extracts "
        "body and metadata."
    ),
)
async def extract_article_endpoint(
    payload: Union[ExtractionRequest, NewsItem],
    service: ExtractionService = Depends(get_extraction_service),
) -> SingleExtractionResponse:
    """Extract full article content for a single news item."""
    # Support both direct NewsItem and wrapped {"news_item": {...}} payload
    news_item = payload.news_item if isinstance(payload, ExtractionRequest) else payload

    # Validate URL upfront to produce controlled 400 for malformed/invalid URLs
    validator = URLValidator()
    validator.validate_url(news_item.url)

    result: ExtractedArticle = await service.extract_article(news_item)
    return SingleExtractionResponse(
        status="success" if result.extraction_status != "EXTRACTION_FAILED" else "failed",
        data=result,
    )


@router.post(
    "/extract-batch",
    response_model=BatchExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract article content for a batch of NewsItems",
    description="Batch extracts content for multiple NewsItems with per-article failure isolation.",
)
async def extract_batch_endpoint(
    payload: Union[BatchExtractionRequest, List[NewsItem]],
    service: ExtractionService = Depends(get_extraction_service),
) -> BatchExtractionResponse:
    """Extract content for a batch of news items."""
    items = payload.news_items if isinstance(payload, BatchExtractionRequest) else payload

    results = await service.extract_batch(items)
    return BatchExtractionResponse(
        status="success",
        count=len(results),
        items=results,
    )
