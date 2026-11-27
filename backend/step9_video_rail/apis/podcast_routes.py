"""FastAPI routes for ESTDPOD YouTube Channel podcasts and guest spotlights."""
import time
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend.common.auth.security import verify_admin_api_key
from backend.step9_video_rail.services.estdpod_sync_service import (
    ESTDPOD_CHANNEL_HANDLE,
    ESTDPOD_CHANNEL_URL,
    EstdpodSyncService,
)

router = APIRouter(
    prefix="/api/v1/podcasts",
    tags=["ESTDPOD YouTube Channel & Podcasts"],
)

sync_service = EstdpodSyncService()
_EPISODES_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_EPISODES_CACHE_TTL = 180.0


@router.get(
    "/episodes",
    summary="List official ESTDPOD episodes and guest spotlights",
)
def list_podcast_episodes(
    response: Response,
    category: Optional[str] = Query(default=None, description="Optional category filter (e.g. 'Tech & AI')"),
    featured_only: bool = Query(default=False, description="Filter for featured flagship episodes only"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Retrieve published ESTDPOD podcast episodes and guest profiles for the website."""
    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=300"
    cache_key = f"{category or ''}:{featured_only}:{limit}"
    now = time.time()
    if cache_key in _EPISODES_CACHE:
        cached_time, cached_payload = _EPISODES_CACHE[cache_key]
        if now - cached_time < _EPISODES_CACHE_TTL:
            return cached_payload

    episodes = sync_service.list_episodes(category=category, limit=limit, featured_only=featured_only)
    payload = {
        "channel": {
            "name": "ESTD",
            "handle": ESTDPOD_CHANNEL_HANDLE,
            "url": ESTDPOD_CHANNEL_URL,
            "bio": "Conversations That Inspire. Ideas That Innovate.",
        },
        "total": len(episodes),
        "episodes": episodes,
    }
    _EPISODES_CACHE[cache_key] = (now, payload)
    return payload


@router.get(
    "/episodes/{id_or_slug}",
    summary="Retrieve single ESTDPOD episode by ID, slug, or YouTube ID",
)
def get_podcast_episode(id_or_slug: str):
    """Retrieve a specific ESTDPOD episode with complete guest bio and key takeaways."""
    episode = sync_service.get_episode_by_slug_or_id(id_or_slug)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EPISODE_NOT_FOUND", "message": f"ESTDPOD episode '{id_or_slug}' not found."},
        )
    return episode


@router.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    summary="Trigger automated synchronization with @ESTDPOD YouTube Channel",
    dependencies=[Depends(verify_admin_api_key)],
)
def sync_estdpod_channel(
    force_refresh: bool = Query(default=False, description="Force refresh existing episode metadata"),
):
    """Poll the @ESTDPOD YouTube channel for new video podcasts and update PostgreSQL."""
    result = sync_service.sync_channel(force_refresh=force_refresh)
    return result

