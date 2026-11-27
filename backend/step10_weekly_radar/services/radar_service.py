"""Dynamic Weekly Radar ("What's Dropping This Week") extraction and serving service.

Extracts upcoming/scheduled events, launches, fixtures, policy deadlines, and market
catalysts directly from live ESTD NewsArticle records using Gemini AI (with Groq failover
and deterministic heuristic fallback), persists them in PostgreSQL, and dynamically
computes relative dates against the current clock.
"""
from __future__ import annotations

import hashlib
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.common.constants.categories import (
    ESTDCategory,
    VALID_CATEGORIES,
    resolve_canonical_category,
)
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.radar_drop import RadarDrop
from backend.step7_content_generation.client.gemini_client import GeminiClient


_FORWARD_KEYWORDS = (
    "upcoming",
    "scheduled",
    "launch",
    "launches",
    "launching",
    "release",
    "releasing",
    "premiere",
    "premieres",
    "drop",
    "drops",
    "fixture",
    "match",
    "clash",
    "derby",
    "tournament",
    "cup",
    "grand prix",
    "summit",
    "conference",
    "deadline",
    "portal",
    "earnings",
    "expected",
    "next week",
    "this week",
    "this weekend",
    "tomorrow",
    "set to",
    "slated",
    "to unveil",
    "to announce",
    "to host",
    "to take over",
    "begins",
    "opens",
    "starts",
    "kickoff",
    "black friday",
    "cyber monday",
    "rollout",
    "briefing",
    "q1",
    "q2",
    "q3",
    "q4",
)

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_CATEGORY_DEFAULT_TAGS = {
    ESTDCategory.TECH.value: "Tech & AI Drop",
    ESTDCategory.ENTERTAINMENT.value: "Streaming & Releases",
    ESTDCategory.SPORTS.value: "Match & Fixture Watch",
    ESTDCategory.DEVELOPMENTS.value: "Policy & Science Watch",
    ESTDCategory.BUSINESS_FINANCE.value: "Market Catalyst",
}

_MONTH_PATTERN = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b",
    re.IGNORECASE,
)

_MONTH_NUM = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


class ExtractedRadarItem(BaseModel):
    """Schema for a single upcoming event extracted by Gemini."""

    title: str = Field(description="Punchy 6 to 12 word upcoming event title")
    description: str = Field(description="1 to 2 factual sentences explaining what is happening and why it matters")
    category: str = Field(
        description="Must be one of: Tech, Entertainment, Sports, Developments, Business & Finance"
    )
    tag: str = Field(description="Short 1 to 3 word event badge e.g. Product Launch, Live Fixture, Streaming & OTT, Policy & Deadlines, Earnings Catalyst")
    event_date_iso: str = Field(
        description="Scheduled UTC date/time in YYYY-MM-DDTHH:MM:SSZ format between today and +10 days"
    )
    source_article_id: Optional[int] = Field(
        default=None,
        description="Exact integer ID of the grounding ESTD article from the provided list",
    )
    confidence: int = Field(default=88, ge=50, le=100)


class RadarExtractionOutput(BaseModel):
    """Structured batch of extracted upcoming events."""

    items: List[ExtractedRadarItem] = Field(default_factory=list)


# In-memory cache & concurrency guard
_RADAR_CACHE_TTL_SECONDS = 60.0
_RADAR_STALE_HOURS = 6.0
_RADAR_NEW_ARTICLE_MIN_COOLDOWN_SECONDS = 900.0  # 15 minutes
_RADAR_CACHE_LOCK = threading.Lock()
_RADAR_REFRESH_LOCK = threading.Lock()
_RADAR_MEMORY_CACHE: Dict[str, Any] = {"items": None, "fetched_at": 0.0, "generated_at": None}


def clear_radar_cache() -> None:
    """Reset the in-memory Weekly Radar cache."""
    with _RADAR_CACHE_LOCK:
        _RADAR_MEMORY_CACHE["items"] = None
        _RADAR_MEMORY_CACHE["fetched_at"] = 0.0
        _RADAR_MEMORY_CACHE["generated_at"] = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_utc_day(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=timezone.utc)


