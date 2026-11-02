"""FastAPI router exposing Step 7 Gemini AI Content Generation endpoints."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.common.logging.logger import logger
from backend.step7_content_generation.client.gemini_client import GeminiClient
from backend.step7_content_generation.config.gemini_settings import (
    GeminiSettings,
    get_gemini_settings,
)
from backend.step7_content_generation.exceptions import (
    ArticleIneligibleError,
    GeminiAuthenticationError,
    GeminiConfigurationError,
    GeminiModelError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GenerationException,
    GenerationValidationError,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.schemas.generation_request import (
    ArticleGenerationRequest,
    DirectGenerationRequest,
    EligibleArticleSummary,
    GenerationResponse,
)
from backend.step7_content_generation.services.generation_service import (
    GenerationService,
)
from backend.step7_content_generation.services.mcp_generation_service import (
    MCPGenerationService,
)

router = APIRouter(prefix="/step7", tags=["Step 7 — Gemini Content Generation"])


def get_mcp_gen_service() -> MCPGenerationService:
    """Dependency provider for MCPGenerationService singleton."""
    return MCPGenerationService()


def get_gen_service() -> GenerationService:
    """Dependency provider for direct GenerationService singleton."""
    return GenerationService()


def get_client() -> GeminiClient:
    """Dependency provider for GeminiClient."""
    return GeminiClient()


@router.post(
    "/generate",
    response_model=GenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate news from existing ESTD knowledge source article via MCP",
)
def generate_article_news(
    request: ArticleGenerationRequest,
    service: MCPGenerationService = Depends(get_mcp_gen_service),
) -> GenerationResponse:
    """Retrieve an article from the PostgreSQL knowledge source using MCP and generate an ESTD news report."""
    try:
        return service.generate_from_mcp_article(request)
    except ArticleIneligibleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        )
    except GenerationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message},
        )
    except GeminiAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message},
        )
    except GeminiRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": exc.code, "message": exc.message},
        )
    except GeminiTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": exc.code, "message": exc.message},
        )
    except GenerationException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": exc.code, "message": exc.message},
        )


@router.post(
    "/generate/direct",
    response_model=GeneratedNews,
    status_code=status.HTTP_200_OK,
    summary="Directly generate ESTD news from provided article data",
)
def generate_direct_news(
    request: DirectGenerationRequest,
    service: GenerationService = Depends(get_gen_service),
) -> GeneratedNews:
    """Transform directly submitted article content into a validated GeneratedNews article."""
    try:
        return service.generate_news(
            title=request.title,
            content=request.content,
            category=request.category.value,
            source_name=request.source_name,
            source_url=request.source_url,
            author=request.author,
            published_at=str(request.published_at) if request.published_at else None,
            description=request.description,
            custom_instructions=request.custom_instructions,
        )
    except GenerationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message},
        )
    except GeminiAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message},
        )
    except GeminiRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": exc.code, "message": exc.message},
        )
    except GeminiTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": exc.code, "message": exc.message},
        )
    except GenerationException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": exc.code, "message": exc.message},
        )


@router.get(
    "/eligible-articles",
    response_model=List[EligibleArticleSummary],
    summary="List articles in knowledge source eligible for AI generation via MCP",
)
def list_eligible_articles(
    limit: int = Query(default=20, ge=1, le=100),
    service: MCPGenerationService = Depends(get_mcp_gen_service),
) -> List[EligibleArticleSummary]:
    """Query PostgreSQL knowledge base via MCP to discover eligible articles."""
    return service.list_eligible_articles(limit=limit)


@router.get(
    "/health",
    summary="Check Gemini AI configuration and API connectivity",
)
def check_gemini_health(
    client: GeminiClient = Depends(get_client),
    settings: GeminiSettings = Depends(get_gemini_settings),
) -> Dict[str, Any]:
    """Verify Gemini configuration and test minimal ping connectivity without exposing secrets."""
    config_summary = settings.get_safe_config_summary()
    try:
        connectivity = client.test_connectivity()
        return {
            "status": "HEALTHY",
            "configuration": config_summary,
            "connectivity": connectivity,
        }
    except Exception as exc:
        safe_msg = settings.mask_secret(str(exc))
        return {
            "status": "DEGRADED",
            "configuration": config_summary,
            "error": safe_msg,
        }
