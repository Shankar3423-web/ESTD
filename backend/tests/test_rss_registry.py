"""Unit tests for RSS Source Registry and RSSSource model."""
import pytest
from pydantic import ValidationError

from backend.common.constants.categories import ESTDCategory, VALID_CATEGORIES
from backend.step1_source_collection.rss.sources.models import RSSSource
from backend.step1_source_collection.rss.sources.registry import (
    DEFAULT_RSS_SOURCES,
    RSSSourceRegistry,
)


def test_rss_source_valid_creation():
    """Verify creating a valid RSSSource object."""
    src = RSSSource(
        source_id="test_src_1",
        source_name="Sample Journal",
        publisher="Global Publisher",
        feed_url="https://example.com/rss.xml",
        category="Developments",
        enabled=True,
    )
    assert src.source_id == "test_src_1"
    assert src.category == "Developments"
    assert src.enabled is True


def test_rss_source_invalid_category_rejected():
    """Verify that RSSSource rejects non-ESTD categories."""
    with pytest.raises(ValidationError) as exc_info:
        RSSSource(
            source_id="invalid_cat_src",
            source_name="Invalid Source",
            publisher="Bad Pub",
            feed_url="https://example.com/feed",
            category="UnrecognizedTopicXYZ",
        )
    assert "Invalid category 'UnrecognizedTopicXYZ'" in str(exc_info.value)


def test_registry_contains_all_five_categories():
    """Verify default registry covers all 5 official ESTD categories."""
    reg = RSSSourceRegistry()
    for cat in VALID_CATEGORIES:
        sources = reg.get_sources_by_category(cat)
        assert len(sources) >= 1, f"Missing default RSS sources for category '{cat}'"


def test_registry_unique_source_ids():
    """Verify all default RSS sources have distinct IDs."""
    ids = [s.source_id for s in DEFAULT_RSS_SOURCES]
    assert len(ids) == len(set(ids)), "Duplicate source_id detected in default registry!"


def test_registry_valid_feed_urls():
    """Verify all default sources have valid HTTP/HTTPS URLs."""
    for s in DEFAULT_RSS_SOURCES:
        assert s.feed_url.startswith("http://") or s.feed_url.startswith("https://")


def test_registry_enabled_filter():
    """Verify enabled_only filtering logic in registry."""
    src_enabled = RSSSource(
        source_id="s_en",
        source_name="Enabled Source",
        publisher="Pub",
        feed_url="https://example.com/feed1",
        category="Technology",
        enabled=True,
    )
    src_disabled = RSSSource(
        source_id="s_dis",
        source_name="Disabled Source",
        publisher="Pub",
        feed_url="https://example.com/feed2",
        category="Technology",
        enabled=False,
    )
    reg = RSSSourceRegistry(initial_sources=[src_enabled, src_disabled])

    all_sources = reg.get_all_sources(enabled_only=False)
    enabled_sources = reg.get_all_sources(enabled_only=True)

    assert len(all_sources) == 2
    assert len(enabled_sources) == 1
    assert enabled_sources[0].source_id == "s_en"


def test_registry_register_source():
    """Verify adding/updating a source in the registry."""
    reg = RSSSourceRegistry(initial_sources=[])
    new_src = RSSSource(
        source_id="custom_tech_feed",
        source_name="Custom Tech",
        publisher="Tech Media",
        feed_url="https://tech.example.com/feed",
        category=ESTDCategory.TECH.value,
        enabled=True,
    )
    reg.register_source(new_src)
    assert reg.get_source_by_id("custom_tech_feed") == new_src
    assert len(reg.get_sources_by_category("Tech")) == 1


def test_registry_get_sources_by_subcategory():
    """Verify registry filters sources by subcategory."""
    reg = RSSSourceRegistry()
    movie_sources = reg.get_sources_by_subcategory("Movies & Cinema")
    assert len(movie_sources) >= 1
    for s in movie_sources:
        assert s.subcategory == "Movies & Cinema"
        assert s.category == "Entertainment"

    cricket_sources = reg.get_sources_by_subcategory("Cricket")
    assert len(cricket_sources) >= 1
    for s in cricket_sources:
        assert s.subcategory == "Cricket"
        assert s.category == "Sports"
