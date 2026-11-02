"""Unit tests for RSSParser and normalization into NewsItem."""
import pytest

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.rss.services.rss_parser import RSSParser
from backend.step1_source_collection.rss.sources.models import RSSSource


def test_parse_valid_rss_2(sample_rss_xml, sample_rss_source):
    """Verify parsing standard RSS 2.0 feed with author, media, and dates."""
    items = RSSParser.parse_feed_content(sample_rss_xml, sample_rss_source)

    assert len(items) == 2
    # Item 1
    item1 = items[0]
    assert isinstance(item1, NewsItem)
    assert item1.title == "Autonomous Drones Deliver Medical Supplies"
    assert item1.url == "https://example.com/articles/autonomous-drones"
    assert item1.source_name == sample_rss_source.source_name
    assert item1.source_type == "rss"
    assert item1.category == "Tech"
    assert item1.author == "Dr. Elena Rostova"
    assert item1.published_at == "2026-09-30T09:00:00Z"
    assert item1.image_url == "https://example.com/images/drone.jpg"
    assert item1.collected_at.endswith("Z")

    # Item 2
    item2 = items[1]
    assert item2.title == "Neuromorphic Chip Emulates Synaptic Plasticity"
    assert item2.url == "https://example.com/articles/neuromorphic-chip"
    assert "Sarah Chen" in (item2.author or "")
    assert item2.published_at == "2026-09-29T18:30:00Z"
    assert item2.image_url == "https://example.com/images/chip.png"


def test_parse_valid_atom(sample_atom_xml):
    """Verify parsing standard Atom feed."""
    atom_source = RSSSource(
        source_id="science_atom",
        source_name="Science Atom Journal",
        publisher="Global Science",
        feed_url="https://example.com/science-feed",
        category="Developments",
        enabled=True,
    )
    items = RSSParser.parse_feed_content(sample_atom_xml, atom_source)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Gravitational Wave Observatory Detects Intermediate Black Hole Merger"
    assert item.url == "https://example.com/articles/gravitational-wave"
    assert item.source_name == "Science Atom Journal"
    assert item.source_type == "rss"
    assert item.category == "Developments"
    assert item.author == "Astrophysics Collaboration"
    assert item.published_at == "2026-09-30T07:45:00Z"


def test_parse_empty_feed(sample_rss_source):
    """Verify parsing an RSS feed with 0 items."""
    empty_xml = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Empty Feed</title>
        <link>https://example.com</link>
      </channel>
    </rss>
    """
    items = RSSParser.parse_feed_content(empty_xml, sample_rss_source)
    assert items == []


def test_parse_skips_entries_missing_title_or_link(sample_rss_source):
    """Verify entries missing title or canonical link are skipped."""
    xml_with_invalid_entries = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Mixed Feed</title>
        <item>
          <!-- Missing title -->
          <link>https://example.com/missing-title</link>
          <description>Has link but no title</description>
        </item>
        <item>
          <!-- Missing link -->
          <title>Has Title But No Link</title>
          <description>Missing link</description>
        </item>
        <item>
          <!-- Valid entry -->
          <title>Valid Complete Entry</title>
          <link>https://example.com/complete</link>
          <description>Valid</description>
        </item>
      </channel>
    </rss>
    """
    items = RSSParser.parse_feed_content(xml_with_invalid_entries, sample_rss_source)
    assert len(items) == 1
    assert items[0].title == "Valid Complete Entry"
    assert items[0].url == "https://example.com/complete"


def test_parse_optional_fields_as_none(sample_rss_source):
    """Verify that entries without author, image, or description leave those fields as None."""
    minimal_xml = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>Minimal</title>
        <item>
          <title>Minimal Article</title>
          <link>https://example.com/minimal-article</link>
        </item>
      </channel>
    </rss>
    """
    items = RSSParser.parse_feed_content(minimal_xml, sample_rss_source)
    assert len(items) == 1
    item = items[0]
    assert item.title == "Minimal Article"
    assert item.description is None
    assert item.author is None
    assert item.published_at is None
    assert item.image_url is None


def test_parse_malformed_xml_handling(sample_rss_source):
    """Verify malformed XML does not ungracefully crash."""
    malformed_xml = "<html><body>This is definitely not XML <item><title>Broken"
    items = RSSParser.parse_feed_content(malformed_xml, sample_rss_source)
    assert isinstance(items, list)
