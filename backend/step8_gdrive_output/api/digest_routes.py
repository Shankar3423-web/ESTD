"""FastAPI routes for Plan C Daily Category Digest generation and history."""
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.common.auth.security import verify_admin_api_key
from backend.database.connection.session import get_db
from backend.database.models.daily_digest_record import DailyDigestRecord
from backend.step8_gdrive_output.services.daily_digest_service import DailyDigestService

router = APIRouter(
    prefix="/api/v1/digest",
    tags=["Plan C - Daily Category Digest"],
)

digest_service = DailyDigestService()


class DigestGenerateRequest(BaseModel):
    """Payload to trigger daily digest compilation."""
    target_date: Optional[str] = Field(
        default=None,
        description="Target calendar date in YYYY-MM-DD format (defaults to UTC today)",
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional subset of categories to compile (e.g. ['Tech', 'Sports'])",
    )
    dry_run: bool = Field(
        default=False,
        description="If True, compiles and validates document preview without creating Google Docs in Drive",
    )
    force: bool = Field(
        default=False,
        description="If True, forces regeneration even if a completed digest doc already exists for the day",
    )


class DigestItemResponse(BaseModel):
    """Details of a single daily digest record."""
    id: int
    digest_date: str
    category: str
    article_count: int
    status: str
    google_document_id: Optional[str] = None
    google_document_url: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DigestListResponse(BaseModel):
    """Response containing list of compiled daily digests."""
    total: int
    items: List[DigestItemResponse]


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    summary="Compile and upload daily category digests to Google Drive",
    dependencies=[Depends(verify_admin_api_key)],
)
def generate_daily_digest(payload: Optional[DigestGenerateRequest] = None):
    """Generate daily digests for today or a specific date.
    
    - Aggregates all approved stories from PostgreSQL for each category.
    - Compiles a unified editorial document (highlights, TOC, full stories with slugs and links).
    - If dry_run=False: Creates exactly 1 Google Doc per category in Google Drive.
    - If dry_run=True: Returns character counts, story counts, and formatted preview.
    """
    req = payload or DigestGenerateRequest()
    parsed_date: Optional[date] = None
    if req.target_date:
        try:
            parsed_date = datetime.strptime(req.target_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DATE_FORMAT", "message": "target_date must be in YYYY-MM-DD format."},
            )

    result = digest_service.generate_all_digests_for_date(
        target_date=parsed_date,
        categories=req.categories,
        dry_run=req.dry_run,
        force=req.force,
    )
    return result


@router.get(
    "/history",
    response_model=DigestListResponse,
    summary="Retrieve history of compiled category digests and Google Doc links",
)
def get_digest_history(
    category: Optional[str] = Query(default=None, description="Optional category filter"),
    limit: int = Query(default=30, ge=1, le=100),
    session: Session = Depends(get_db),
):
    """Return historical daily digests with their Google Document URLs and status."""
    query = session.query(DailyDigestRecord)
    if category:
        query = query.filter(DailyDigestRecord.category == category)

    records = query.order_by(DailyDigestRecord.digest_date.desc(), DailyDigestRecord.created_at.desc()).limit(limit).all()

    items = [
        DigestItemResponse(
            id=r.id,
            digest_date=str(r.digest_date),
            category=r.category,
            article_count=r.article_count,
            status=r.status,
            google_document_id=r.google_document_id,
            google_document_url=r.google_document_url,
            google_drive_folder_id=r.google_drive_folder_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]
    return DigestListResponse(total=len(items), items=items)


@router.get(
    "/{digest_id}",
    response_model=DigestItemResponse,
    summary="Retrieve details of a single daily digest record",
)
def get_digest_by_id(digest_id: int, session: Session = Depends(get_db)):
    """Fetch a specific daily digest record by its primary key ID."""
    record = session.query(DailyDigestRecord).filter(DailyDigestRecord.id == digest_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DIGEST_NOT_FOUND", "message": f"Daily digest record #{digest_id} not found."},
        )
    return DigestItemResponse(
        id=record.id,
        digest_date=str(record.digest_date),
        category=record.category,
        article_count=record.article_count,
        status=record.status,
        google_document_id=record.google_document_id,
        google_document_url=record.google_document_url,
        google_drive_folder_id=record.google_drive_folder_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )

