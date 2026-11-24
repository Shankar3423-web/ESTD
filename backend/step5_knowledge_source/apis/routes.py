"""FastAPI routes for Step 5 Knowledge Source API."""
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.common.auth.security import verify_admin_api_key
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

# High-speed in-memory caches to eliminate transatlantic database round trips
_ARTICLE_RESPONSE_CACHE: Dict[int, Tuple[float, SingleArticleResponse]] = {}
_ARTICLE_CACHE_TTL = 300.0  # 5 minutes
_LIST_RESPONSE_CACHE: Dict[str, Tuple[float, ArticleListResponse]] = {}
_LIST_CACHE_TTL = 60.0  # 60 seconds

def _invalidate_knowledge_cache(article_id: Optional[int] = None):
    """Invalidate cached articles and list payloads when content updates."""
    if article_id and article_id in _ARTICLE_RESPONSE_CACHE:
        _ARTICLE_RESPONSE_CACHE.pop(article_id, None)
    _LIST_RESPONSE_CACHE.clear()


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
    dependencies=[Depends(verify_admin_api_key)],
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
    _invalidate_knowledge_cache()
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
    now = time.time()
    if article_id in _ARTICLE_RESPONSE_CACHE:
        cached_time, cached_res = _ARTICLE_RESPONSE_CACHE[article_id]
        if now - cached_time < _ARTICLE_CACHE_TTL:
            return cached_res

    article = service.get_article_by_id(article_id, session=session)
    response_obj = SingleArticleResponse(
        status="success",
        data=ArticleResponse.model_validate(article),
    )
    _ARTICLE_RESPONSE_CACHE[article_id] = (now, response_obj)
    return response_obj


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
    now = time.time()
    cache_key = f"{category}:{subcategory}:{source}:{source_type}:{start_date}:{end_date}:{page}:{page_size}"
    if cache_key in _LIST_RESPONSE_CACHE:
        cached_time, cached_res = _LIST_RESPONSE_CACHE[cache_key]
        if now - cached_time < _LIST_CACHE_TTL:
            return cached_res

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
    response_obj = ArticleListResponse(
        status="success",
        data=ArticleListPayload(
            items=items,
            pagination=pagination,
        ),
    )
    _LIST_RESPONSE_CACHE[cache_key] = (now, response_obj)

    # Pre-seed individual articles so clicking any article from this list loads in <1ms
    for art in articles:
        if art.id:
            _ARTICLE_RESPONSE_CACHE[art.id] = (
                now,
                SingleArticleResponse(
                    status="success",
                    data=ArticleResponse.model_validate(art),
                ),
            )

    return response_obj


@router.delete(
    "/articles/{article_id}",
    response_model=DeleteArticleResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an article from the knowledge source",
    dependencies=[Depends(verify_admin_api_key)],
)
def delete_article(
    article_id: int,
    session: Session = Depends(get_db),
):
    """Delete an article by ID from the knowledge source."""
    service.delete_article(article_id, session=session)
    _invalidate_knowledge_cache(article_id)
    return DeleteArticleResponse(
        status="success",
        message=f"Article {article_id} deleted successfully.",
        article_id=article_id,
    )