def _compute_drop_key(category: str, title: str, source_article_id: Optional[int]) -> str:
    """Build a stable deduplication key so armed user reminders persist across refreshes."""
    norm_words = re.sub(r"[^a-z0-9\s]", "", (title or "").lower()).split()
    stem = " ".join(norm_words[:6])
    raw = f"{category}|{source_article_id or 'none'}|{stem}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _parse_iso_utc(raw_iso: str, fallback_dt: datetime) -> datetime:
    """Parse an ISO-8601 string into timezone-aware UTC datetime."""
    if not raw_iso:
        return fallback_dt
    clean = raw_iso.strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed
    except ValueError:
        # Try date-only YYYY-MM-DD
        try:
            d = datetime.strptime(clean[:10], "%Y-%m-%d").replace(hour=14, tzinfo=timezone.utc)
            return d
        except ValueError:
            return fallback_dt


def _score_article_forward_potential(article: NewsArticle, now_utc: datetime) -> float:
    """Score an article by forward-looking event cues and recency."""
    text = f"{article.title or ''} {article.description or ''} {(article.content or '')[:500]}".lower()
    score = 0.0
    for kw in _FORWARD_KEYWORDS:
        if kw in text:
            score += 2.0
    if _MONTH_PATTERN.search(text):
        score += 3.0
    for wd in _WEEKDAY_MAP:
        if re.search(rf"\b{wd}\b", text):
            score += 1.5

    ref_ts = article.published_at or article.created_at or now_utc
    if ref_ts.tzinfo is None:
        ref_ts = ref_ts.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now_utc - ref_ts).total_seconds() / 3600.0)
    recency_bonus = max(0.0, 10.0 - (age_hours / 18.0))
    return score + recency_bonus


def _infer_upcoming_date_from_text(text: str, now_utc: datetime, fallback_offset_days: int = 1) -> datetime:
    """Deterministically infer a plausible upcoming UTC datetime from article text."""
    lower = (text or "").lower()
    today_start = _start_of_utc_day(now_utc)

    # 1. Explicit Month + Day mention in the near future
    for match in _MONTH_PATTERN.finditer(text or ""):
        month_str, day_str, year_str = match.group(1), match.group(2), match.group(3)
        month_num = _MONTH_NUM.get(month_str.lower())
        day_num = int(day_str)
        year_num = int(year_str) if year_str else now_utc.year
        if month_num and 1 <= day_num <= 31:
            try:
                candidate = datetime(year_num, month_num, day_num, 14, 0, 0, tzinfo=timezone.utc)
                delta = (candidate.date() - now_utc.date()).days
                if 0 <= delta <= 14:
                    return candidate
            except ValueError:
                pass

    # 2. Relative keywords
    if "tomorrow" in lower:
        return today_start + timedelta(days=1, hours=14)
    if "this weekend" in lower:
        days_until_sat = (5 - now_utc.weekday()) % 7
        if days_until_sat == 0 and now_utc.hour >= 18:
            days_until_sat = 1
        return today_start + timedelta(days=max(0, days_until_sat), hours=15)
    if "next week" in lower:
        days_until_mon = (7 - now_utc.weekday()) % 7 or 7
        return today_start + timedelta(days=days_until_mon + 1, hours=14)

    # 3. Weekday mention
    for wd_name, wd_idx in _WEEKDAY_MAP.items():
        if re.search(rf"\b{wd_name}\b", lower):
            days_ahead = (wd_idx - now_utc.weekday()) % 7
            if days_ahead == 0 and now_utc.hour >= 18:
                days_ahead = 7
            return today_start + timedelta(days=days_ahead, hours=14)

    # 4. Default upcoming slot within this week
    return today_start + timedelta(days=max(0, fallback_offset_days), hours=15)


