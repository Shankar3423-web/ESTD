"""RSS/Atom Feed Parser and Normalizer for ESTD Step 1."""
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import feedparser

from backend.common.exceptions.custom_exceptions import RSSInvalidFeedError, RSSParseError
from backend.common.utils.datetime_utils import get_utc_now_iso, normalize_datetime_to_iso
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.rss.sources.models import RSSSource


class RSSParser:
    """Parses raw RSS/Atom feed content using feedparser and normalizes entries to NewsItem."""

    @classmethod
    def parse_feed_content(
        cls,
        raw_content: bytes | str,
        source: RSSSource,
    ) -> List[NewsItem]:
        """Parse raw RSS/Atom XML bytes or string and normalize to NewsItem list.

        Args:
            raw_content: XML content of the feed.
            source: RSSSource metadata configuration.

        Returns:
            List of normalized NewsItem instances.
        """
        try:
            feed = feedparser.parse(raw_content)
        except Exception as err:
            raise RSSParseError(
                source_id=source.source_id,
                message=f"feedparser failed to parse XML: {err}",
            ) from err

        if not hasattr(feed, "entries"):
            raise RSSInvalidFeedError(
                source_id=source.source_id,
                message="Parsed feed object lacks 'entries' attribute.",
            )

        entries = feed.entries
        normalized_items: List[NewsItem] = []
        collected_now = get_utc_now_iso()

        for entry in entries:
            item = cls._normalize_entry(entry, source, collected_now)
            if item:
                normalized_items.append(item)

        return normalized_items

    @classmethod
    def _normalize_entry(
        cls,
        entry: Any,
        source: RSSSource,
        collected_now: str,
    ) -> Optional[NewsItem]:
        """Normalize a single feedparser entry into a NewsItem."""
        # 1. Title
        title = entry.get("title")
        if not title or not str(title).strip():
            return None
        clean_title = str(title).strip()

        # 2. Canonical Article URL (Never feed URL)
        url = cls._extract_link(entry)
        if not url or not str(url).strip():
            return None
        clean_url = str(url).strip()

        # 3. Description / Summary
        description = cls._extract_description(entry)

        # 4. Author
        author = cls._extract_author(entry)

        # 5. Published At
        published_at = cls._extract_published_at(entry)

        # 6. Image URL
        image_url = cls._extract_image_url(entry)

        try:
            return NewsItem(
                title=clean_title,
                description=description,
                url=clean_url,
                source_name=source.source_name,
                source_type="rss",
                author=author,
                published_at=published_at,
                category=source.category,
                subcategory=source.subcategory,
                language=source.language or "en",
                region=source.region,
                image_url=image_url,
                collected_at=collected_now,
            )
        except Exception:
            # Skip invalid entry if schema validation fails
            return None

    @classmethod
    def _extract_link(cls, entry: Any) -> Optional[str]:
        """Extract canonical article link."""
        link = entry.get("link")
        if link and isinstance(link, str) and link.startswith("http"):
            return link

        # Inspect links array if present
        links = entry.get("links", [])
        if isinstance(links, list):
            for l in links:
                if isinstance(l, dict) and l.get("rel") == "alternate" and l.get("href"):
                    return l.get("href")
            for l in links:
                if isinstance(l, dict) and l.get("href") and l.get("href").startswith("http"):
                    return l.get("href")

        return None

    @classmethod
    def _extract_description(cls, entry: Any) -> Optional[str]:
        """Extract article description/summary without HTML bloat where feasible."""
        summary = entry.get("summary") or entry.get("description")
        if summary and isinstance(summary, str) and summary.strip():
            return summary.strip()

        content = entry.get("content")
        if isinstance(content, list) and content:
            first_val = content[0].get("value")
            if first_val and isinstance(first_val, str) and first_val.strip():
                return first_val.strip()

        return None

    @classmethod
    def _extract_author(cls, entry: Any) -> Optional[str]:
        """Extract author or creator."""
        author = entry.get("author")
        if author and isinstance(author, str) and author.strip():
            return author.strip()

        author_detail = entry.get("author_detail")
        if isinstance(author_detail, dict) and author_detail.get("name"):
            name = author_detail.get("name")
            if name and isinstance(name, str) and name.strip():
                return name.strip()

        # Some RSS feeds use dc:creator
        dc_creator = entry.get("dc_creator") or entry.get("creator")
        if dc_creator and isinstance(dc_creator, str) and dc_creator.strip():
            return dc_creator.strip()

        return None

    @classmethod
    def _extract_published_at(cls, entry: Any) -> Optional[str]:
        """Normalize publication timestamp to UTC ISO 8601 string."""
        # 1. Prefer feedparser's 9-tuple struct_time if available
        parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed_time and isinstance(parsed_time, (tuple, time.struct_time)):
            try:
                dt = datetime(*parsed_time[:6], tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass

        # 2. Fall back to raw string normalization
        raw_date = entry.get("published") or entry.get("pubDate") or entry.get("updated")
        return normalize_datetime_to_iso(raw_date)

    @classmethod
    def _extract_image_url(cls, entry: Any) -> Optional[str]:
        """Extract article image or thumbnail from standard RSS/Atom structures."""
        # 1. media:content
        media_content = entry.get("media_content")
        if isinstance(media_content, list) and media_content:
            for media in media_content:
                if isinstance(media, dict) and media.get("url"):
                    media_type = media.get("type", "")
                    media_medium = media.get("medium", "")
                    if media_medium == "image" or "image" in media_type or not media_type:
                        return media.get("url")

        # 2. media:thumbnail
        media_thumbnail = entry.get("media_thumbnail")
        if isinstance(media_thumbnail, list) and media_thumbnail:
            first = media_thumbnail[0]
            if isinstance(first, dict) and first.get("url"):
                return first.get("url")

        # 3. enclosures
        enclosures = entry.get("enclosures")
        if isinstance(enclosures, list) and enclosures:
            for enc in enclosures:
                if isinstance(enc, dict) and enc.get("href"):
                    enc_type = enc.get("type", "")
                    if "image" in enc_type:
                        return enc.get("href")

        return None
