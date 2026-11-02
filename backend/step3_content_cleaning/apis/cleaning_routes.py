"""FastAPI routes for Step 3 Content Cleaning & Normalization API."""
from typing import List, Union
from fastapi import APIRouter, Depends, status

from backend.step1_source_collection.models.response_models import ErrorResponse
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.schemas.cleaning_schemas import (
    BatchCleaningRequest,
    BatchCleaningResponse,
    CleaningRequest,
    SingleCleaningResponse,
)
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)

router = APIRouter(
    prefix="/api/v1/content-cleaning",
    tags=["Step 3 - Content Cleaning"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)


def get_cleaning_service() -> ContentCleaningService:
    """Dependency injection provider for ContentCleaningService."""
    return ContentCleaningService()


@router.post(
    "/clean",
    response_model=SingleCleaningResponse,
    status_code=status.HTTP_200_OK,
    summary="Clean and normalize an extracted article",
    description=(
        "Takes an ExtractedArticle from Step 2. Cleans HTML markup, strips boilerplate "
        "advertisements, newsletter notices, and social sharing widgets, normalizes Unicode and whitespace, "
        "and deduplicates repeated extraction artifacts into a CleanedArticle."
    ),
)
async def clean_article_endpoint(
    payload: Union[CleaningRequest, ExtractedArticle],
    service: ContentCleaningService = Depends(get_cleaning_service),
) -> SingleCleaningResponse:
    """Clean and normalize a single extracted article."""
    article = payload.article if isinstance(payload, CleaningRequest) else payload

    result: CleanedArticle = service.clean_article(article)
    return SingleCleaningResponse(
        status="success" if result.cleaning_status == CleaningStatus.SUCCESS else "failed",
        data=result,
    )


@router.post(
    "/clean-batch",
    response_model=BatchCleaningResponse,
    status_code=status.HTTP_200_OK,
    summary="Clean and normalize a batch of extracted articles",
    description="Batch cleans and normalizes content for multiple ExtractedArticles with per-article failure isolation.",
)
async def clean_batch_endpoint(
    payload: Union[BatchCleaningRequest, List[ExtractedArticle]],
    service: ContentCleaningService = Depends(get_cleaning_service),
) -> BatchCleaningResponse:
    """Clean and normalize a batch of extracted articles."""
    articles = payload.articles if isinstance(payload, BatchCleaningRequest) else payload

    results = service.clean_batch(articles)
    return BatchCleaningResponse(
        status="success",
        count=len(results),
        items=results,
    )