class RadarService:
    """Extracts, caches, and serves dynamic Weekly Radar drops from live ESTD news."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self._gemini_client = gemini_client

    def _get_gemini_client(self) -> GeminiClient:
        if self._gemini_client is None:
            self._gemini_client = GeminiClient()
        return self._gemini_client

    def _select_candidate_articles(self, session: Session, now_utc: datetime) -> List[NewsArticle]:
        """Gather top recent and forward-looking articles balanced across all 5 categories."""
        cutoff = now_utc - timedelta(days=10)
        candidates: List[NewsArticle] = []

        for cat in VALID_CATEGORIES:
            rows = (
                session.query(NewsArticle)
                .filter(
                    NewsArticle.category == cat,
                    func.coalesce(NewsArticle.published_at, NewsArticle.created_at) >= cutoff,
                )
                .order_by(NewsArticle.created_at.desc())
                .limit(25)
                .all()
            )
            if not rows:
                # Fallback if DB has no articles within 10 days (e.g., fresh/seeded env)
                rows = (
                    session.query(NewsArticle)
                    .filter(NewsArticle.category == cat)
                    .order_by(NewsArticle.created_at.desc())
                    .limit(12)
                    .all()
                )
            scored = sorted(
                rows,
                key=lambda a: _score_article_forward_potential(a, now_utc),
                reverse=True,
            )
            candidates.extend(scored[:7])

        return candidates

    def _extract_via_gemini(
        self,
        candidates: List[NewsArticle],
        now_utc: datetime,
    ) -> List[Dict[str, Any]]:
        """Use Gemini AI (with Groq circuit-breaker fallback) to extract structured weekly drops."""
        if not candidates:
            return []

        today_str = now_utc.strftime("%Y-%m-%d")
        end_window_str = (now_utc + timedelta(days=9)).strftime("%Y-%m-%d")
        today_label = now_utc.strftime("%Y-%m-%d (%A) %H:%M UTC")

        article_blocks = []
        article_by_id: Dict[int, NewsArticle] = {}
        for art in candidates[:35]:
            article_by_id[art.id] = art
            pub = (art.published_at or art.created_at or now_utc).strftime("%Y-%m-%d")
            excerpt = re.sub(r"\s+", " ", (art.description or art.content or "")).strip()[:360]
            article_blocks.append(
                f"[ID:{art.id}] Category: {art.category} | Published: {pub} | Source: {art.source_name or 'ESTD Wire'}\n"
                f"Headline: {art.title}\n"
                f"Summary: {excerpt}"
            )

        joined_articles = "\n\n".join(article_blocks)

        prompt = f"""You are ESTD Forward Intel, the AI radar analyst for the ESTD News Platform.
Current UTC date & time: {today_label}.
Target Radar Window: {today_str} through {end_window_str} (THIS WEEK and the next ~9 days).

Below are real, freshly ingested news stories from the ESTD PostgreSQL wire:
==================================================
{joined_articles}
==================================================

Your task:
Extract 6 to 8 high-signal UPCOMING / UNFOLDING events ("What's Dropping This Week") directly grounded in the news stories above.
Include:
1. Explicitly scheduled launches, releases, matches, policy deadlines, summits, recalls, or earnings mentioned in the articles that take place on or after {today_str}.
2. Imminent near-term developments, weekend releases/matches, market sessions, or follow-up milestones directly arising this week from the articles above.

