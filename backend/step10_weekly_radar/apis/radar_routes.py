"""FastAPI routes for Dynamic Weekly Radar ("What's Dropping This Week")."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from backend.database.connection.session import get_db
from backend.step10_weekly_radar.services.radar_service import RadarService

router = APIRouter(
    prefix="/api/v1/radar",
    tags=["Step 10: Dynamic Weekly Radar"],
)

_radar_service = RadarService()


@router.get(
    "/drops",
    summary="Retrieve dynamic upcoming weekly drops extracted from live ESTD news",
)
def get_weekly_radar_drops(
    response: Response,
    category: Optional[str] = Query(default=None, description="Optional ESTD category filter"),
    refresh: bool = Query(default=False, description="Force fresh AI extraction from latest news"),
    session: Session = Depends(get_db),
):
    """Return active upcoming events for this week, automatically syncing when stale or empty."""
    if not refresh:
        response.headers["Cache-Control"] = "public, max-age=60"
    return _radar_service.get_weekly_radar(
        session=session,
        category=category,
        force_refresh=refresh,
        auto_refresh=True,
    )


@router.post(
    "/refresh",
    summary="Re-scan recent news articles and refresh Weekly Radar upcoming events",
)
def refresh_weekly_radar_drops(
    force: bool = Query(default=True, description="Bypass cooldown and re-extract from latest articles"),
    session: Session = Depends(get_db),
):
    """Trigger immediate extraction of upcoming events from the latest ingested news."""
    return _radar_service.refresh_weekly_radar(session=session, force=force)
