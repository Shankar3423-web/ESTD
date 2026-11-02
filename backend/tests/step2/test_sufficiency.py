"""Unit tests for Step 2 Content Sufficiency Checker."""
import pytest

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.config import ExtractionConfig
from backend.step2_article_extraction.extractors.sufficiency_checker import (
    SufficiencyChecker,
)


def test_sufficiency_no_description():
    """Item with None or empty description must be determined insufficient."""
    item = NewsItem(
        title="Test Title",
        description=None,
        url="https://example.com/item1",
        source_type="gnews",
        category="Technology",
    )
    checker = SufficiencyChecker()
    is_sufficient, content = checker.evaluate(item)
    assert is_sufficient is False
    assert content is None


def test_sufficiency_short_snippet():
    """Short summary snippet must be determined insufficient."""
    item = NewsItem(
        title="Test Title",
        description="Just a brief headline snippet of twenty words.",
        url="https://example.com/item2",
        source_type="gnews",
        category="Technology",
    )
    checker = SufficiencyChecker()
    is_sufficient, content = checker.evaluate(item)
    assert is_sufficient is False
    assert content is None


def test_sufficiency_meaningful_content(sample_news_item_full_content):
    """Substantial article text must be determined sufficient."""
    checker = SufficiencyChecker()
    is_sufficient, content = checker.evaluate(sample_news_item_full_content)
    assert is_sufficient is True
    assert content is not None
    assert len(content) >= checker.config.min_content_chars
    assert "Google DeepMind" in content


def test_sufficiency_truncated_pattern_detected(sample_news_item_truncated):
    """Items ending in truncation markers like [+1820 chars] must be deemed insufficient."""
    checker = SufficiencyChecker()
    is_sufficient, content = checker.evaluate(sample_news_item_truncated)
    assert is_sufficient is False
    assert content is None


def test_sufficiency_read_more_pattern_detected():
    """Items with 'continue reading' or 'read more' must be deemed insufficient."""
    text = (
        "This is an article that looks long at first glance because it describes an emerging "
        "energy storage framework in great depth across multiple sentences with lots of technical "
        "terminology and descriptions of electrochemical interactions. Continue reading the full story at the publisher site."
    )
    item = NewsItem(
        title="Energy Storage",
        description=text,
        url="https://example.com/energy",
        source_type="newsdata",
        category="Science",
    )
    checker = SufficiencyChecker()
    is_sufficient, content = checker.evaluate(item)
    assert is_sufficient is False


def test_sufficiency_html_tags_stripped():
    """HTML markup in RSS description is stripped before evaluation."""
    raw_html = (
        "<p>Researchers at the National Institute of Standards have announced a comprehensive "
        "methodology for characterizing semiconductor quantum dots with atomic-scale resolution. "
        "The findings represent a significant milestone for nanoscale solid-state physics and will "
        "accelerate precision manufacturing across next-generation optoelectronic devices worldwide.</p>"
    )
    item = NewsItem(
        title="Quantum Dots",
        description=raw_html,
        url="https://example.com/quantum",
        source_type="rss",
        category="Science",
    )
    checker = SufficiencyChecker()
    is_sufficient, content = checker.evaluate(item)
    assert is_sufficient is True
    assert "<p>" not in content
    assert "</p>" not in content


def test_sufficiency_custom_config():
    """Custom configuration thresholds are respected."""
    custom_cfg = ExtractionConfig(
        EXTRACTION_MIN_CONTENT_CHARS=50,
        EXTRACTION_MIN_CONTENT_WORDS=8,
    )
    checker = SufficiencyChecker(config=custom_cfg)
    item = NewsItem(
        title="Short Item",
        description="This is a moderately short description with ten words here.",
        url="https://example.com/short",
        source_type="rss",
        category="Business",
    )
    is_sufficient, content = checker.evaluate(item)
    assert is_sufficient is True
    assert content is not None
