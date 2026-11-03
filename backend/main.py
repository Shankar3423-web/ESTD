"""ESTD Step 1 Source Collection Application Entry Point."""
import sys
from pathlib import Path

# Ensure project root (ESTD) and backend are in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.common.exceptions.custom_exceptions import (
    ConfigurationError,
    ESTDException,
    ExternalAPIError,
    InvalidCategoryError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderServerError,
    ProviderTimeoutError,
    RSSEmptyFeedError,
    RSSException,
    RSSFetchError,
    RSSInvalidFeedError,
    RSSParseError,
    RSSSourceNotFoundError,
    RSSTimeoutError,
)
from backend.common.logging.logger import logger
from backend.step1_source_collection.apis.routes import router as source_collection_router
from backend.step2_article_extraction.apis.routes import router as article_extraction_router
from backend.step2_article_extraction.exceptions import (
    InvalidURLError,
    SSRFSecurityError,
)
from backend.step3_content_cleaning.apis.cleaning_routes import router as content_cleaning_router
from backend.step3_content_cleaning.exceptions import (
    CleaningException,
    CleaningValidationError,
    ContentCleaningFailedError,
    InvalidArticleContentError,
)
from contextlib import asynccontextmanager

from backend.database.connection.session import init_db
from backend.step4_duplicate_detection.api.duplicate_routes import router as duplicate_detection_router
from backend.step4_duplicate_detection.exceptions import (
    DuplicateConfigurationError,
    DuplicateDetectionException,
    DuplicateIndexDatabaseError,
    InvalidArticleForDeduplicationError,
    SimilarityCalculationError,
)
from backend.step5_knowledge_source.apis.routes import router as knowledge_source_router
from backend.step5_knowledge_source.exceptions import (
    ArticleDuplicateError,
    ArticleNotFoundError,
    CategoryNotFoundError,
    DatabaseConnectionError,
    InvalidArticleDataError,
    KnowledgeSourceException,
)
from backend.step6_mcp.apis.routes import router as mcp_router
from backend.step6_mcp.exceptions import (
    MCPAuthenticationError,
    MCPConfigurationError,
    MCPConnectionError,
    MCPException,
    MCPSecurityError,
    MCPTimeoutError,
    MCPToolExecutionError,
)
from backend.step7_content_generation.api.generation_routes import router as generation_router
from backend.step8_gdrive_output.api.routes import router as gdrive_output_router
from backend.pipeline.router import router as pipeline_router
from backend.step9_video_rail.apis.video_routes import router as video_router


# Auto-run schema checks including likes_count and article_likes
try:
    init_db()
