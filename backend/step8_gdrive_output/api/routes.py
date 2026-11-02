"""FastAPI router exposing Step 8 Google Drive and Google Docs output endpoints."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.connection.session import get_db
from backend.database.repositories.google_document_repository import GoogleDocumentRepository
from backend.step8_gdrive_output.exceptions import (
    ArticleIneligibleForOutputError,
    DocumentCreationError,
    DocumentRecordNotFoundError,
    FolderInitializationError,
    GoogleDriveAPIError,
    InvalidStep8CategoryError,
    Step8Exception,
    Step8ValidationError,
)
from backend.step8_gdrive_output.schemas.document_record import (
    Step8DocumentRecordSchema,
    Step8DocumentResponse,
)
from backend.step8_gdrive_output.schemas.folder_hierarchy import FolderHierarchySchema
from backend.step8_gdrive_output.schemas.process_request import (
    BatchProcessRequest,
    BatchProcessResponse,
    BatchProcessSummaryItem,
    ProcessArticleRequest,
    ProcessDirectRequest,
)
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator

router = APIRouter(prefix="/step8", tags=["Step 8 — Google Docs & Drive Output"])


def get_gdrive_service() -> GoogleDriveService:
    """Dependency provider for GoogleDriveService."""
    return GoogleDriveService()


def get_folder_resolver(
    gdrive_service: GoogleDriveService = Depends(get_gdrive_service),
) -> DriveFolderResolver:
    """Dependency provider for DriveFolderResolver."""
    return DriveFolderResolver(gdrive_service=gdrive_service)


def get_orchestrator(
    gdrive_service: GoogleDriveService = Depends(get_gdrive_service),
    folder_resolver: DriveFolderResolver = Depends(get_folder_resolver),
) -> Step8Orchestrator:
    """Dependency provider for Step8Orchestrator."""
    return Step8Orchestrator(
        gdrive_service=gdrive_service,
        folder_resolver=folder_resolver,
    )


@router.post(
    "/initialize-folders",
    response_model=FolderHierarchySchema,
    status_code=status.HTTP_200_OK,
    summary="Idempotently initialize ESTD CONTENT folder and 5 category subfolders",
)
def initialize_folder_hierarchy(
    force_refresh: bool = Query(default=False, description="Force refresh discovery from Google Drive"),
    folder_resolver: DriveFolderResolver = Depends(get_folder_resolver),
) -> FolderHierarchySchema:
    """Ensure ESTD CONTENT root folder and all 5 category subfolders exist in Google Drive."""
    try:
        return folder_resolver.initialize_hierarchy(force_refresh=force_refresh)
    except FolderInitializationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except GoogleDriveAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )


@router.get(
    "/folders",
    response_model=FolderHierarchySchema,
    summary="Get current Google Drive folder hierarchy structure and IDs",
)
def get_folder_structure(
    folder_resolver: DriveFolderResolver = Depends(get_folder_resolver),
) -> FolderHierarchySchema:
    """Retrieve current folder hierarchy details."""
    try:
        return folder_resolver.initialize_hierarchy(force_refresh=False)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "FOLDER_DISCOVERY_ERROR", "message": str(exc)},
        )


@router.post(
    "/process-article/{article_id}",
    response_model=Step8DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Process an approved knowledge source article into Google Docs",
)
def process_article(
    article_id: int,
    force_recreate: bool = Query(default=False, description="Force recreate document even if already created"),
    session: Session = Depends(get_db),
    orchestrator: Step8Orchestrator = Depends(get_orchestrator),
) -> Step8DocumentResponse:
    """Transform an approved article into a Google Document in the correct category folder."""
    try:
        return orchestrator.process_article_by_id(
            article_id=article_id,
            session=session,
            force_recreate=force_recreate,
        )
    except ArticleIneligibleForOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except InvalidStep8CategoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except DocumentCreationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except GoogleDriveAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except Step8Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )


@router.post(
    "/process-direct",
    response_model=Step8DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Directly output validated GeneratedNews content to Google Docs",
)
def process_direct_content(
    request: ProcessDirectRequest,
    session: Session = Depends(get_db),
    orchestrator: Step8Orchestrator = Depends(get_orchestrator),
) -> Step8DocumentResponse:
    """Format and upload a directly provided GeneratedNews article to Google Docs."""
    try:
        # If no article_id supplied, synthesize a transient identifier for tracking
        article_id = request.article_id or int(hash(request.news.title) % 100000000)
        return orchestrator.process_approved_content(
            news=request.news,
            article_id=article_id,
            session=session,
            force_recreate=False,
        )
    except Step8ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except DocumentCreationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )
    except GoogleDriveAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message, "details": exc.details},
        )


@router.get(
    "/documents/{article_id}",
    response_model=Step8DocumentResponse,
    summary="Get Google Document reference and status for an article",
)
def get_document_status(
    article_id: int,
    session: Session = Depends(get_db),
) -> Step8DocumentResponse:
    """Retrieve persisted Google Document record and Drive URLs for an article."""
    record = GoogleDocumentRepository.get_by_article_id(session, article_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"No Google Document record found for article ID {article_id}.",
            },
        )

    return Step8DocumentResponse(
        success=(record.status == "CREATED"),
        status=record.status,
        article_id=article_id,
        data=Step8DocumentRecordSchema.model_validate(record),
        is_duplicate_prevented=False,
    )


@router.post(
    "/retry/{article_id}",
    response_model=Step8DocumentResponse,
    summary="Retry failed Google Document creation for an article",
)
def retry_article_document(
    article_id: int,
    session: Session = Depends(get_db),
    orchestrator: Step8Orchestrator = Depends(get_orchestrator),
) -> Step8DocumentResponse:
    """Retry creating a Google Document for an article that previously failed."""
    try:
        return orchestrator.retry_article(article_id=article_id, session=session)
    except DocumentRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": exc.code, "message": exc.message},
        )
    except DocumentCreationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": exc.code, "message": exc.message},
        )


@router.get(
    "/health",
    summary="Check Google Drive / Docs connectivity and credentials health",
)
def check_step8_health(
    gdrive_service: GoogleDriveService = Depends(get_gdrive_service),
) -> Dict[str, Any]:
    """Verify Google OAuth credentials and test Google Drive API connectivity without exposing secrets."""
    from backend.step6_mcp.config.mcp_settings import get_mcp_settings
    settings = get_mcp_settings()
    auth_state = settings.get_google_auth_status()

    if not auth_state["credentials_authorized"]:
        return {
            "status": "REQUIRES_AUTHENTICATION",
            "authenticated": False,
            "connected": False,
            "details": "Run 'python -m backend.step6_mcp.google_drive_launcher --auth' to authenticate.",
        }

    try:
        # Perform quick metadata ping (search with limit=1)
        files = gdrive_service.search_files("trashed=false", limit=1)
        return {
            "status": "HEALTHY",
            "authenticated": True,
            "connected": True,
            "account": "shankar13052005@gmail.com",
            "api_endpoint": "https://www.googleapis.com/drive/v3",
        }
    except Exception as exc:
        return {
            "status": "DEGRADED",
            "authenticated": True,
            "connected": False,
            "error": str(exc),
        }