Strict Rules:
- EVERY `event_date_iso` MUST fall between {today_str}T00:00:00Z and {end_window_str}T23:59:59Z. NEVER output past dates before {today_str}.
- Spread events across the week (today, tomorrow, weekend, next week) realistically based on each story's timing.
- Cover as many of the 5 ESTD categories as available in the articles: Tech, Entertainment, Sports, Developments, Business & Finance.
- `category` MUST be an exact match to one of: "Tech", "Entertainment", "Sports", "Developments", "Business & Finance".
- `source_article_id` MUST be the exact integer ID from `[ID:...]` of the grounding article.
- `title`: crisp, forward-looking headline (6 to 12 words).
- `description`: 1 to 2 clear, factual sentences grounded in the article.
- `tag`: short 1 to 3 word badge (e.g., "Product Launch", "Streaming & OTT", "Live Fixture", "Policy Milestone", "Earnings Catalyst", "Market Watch", "Cyber Advisory").
"""

        client = self._get_gemini_client()
        result = client.generate_structured(
            prompt=prompt,
            response_schema=RadarExtractionOutput,
            temperature=0.2,
        )

        today_start = _start_of_utc_day(now_utc)
        max_future = today_start + timedelta(days=14)
        extracted: List[Dict[str, Any]] = []

        for item in (result.items or []):
            cat = resolve_canonical_category(item.category) or (
                item.category if item.category in VALID_CATEGORIES else None
            )
            if not cat:
                continue

            ev_dt = _parse_iso_utc(item.event_date_iso, today_start + timedelta(days=1, hours=14))
            if ev_dt < today_start:
                # Clamp past-dated extractions onto today if within 24h, otherwise skip stale items
                if (today_start - ev_dt).days <= 1:
                    ev_dt = today_start + timedelta(hours=18)
                else:
                    continue
            if ev_dt > max_future:
                ev_dt = today_start + timedelta(days=7, hours=14)

            src_art = article_by_id.get(item.source_article_id) if item.source_article_id else None
            clean_title = re.sub(r"\s+\|\s+[^|]+$", "", item.title.strip()).strip()
            clean_desc = re.sub(r"\s+", " ", item.description.strip())
            if len(clean_desc) > 155:
                clean_desc = clean_desc[:155].rsplit(" ", 1)[0].rstrip(",;:") + "..."
            extracted.append(
                {
                    "title": clean_title[:100],
                    "description": clean_desc,
                    "category": cat,
                    "tag": (item.tag or _CATEGORY_DEFAULT_TAGS.get(cat, "Upcoming")).strip()[:80],
                    "event_date": ev_dt,
                    "end_date": ev_dt + timedelta(hours=2),
                    "source_article_id": src_art.id if src_art else None,
                    "source_title": src_art.title if src_art else None,
                    "source_url": (src_art.canonical_url or src_art.url) if src_art else None,
                    "source_name": src_art.source_name if src_art else "ESTD Intelligence",
                    "confidence": int(item.confidence or 88),
                }
            )

        return extracted

    def _extract_heuristic_fallback(
        self,
        candidates: List[NewsArticle],
        now_utc: datetime,
        existing_categories: set[str],
        needed_count: int = 6,
    ) -> List[Dict[str, Any]]:
        """Deterministic fallback extractor grounded in real NewsArticle rows."""
        if not candidates or needed_count <= 0:
            return []

        fallback_items: List[Dict[str, Any]] = []
        used_article_ids: set[int] = set()

        # Pass 1: one per missing category for broad coverage
        ordered_cats = [c for c in VALID_CATEGORIES if c not in existing_categories] + [
            c for c in VALID_CATEGORIES if c in existing_categories
        ]

        day_offset = 0
        for cat in ordered_cats:
            if len(fallback_items) >= needed_count:
                break
            cat_articles = [a for a in candidates if a.category == cat and a.id not in used_article_ids]
            if not cat_articles:
                continue
            art = cat_articles[0]
            used_article_ids.add(art.id)
            raw_text = f"{art.title or ''}. {art.description or ''}"
            ev_dt = _infer_upcoming_date_from_text(raw_text, now_utc, fallback_offset_days=day_offset % 6)
            day_offset += 1

            raw_title = re.sub(r"\s+\|\s+[^|]+$", "", (art.title or "").strip()).strip()
            if len(raw_title) > 85:
                raw_title = raw_title[:85].rsplit(" ", 1)[0].rstrip(",;:-") + "..."

            raw_desc = re.sub(r"\s+", " ", (art.description or art.content or "")).strip()
            if len(raw_desc) > 145:
                desc = raw_desc[:145].rsplit(" ", 1)[0].rstrip(",;:") + "..."
            elif raw_desc:
                desc = raw_desc
            else:
                desc = f"Developing {cat} coverage tracked by ESTD from {art.source_name or 'live wire'}."

            fallback_items.append(
                {
                    "title": raw_title,
                    "description": desc,
                    "category": cat,
                    "tag": art.subcategory or _CATEGORY_DEFAULT_TAGS.get(cat, "Upcoming Watch"),
                    "event_date": ev_dt,
                    "end_date": ev_dt + timedelta(hours=2),
                    "source_article_id": art.id,
                    "source_title": art.title,
                    "source_url": art.canonical_url or art.url,
                    "source_name": art.source_name or "ESTD Wire",
                    "confidence": 76,
                }
            )

        return fallback_items

    def refresh_weekly_radar(
        self,
        session: Optional[Session] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Extract fresh upcoming drops from recent news and persist them to PostgreSQL."""
        with _RADAR_REFRESH_LOCK:
            if session is not None:
                return self._refresh_with_session(session, force=force)
            with get_db_session() as own_session:
                return self._refresh_with_session(own_session, force=force)

    def _refresh_with_session(self, session: Session, force: bool = False) -> Dict[str, Any]:
        now_utc = _utc_now()
        today_start = _start_of_utc_day(now_utc)

        if not force:
            newest_gen = (
                session.query(func.max(RadarDrop.generated_at))
                .filter(RadarDrop.is_active == True)  # noqa: E712
                .scalar()
            )
            if newest_gen is not None:
                if newest_gen.tzinfo is None:
                    newest_gen = newest_gen.replace(tzinfo=timezone.utc)
                if (now_utc - newest_gen).total_seconds() < 60:
                    active = self._query_active_drops(session, now_utc=now_utc)
                    return {
                        "refreshed": False,
                        "reason": "cooldown_active",
                        "generated_at": newest_gen.isoformat(),
                        "total": len(active),
                        "items": [d.to_dict(now_utc) for d in active],
                    }

        candidates = self._select_candidate_articles(session, now_utc)
        if not candidates:
            logger.info("[WeeklyRadar] No NewsArticle records available yet for radar extraction.")
            return {
                "refreshed": False,
                "reason": "no_articles",
                "generated_at": now_utc.isoformat(),
                "total": 0,
                "items": [],
            }

        extracted: List[Dict[str, Any]] = []
        extraction_mode = "gemini_ai"
        try:
            extracted = self._extract_via_gemini(candidates, now_utc)
        except Exception as exc:
            logger.warning(f"[WeeklyRadar] Gemini extraction failed, using deterministic fallback: {exc}")
            extraction_mode = "heuristic_fallback"

        if len(extracted) < 4:
            existing_cats = {item["category"] for item in extracted}
            needed = max(0, 6 - len(extracted))
            fallback = self._extract_heuristic_fallback(
                candidates,
                now_utc,
                existing_categories=existing_cats,
                needed_count=needed,
            )
            if fallback:
                if not extracted:
                    extraction_mode = "heuristic_fallback"
                else:
                    extraction_mode = "hybrid_ai_fallback"
                extracted.extend(fallback)

        if not extracted:
            return {
                "refreshed": False,
                "reason": "empty_extraction",
                "generated_at": now_utc.isoformat(),
                "total": 0,
                "items": [],
            }

        # Deactivate expired or previously active drops before upserting fresh batch
        session.query(RadarDrop).filter(RadarDrop.is_active == True).update(  # noqa: E712
            {"is_active": False, "updated_at": now_utc},
            synchronize_session=False,
        )

        persisted_drops: List[RadarDrop] = []
        seen_keys: set[str] = set()

        for item in extracted[:9]:
            drop_key = _compute_drop_key(item["category"], item["title"], item.get("source_article_id"))
            if drop_key in seen_keys:
                continue
            seen_keys.add(drop_key)

            existing = session.query(RadarDrop).filter(RadarDrop.drop_key == drop_key).first()
            if existing:
                existing.title = item["title"]
                existing.description = item["description"]
                existing.category = item["category"]
                existing.tag = item["tag"]
                existing.event_date = item["event_date"]
                existing.end_date = item["end_date"]
                existing.source_article_id = item.get("source_article_id")
                existing.source_title = item.get("source_title")
                existing.source_url = item.get("source_url")
                existing.source_name = item.get("source_name")
                existing.confidence = item.get("confidence", 85)
                existing.is_active = True
                existing.generated_at = now_utc
                existing.updated_at = now_utc
                persisted_drops.append(existing)
            else:
                new_drop = RadarDrop(
                    drop_key=drop_key,
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    tag=item["tag"],
                    event_date=item["event_date"],
                    end_date=item["end_date"],
                    source_article_id=item.get("source_article_id"),
                    source_title=item.get("source_title"),
                    source_url=item.get("source_url"),
                    source_name=item.get("source_name"),
                    confidence=item.get("confidence", 85),
                    is_active=True,
                    generated_at=now_utc,
                )
                session.add(new_drop)
                persisted_drops.append(new_drop)

        session.flush()
        session.commit()

        # Re-query sorted active upcoming drops
        active_drops = self._query_active_drops(session, now_utc=now_utc)
        serialized = [d.to_dict(now_utc) for d in active_drops]

        with _RADAR_CACHE_LOCK:
            _RADAR_MEMORY_CACHE["items"] = serialized
            _RADAR_MEMORY_CACHE["fetched_at"] = time.monotonic()
            _RADAR_MEMORY_CACHE["generated_at"] = now_utc.isoformat()

        logger.info(
            f"[WeeklyRadar] Refreshed {len(serialized)} dynamic upcoming drops via {extraction_mode} "
            f"(window >= {today_start.date().isoformat()})."
        )
        return {
            "refreshed": True,
            "mode": extraction_mode,
            "generated_at": now_utc.isoformat(),
            "total": len(serialized),
            "items": serialized,
        }

    def _query_active_drops(
        self,
        session: Session,
        now_utc: datetime,
        category: Optional[str] = None,
    ) -> List[RadarDrop]:
        today_start = _start_of_utc_day(now_utc)
        q = session.query(RadarDrop).filter(
            RadarDrop.is_active == True,  # noqa: E712
            RadarDrop.event_date >= today_start,
        )
        if category and category != "All":
            resolved = resolve_canonical_category(category) or category
            q = q.filter(RadarDrop.category == resolved)
        return q.order_by(RadarDrop.event_date.asc(), RadarDrop.confidence.desc()).limit(12).all()

    def _needs_auto_refresh(self, session: Session, active_drops: List[RadarDrop], now_utc: datetime) -> bool:
        if not active_drops:
            # Only auto-refresh if there are actually articles in DB
            has_articles = session.query(NewsArticle.id).limit(1).first() is not None
            return has_articles

        newest_gen = max(
            (d.generated_at.replace(tzinfo=timezone.utc) if d.generated_at.tzinfo is None else d.generated_at)
            for d in active_drops
        )
        age_seconds = (now_utc - newest_gen).total_seconds()
        if age_seconds > _RADAR_STALE_HOURS * 3600:
            return True

        # Check if newer news arrived since the last radar generation (with cooldown)
        if age_seconds >= _RADAR_NEW_ARTICLE_MIN_COOLDOWN_SECONDS:
            latest_article_at = session.query(func.max(NewsArticle.created_at)).scalar()
            if latest_article_at is not None:
                if latest_article_at.tzinfo is None:
                    latest_article_at = latest_article_at.replace(tzinfo=timezone.utc)
                if latest_article_at > newest_gen:
                    return True

        return False

    def get_weekly_radar(
        self,
        session: Session,
        category: Optional[str] = None,
        force_refresh: bool = False,
        auto_refresh: bool = True,
    ) -> Dict[str, Any]:
        """Return active dynamic Weekly Radar drops, refreshing automatically when stale or empty."""
        now_utc = _utc_now()

        if force_refresh:
            res = self.refresh_weekly_radar(session=session, force=True)
            items = res.get("items", [])
            if category and category != "All":
                resolved = resolve_canonical_category(category) or category
                items = [i for i in items if i["category"] == resolved]
            return {
                "total": len(items),
                "generated_at": res.get("generated_at"),
                "server_now": now_utc.isoformat(),
                "cached": False,
                "items": items,
            }

        # Check fast in-memory cache first
        with _RADAR_CACHE_LOCK:
            cached_items = _RADAR_MEMORY_CACHE["items"]
            fetched_at = _RADAR_MEMORY_CACHE["fetched_at"]
            cached_gen = _RADAR_MEMORY_CACHE["generated_at"]
            if cached_items is not None and (time.monotonic() - fetched_at) < _RADAR_CACHE_TTL_SECONDS:
                filtered = cached_items
                if category and category != "All":
                    resolved = resolve_canonical_category(category) or category
                    filtered = [i for i in cached_items if i["category"] == resolved]
                return {
                    "total": len(filtered),
                    "generated_at": cached_gen,
                    "server_now": now_utc.isoformat(),
                    "cached": True,
                    "items": filtered,
                }

        active_all = self._query_active_drops(session, now_utc=now_utc, category=None)

        if auto_refresh and self._needs_auto_refresh(session, active_all, now_utc):
            self.refresh_weekly_radar(session=session, force=True)
            active_all = self._query_active_drops(session, now_utc=now_utc, category=None)

        serialized_all = [d.to_dict(now_utc) for d in active_all]
        newest_gen_iso = (
            max(
                (d.generated_at.replace(tzinfo=timezone.utc) if d.generated_at.tzinfo is None else d.generated_at)
                for d in active_all
            ).isoformat()
            if active_all
            else None
        )

        with _RADAR_CACHE_LOCK:
            _RADAR_MEMORY_CACHE["items"] = serialized_all
            _RADAR_MEMORY_CACHE["fetched_at"] = time.monotonic()
            _RADAR_MEMORY_CACHE["generated_at"] = newest_gen_iso

        filtered = serialized_all
        if category and category != "All":
            resolved = resolve_canonical_category(category) or category
            filtered = [i for i in serialized_all if i["category"] == resolved]

        return {
            "total": len(filtered),
            "generated_at": newest_gen_iso,
            "server_now": now_utc.isoformat(),
            "cached": False,
            "items": filtered,
        }
