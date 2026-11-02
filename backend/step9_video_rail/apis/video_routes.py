"""ESTD Step 9 Multi-Angle Video Rail API Routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.connection.session import get_db
from backend.database.models.news_article import NewsArticle
from backend.step9_video_rail.services.video_service import (
    get_cached_video_rail,
    resolve_story_video_rail,
    search_youtube_videos,
)

router = APIRouter(prefix="/api/v1/videos", tags=["Step 9: Multi-Angle Video Rail"])


@router.get(
    "/story/{article_id}",
    summary="Retrieve verified 5-angle video rail for an article",
)
def get_story_video_rail(
    article_id: int,
    force_refresh: bool = Query(default=False, description="Bypass cache and rediscover fresh videos"),
    session: Session = Depends(get_db),
):
    """Retrieve 5 verified video perspectives (Official, Broadcast, Analysis, Creator, Fan) for a news story."""
    # Fast path: check in-memory cache if not forcing refresh
    if not force_refresh:
        cached = get_cached_video_rail(article_id)
        if cached:
            return {
                "article_id": article_id,
                "cached": True,
                "total": len(cached),
                "video_rail": cached,
            }

    article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ARTICLE_NOT_FOUND", "message": f"Article #{article_id} not found."},
        )

    perspectives = resolve_story_video_rail(
        article_id=article.id,
        title=article.title,
        category=article.category,
        subcategory=article.subcategory,
        source_name=article.source_name,
        force_refresh=force_refresh,
    )

    return {
        "article_id": article.id,
        "cached": False,
        "total": len(perspectives),
        "video_rail": perspectives,
    }


@router.get(
    "/search",
    summary="Dynamic search for YouTube videos matching any news headline or query",
)
def search_videos_endpoint(
    query: str = Query(..., min_length=2, description="News topic or headline to search"),
    limit: int = Query(default=5, ge=1, le=15, description="Max videos to return"),
):
    """Dynamically search YouTube public indices for authentic videos matching a news query."""
    videos = search_youtube_videos(query=query, max_results=limit)
    return {
        "query": query,
        "total": len(videos),
        "items": videos,
    }


@router.post(
    "/story/{article_id}/refresh",
    summary="Force refresh video perspectives for an article",
)
def refresh_story_video_rail(
    article_id: int,
    session: Session = Depends(get_db),
):
    """Force re-query and rebuild video perspectives for a specific story."""
    article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ARTICLE_NOT_FOUND", "message": f"Article #{article_id} not found."},
        )

    perspectives = resolve_story_video_rail(
        article_id=article.id,
        title=article.title,
        category=article.category,
        subcategory=article.subcategory,
        source_name=article.source_name,
        force_refresh=True,
    )

    return {
        "article_id": article.id,
        "refreshed": True,
        "total": len(perspectives),
        "video_rail": perspectives,
    }
