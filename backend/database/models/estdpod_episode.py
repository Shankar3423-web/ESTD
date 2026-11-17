"""SQLAlchemy ORM model for ESTDPOD YouTube Channel podcast episodes and guest showcase."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    Text,
)

from backend.database.connection.session import Base


class EstdpodEpisode(Base):
    """Tracks published episodes, video podcasts, and guest spotlights from @ESTDPOD."""

    __tablename__ = "estdpod_episodes"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # YouTube Identity
    youtube_video_id = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="YouTube Video ID (e.g. dQw4w9WgXcQ)",
    )
    title = Column(Text, nullable=False, doc="Video/Podcast headline or episode title")
    slug = Column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
        doc="SEO-friendly unique URL slug",
    )
    description = Column(Text, nullable=True, doc="Original YouTube description and show notes")
    thumbnail_url = Column(Text, nullable=True, doc="High-resolution YouTube video thumbnail")
    duration = Column(String(32), nullable=True, doc="Human-readable duration (e.g. 1:30:43)")
    duration_seconds = Column(Integer, nullable=True, default=0, doc="Duration in total seconds")
    published_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Publication timestamp on YouTube",
    )

    # Guest Profile & Showcase (Matching reference inspiration)
    guest_name = Column(String(255), nullable=True, index=True, doc="Featured guest name(s)")
    guest_designation = Column(String(255), nullable=True, doc="Guest title / professional designation")
    guest_organization = Column(String(255), nullable=True, doc="Company, party, or institution affiliation")
    guest_avatar_url = Column(Text, nullable=True, doc="Direct photo or portrait avatar of the guest")

    # Classification & Context
    category = Column(String(100), nullable=False, default="Tech", index=True)
    tags = Column(JSON, nullable=True, default=list, doc="Array of topic tags or hashtags")
    key_takeaways = Column(JSON, nullable=True, default=list, doc="Structured executive points or chapter markers")

    # Metadata & Display Prioritization
    view_count = Column(Integer, nullable=True, default=0)
    is_featured = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert episode model to dictionary for API serialization."""
        return {
            "id": self.id,
            "youtube_video_id": self.youtube_video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={self.youtube_video_id}",
            "youtube_embed_url": f"https://www.youtube-nocookie.com/embed/{self.youtube_video_id}?autoplay=1&rel=0",
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url or f"https://i.ytimg.com/vi/{self.youtube_video_id}/maxresdefault.jpg",
            "duration": self.duration,
            "duration_seconds": self.duration_seconds,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "guest_name": self.guest_name,
            "guest_designation": self.guest_designation,
            "guest_organization": self.guest_organization,
            "guest_avatar_url": self.guest_avatar_url,
            "category": self.category,
            "tags": self.tags or [],
            "key_takeaways": self.key_takeaways or [],
            "view_count": self.view_count or 0,
            "is_featured": self.is_featured,
            "channel_name": "ESTD",
            "channel_handle": "@ESTDPOD",
            "channel_url": "https://www.youtube.com/@ESTDPOD",
        }

