"""FastAPI routes for Step 4 Duplicate Detection & Deduplication API."""
from typing import List, Union
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database.connection.session import get_db
from backend.database.repositories.duplicate_index_repository import (
    DuplicateIndexRepository,
)
from backend.step1_source_collection.models.response_models import ErrorResponse
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step4_duplicate_detection.schemas.duplicate_request import (
    BatchDuplicateCheckRequest,
    DuplicateCheckRequest,
)
from backend.step4_duplicate_detection.schemas.duplicate_response import (
    BatchDuplicateResponse,
    DuplicateIndexStatsResponse,
    SingleDuplicateResponse,
)
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)

router = APIRouter(
    prefix="/api/v1/duplicate-detection",
    tags=["Step 4 - Duplicate Detection"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)


def get_duplicate_service() -> DuplicateDetectionService:
    """Dependency provider for DuplicateDetectionService."""
    return DuplicateDetectionService()


@router.post(
    "/check",
    response_model=SingleDuplicateResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate duplicate status of a single cleaned article",
    description=(
        "Evaluates a CleanedArticle produced by Step 3 through the 3-stage deduplication pipeline: "
        "1) URL normalization and matching, 2) SHA-256 exact content hash, and 3) TF-IDF cosine similarity. "
        "Returns classification as UNIQUE or DUPLICATE with full audit reason and metadata."
    ),
)
async def check_article_endpoint(
    payload: Union[DuplicateCheckRequest, CleanedArticle],
    service: DuplicateDetectionService = Depends(get_duplicate_service),
    db: Session = Depends(get_db),
) -> SingleDuplicateResponse:
    """Evaluate duplicate status of a single cleaned article."""
    article = payload.article if isinstance(payload, DuplicateCheckRequest) else payload
    result = service.check_article(article, session=db)
    return SingleDuplicateResponse(
        status="success",
        data=result,
    )


@router.post(
    "/check-batch",
    response_model=BatchDuplicateResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate duplicate status of a batch of cleaned articles",
    description=(
        "Evaluates a batch of CleanedArticles. Performs cross-batch duplicate detection (identifying duplicates "
        "within the submitted batch) as well as historical duplicate detection against the persistent database index."
    ),
)
async def check_batch_endpoint(
    payload: Union[BatchDuplicateCheckRequest, List[CleanedArticle]],
    service: DuplicateDetectionService = Depends(get_duplicate_service),
    db: Session = Depends(get_db),
) -> BatchDuplicateResponse:
    """Evaluate duplicate status of a batch of cleaned articles."""
    articles = payload.articles if isinstance(payload, BatchDuplicateCheckRequest) else payload
    results = service.check_batch(articles, session=db)

    unique_count = sum(1 for r in results if r.decision.status.value == "UNIQUE")
    dup_count = sum(1 for r in results if r.decision.status.value == "DUPLICATE")

    return BatchDuplicateResponse(
        status="success",
        total_count=len(results),
        unique_count=unique_count,
        duplicate_count=dup_count,
        items=results,
    )


@router.get(
    "/stats",
    response_model=DuplicateIndexStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve duplicate index statistics",
    description="Returns total records, unique articles, and recorded duplicates in the historical index.",
)
async def get_index_stats_endpoint(
    db: Session = Depends(get_db),
) -> DuplicateIndexStatsResponse:
    """Retrieve historical duplicate index statistics."""
    total = DuplicateIndexRepository.count_total(db)
    unique = DuplicateIndexRepository.count_unique(db)
    duplicates = DuplicateIndexRepository.count_duplicates(db)
    return DuplicateIndexStatsResponse(
        status="success",
        total_indexed=total,
        unique_articles=unique,
        duplicate_records=duplicates,
    )