except Exception as _init_exc:
    logger.warning(f"Immediate schema initialization notice: {_init_exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager ensuring database schema and reference data exist upon server startup."""
    try:
        init_db()
        from backend.database.connection.session import get_db_session
        from backend.database.repositories.category_repository import CategoryRepository
        with get_db_session() as session:
            CategoryRepository.seed_categories(session)
    except Exception as exc:
        logger.warning(f"Database initialization notice on startup: {exc}")
    yield


app = FastAPI(
    title="ESTD - Steps 1–5 News Intelligence Engine",
    description="API for collecting, extracting, normalizing, deduplicating, and persisting news article knowledge.",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS middleware for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://frontend-zeta-amber.vercel.app",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://frontend-.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Centralized Error Handlers (Consistent Error Response Format)
# ============================================================================

@app.exception_handler(InvalidCategoryError)
async def invalid_category_handler(request: Request, exc: InvalidCategoryError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    logger.error(f"Configuration error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ProviderAuthenticationError)
async def provider_auth_error_handler(request: Request, exc: ProviderAuthenticationError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ProviderRateLimitError)
async def provider_rate_limit_handler(request: Request, exc: ProviderRateLimitError):
    headers = {}
    if exc.retry_after is not None:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ProviderTimeoutError)
async def provider_timeout_handler(request: Request, exc: ProviderTimeoutError):
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ProviderConnectionError)
async def provider_connection_error_handler(request: Request, exc: ProviderConnectionError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ProviderServerError)
async def provider_server_error_handler(request: Request, exc: ProviderServerError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ProviderResponseError)
async def provider_response_error_handler(request: Request, exc: ProviderResponseError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ExternalAPIError)
async def external_api_error_handler(request: Request, exc: ExternalAPIError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RSSException)
async def rss_exception_handler(request: Request, exc: RSSException):
    status_code = status.HTTP_502_BAD_GATEWAY
    if isinstance(exc, RSSTimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    elif isinstance(exc, RSSSourceNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(InvalidURLError)
async def invalid_url_handler(request: Request, exc: InvalidURLError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(SSRFSecurityError)
async def ssrf_security_handler(request: Request, exc: SSRFSecurityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(InvalidArticleContentError)
async def invalid_article_content_handler(request: Request, exc: InvalidArticleContentError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(CleaningValidationError)
async def cleaning_validation_error_handler(request: Request, exc: CleaningValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ContentCleaningFailedError)
async def content_cleaning_failed_handler(request: Request, exc: ContentCleaningFailedError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(InvalidArticleForDeduplicationError)
async def invalid_article_dedup_handler(request: Request, exc: InvalidArticleForDeduplicationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(SimilarityCalculationError)
async def similarity_calculation_error_handler(request: Request, exc: SimilarityCalculationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(DuplicateIndexDatabaseError)
async def duplicate_index_db_error_handler(request: Request, exc: DuplicateIndexDatabaseError):
    logger.error(f"Duplicate index database error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(DuplicateConfigurationError)
async def duplicate_config_error_handler(request: Request, exc: DuplicateConfigurationError):
    logger.error(f"Duplicate configuration error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}},
    )



@app.exception_handler(ArticleNotFoundError)
async def article_not_found_handler(request: Request, exc: ArticleNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(CategoryNotFoundError)
async def category_not_found_handler(request: Request, exc: CategoryNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ArticleDuplicateError)
async def article_duplicate_handler(request: Request, exc: ArticleDuplicateError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(InvalidArticleDataError)
async def invalid_article_data_handler(request: Request, exc: InvalidArticleDataError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(DatabaseConnectionError)
async def database_connection_error_handler(request: Request, exc: DatabaseConnectionError):
    logger.error(f"Database error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(KnowledgeSourceException)
async def knowledge_source_exception_handler(request: Request, exc: KnowledgeSourceException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(MCPSecurityError)
async def mcp_security_error_handler(request: Request, exc: MCPSecurityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(MCPAuthenticationError)
async def mcp_auth_error_handler(request: Request, exc: MCPAuthenticationError):
    content = {"error": {"code": exc.code, "message": exc.message}}
    if exc.manual_action_required:
        content["error"]["manual_action_required"] = exc.manual_action_required
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=content,
    )


@app.exception_handler(MCPTimeoutError)
async def mcp_timeout_handler(request: Request, exc: MCPTimeoutError):
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(MCPConnectionError)
async def mcp_connection_handler(request: Request, exc: MCPConnectionError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(MCPToolExecutionError)
async def mcp_tool_execution_handler(request: Request, exc: MCPToolExecutionError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(ESTDException)
async def estd_exception_handler(request: Request, exc: ESTDException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Extract human-readable error messages from Pydantic errors
    errors = exc.errors()
    first_msg = errors[0].get("msg") if errors else "Invalid request parameters."
    loc = errors[0].get("loc", []) if errors else []
    field_name = loc[-1] if loc else "field"
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Validation error for '{field_name}': {first_msg}",
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal error occurred.",
            }
        },
    )


# ============================================================================
# Core Endpoints
# ============================================================================

@app.get("/setup-likes", tags=["Health"])
def setup_likes_endpoint():
    try:
        from backend.database.connection.session import get_engine
        from sqlalchemy import text
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS likes_count INTEGER DEFAULT 0 NOT NULL;"))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS article_likes (
                    id SERIAL PRIMARY KEY,
                    article_id BIGINT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
                    client_id VARCHAR(128) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    CONSTRAINT uq_article_client_like UNIQUE (article_id, client_id)
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_article_likes_article_id ON article_likes(article_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_article_likes_client_id ON article_likes(client_id);"))
        return {"status": "ok", "message": "Likes schema configured successfully."}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


@app.get("/", tags=["Health"], summary="Root service status endpoint")
async def root():
    """Root endpoint confirming service availability."""
    return {
        "success": True,
        "service": "ESTD Backend API",
        "message": "ESTD backend is running successfully",
        "status": "running",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"], summary="Comprehensive health check endpoint")
def health_check(response: Response):
    """Health check verifying FastAPI runtime and database connectivity."""
    try:
        from backend.database.connection.session import check_db_health
        db_health = check_db_health()
        return {
            "success": True,
            "service": "ESTD Backend API",
            "status": "healthy",
            "database": db_health.get("database", "connected"),
        }
    except Exception as exc:
        logger.error(f"Health check database failure: {exc}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "success": False,
            "service": "ESTD Backend API",
            "status": "unhealthy",
            "database": "disconnected",
            "error": "Database connectivity failed",
        }


# Include Step 1 Source Collection routes
app.include_router(source_collection_router)

# Include Step 2 Article Extraction routes
app.include_router(article_extraction_router)

# Include Step 3 Content Cleaning routes
app.include_router(content_cleaning_router)

# Include Step 4 Duplicate Detection & Deduplication routes
app.include_router(duplicate_detection_router)

# Include Step 5 Knowledge Source / PostgreSQL routes
app.include_router(knowledge_source_router)

# Include Step 6 MCP Integration routes
app.include_router(mcp_router)

# Include Step 7 Gemini AI Content Generation routes
app.include_router(generation_router)

# Include Step 8 Google Docs & Drive Output routes
app.include_router(gdrive_output_router)

# Include Pipeline Orchestration routes for Verification Dashboard
app.include_router(pipeline_router)

# Include Step 9 Multi-Angle Video Rail routes
app.include_router(video_router)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
