"""SQLAlchemy ORM model for dynamic Weekly Radar ("What's Dropping This Week") events."""
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from backend.common.constants.categories import VALID_CATEGORIES
from backend.database.connection.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RadarDrop(Base):
    """Represents a dynamic upcoming/scheduled event extracted from live news."""

    __tablename__ = "radar_drops"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    drop_key = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        doc="Deterministic deduplication key for an upcoming event",
    )
    title = Column(Text, nullable=False, doc="Concise title of the upcoming drop/event")
    description = Column(Text, nullable=False, doc="Factual 1-2 sentence summary grounded in news")
    category = Column(String(100), nullable=False, index=True, doc="Canonical ESTD parent category")
    tag = Column(String(100), nullable=False, default="Upcoming Event", doc="Short event type badge")

    event_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Scheduled UTC timestamp when this event drops or occurs",
    )
    end_date = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Optional UTC end timestamp for calendar export",
    )

    source_article_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("news_articles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="ID of the grounding NewsArticle in ESTD knowledge base",
    )
    source_title = Column(Text, nullable=True, doc="Headline of the grounding article")
    source_url = Column(Text, nullable=True, doc="Original publisher URL of the grounding article")
    source_name = Column(String(255), nullable=True, doc="Publisher name of the grounding article")

    confidence = Column(Integer, nullable=False, default=85, doc="Extraction confidence (0-100)")
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    generated_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_radar_drops_active_event_date", "is_active", "event_date"),
        Index("ix_radar_drops_category_active", "category", "is_active"),
    )

    def validate_category(self) -> bool:
        return self.category in VALID_CATEGORIES

    def to_dict(self, now_utc: datetime | None = None) -> Dict[str, Any]:
        """Serialize drop with dynamically computed relative date labels."""
        ref_now = now_utc or _utc_now()
        if ref_now.tzinfo is None:
            ref_now = ref_now.replace(tzinfo=timezone.utc)

        ev = self.event_date
        if ev.tzinfo is None:
            ev = ev.replace(tzinfo=timezone.utc)

        end_dt = self.end_date
        if end_dt is not None and end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        delta_days = (ev.date() - ref_now.date()).days

        if delta_days < 0:
            relative_time = "Past"
            status_urgency = "normal"
        elif delta_days == 0:
            relative_time = "Live Today" if ref_now >= ev else "Dropping Today"
            status_urgency = "urgent"
        elif delta_days == 1:
            relative_time = "Tomorrow"
            status_urgency = "urgent"
        elif delta_days == 2:
            relative_time = "In 2 Days"
            status_urgency = "urgent"
        elif delta_days <= 6:
            if ev.weekday() in (5, 6) and ref_now.weekday() < 5:
                relative_time = "This Weekend"
            else:
                relative_time = f"In {delta_days} Days"
            status_urgency = "soon"
        elif delta_days <= 13:
            relative_time = "Next Week"
            status_urgency = "normal"
        else:
            relative_time = "Upcoming"
            status_urgency = "normal"

        effective_end = end_dt or datetime.fromtimestamp(ev.timestamp() + 7200, tz=timezone.utc)

        raw_desc = " ".join((self.description or "").split())
        if len(raw_desc) > 160:
            clean_desc = raw_desc[:160].rsplit(" ", 1)[0].rstrip(",;:") + "..."
        else:
            clean_desc = raw_desc

        return {
            "id": f"radar-{self.id}",
            "db_id": self.id,
            "drop_key": self.drop_key,
            "title": self.title,
            "description": clean_desc,
            "category": self.category,
            "tag": self.tag,
            "event_date": ev.isoformat(),
            "end_date": effective_end.isoformat(),
            "target_date_ics": ev.strftime("%Y%m%dT%H%M%SZ"),
            "end_date_ics": effective_end.strftime("%Y%m%dT%H%M%SZ"),
            "date": ev.strftime("%b %d"),
            "day_name": ev.strftime("%A"),
            "day_short": ev.strftime("%a").upper(),
            "relative_time": relative_time,
            "status_urgency": status_urgency,
            "source_article_id": self.source_article_id,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "confidence": self.confidence,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
