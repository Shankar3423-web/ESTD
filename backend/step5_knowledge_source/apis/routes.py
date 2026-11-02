"""FastAPI routes for Step 5 Knowledge Source API."""
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.exceptions.custom_exceptions import InvalidCategoryError
from backend.database.connection.session import get_db
from backend.step4_duplicate_detection.schemas.duplicate_response import DuplicateCheckResult
from backend.step5_knowledge_source.exceptions import (
    ArticleDuplicateError,
    ArticleNotFoundError,
    DatabaseConnectionError,
    InvalidArticleDataError,
)
from backend.step5_knowledge_source.schemas.article_schemas import (
    ArticleCreateRequest,
    ArticleListPayload,
    ArticleListResponse,
    ArticleResponse,
    DeleteArticleResponse,
    SingleArticleResponse,
)
from backend.step5_knowledge_source.schemas.category_schemas import (
    CategoryListResponse,
    CategoryResponse,
    SubcategoryListResponse,
    SubcategoryResponse,
)
from backend.step5_knowledge_source.schemas.common_schemas import (
    DatabaseHealthResponse,
    PaginationMetadata,
)
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService

router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["Step 5 - Knowledge Source"],
)

service = KnowledgeSourceService()


@router.get(
    "/health",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Knowledge source database health check",
)
def get_health():
    """Verify live PostgreSQL connectivity and report knowledge database health."""
    health_info = service.check_health()
    return DatabaseHealthResponse(
        status=health_info.get("status", "healthy"),
        database=health_info.get("database", "connected"),
        database_name=health_info.get("database_name", "estd_knowledge"),
        server_version=health_info.get("server_version"),
    )


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List canonical reference categories",
)
def list_categories(session: Session = Depends(get_db)):
    """Retrieve all 5 canonical categories seeded in PostgreSQL."""
    categories = service.list_categories(session=session)
    items = [CategoryResponse.model_validate(cat) for cat in categories]
    return CategoryListResponse(
        status="success",
        total=len(items),
        items=items,
    )


@router.get(
    "/subcategories",
    response_model=SubcategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List canonical reference subcategories",
)
def list_subcategories(
    category: Optional[str] = Query(default=None, description="Optional parent category filter"),
    session: Session = Depends(get_db),
):
    """Retrieve canonical subcategories, optionally filtered by parent category."""
    subcategories = service.list_subcategories(category=category, session=session)
    items = [SubcategoryResponse.model_validate(sub) for sub in subcategories]
    return SubcategoryListResponse(
        status="success",
        total=len(items),
        items=items,
    )


@router.post(
    "/articles",
    response_model=SingleArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Persist a unique article into the knowledge source",
)
def store_article(
    payload: Dict[str, Any],
    session: Session = Depends(get_db),
):
    """Persist a unique article into PostgreSQL knowledge source.
    
    Accepts either:
    1. A Step 4 DuplicateCheckResult: {'status': 'unique', 'decision': {...}, 'article': {...}}
    2. An ArticleCreateRequest: {'title': '...', 'content': '...', 'url': '...', 'category': '...'}
    """
    # Check if payload matches Step 4 DuplicateCheckResult structure
    if "decision" in payload and "article" in payload:
        try:
            check_result = DuplicateCheckResult.model_validate(payload)
            article = service.persist_from_step4(check_result, session=session)
            return SingleArticleResponse(
                status="success",
                data=ArticleResponse.model_validate(article),
            )
        except (ArticleDuplicateError, InvalidCategoryError, InvalidArticleDataError):
            raise
        except Exception as exc:
            raise InvalidArticleDataError(f"Malformed Step 4 duplicate check payload: {exc}")

    # Otherwise validate as standard ArticleCreateRequest
    try:
        request_obj = ArticleCreateRequest.model_validate(payload)
    except InvalidCategoryError:
        raise
    except Exception as exc:
        raise InvalidArticleDataError(f"Validation error for article creation: {exc}")

    article = service.create_article(request_obj, session=session)
    return SingleArticleResponse(
        status="success",
        data=ArticleResponse.model_validate(article),
    )


@router.get(
    "/articles/{article_id}",
    response_model=SingleArticleResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an article by its ID",
)
def get_article(
    article_id: int,
    session: Session = Depends(get_db),
):
    """Retrieve a single article from the knowledge source by its primary key ID."""
    article = service.get_article_by_id(article_id, session=session)
    return SingleArticleResponse(
        status="success",
        data=ArticleResponse.model_validate(article),
    )


@router.get(
    "/articles",
    response_model=ArticleListResponse,
    status_code=status.HTTP_200_OK,
    summary="List, filter, and paginate articles from knowledge source",
)
def list_articles(
    category: Optional[str] = Query(default=None, description="Filter by canonical category"),
    subcategory: Optional[str] = Query(default=None, description="Filter by subcategory"),
    source: Optional[str] = Query(default=None, description="Filter by publisher name substring"),
    source_type: Optional[str] = Query(default=None, description="Filter by source type (gnews, newsdata, rss)"),
    start_date: Optional[str] = Query(default=None, description="Filter by published_at on or after ISO date"),
    end_date: Optional[str] = Query(default=None, description="Filter by published_at on or before ISO date"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)"),
    session: Session = Depends(get_db),
):
    """Retrieve filtered, paginated articles stored in the PostgreSQL knowledge source."""
    articles, pagination = service.list_articles(
        category=category,
        subcategory=subcategory,
        source=source,
        source_type=source_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        session=session,
    )

    items = [ArticleResponse.model_validate(art) for art in articles]
    return ArticleListResponse(
        status="success",
        data=ArticleListPayload(
            items=items,
            pagination=pagination,
        ),
    )


@router.delete(
    "/articles/{article_id}",
    response_model=DeleteArticleResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an article from the knowledge source",
)
def delete_article(
    article_id: int,
    session: Session = Depends(get_db),
):
    """Delete an article by ID from the knowledge source."""
    service.delete_article(article_id, session=session)
    return DeleteArticleResponse(
        status="success",
        message=f"Article {article_id} deleted successfully.",
        article_id=article_id,
    )
