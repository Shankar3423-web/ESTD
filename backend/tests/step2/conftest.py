"""Pytest fixtures for Step 2 Article Scraping and Extraction test suite."""
from pathlib import Path
import pytest

from backend.step1_source_collection.models.news_item import NewsItem

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return Path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def valid_article_html() -> str:
    """Return raw HTML of valid_article.html."""
    return (FIXTURES_DIR / "article_valid.html").read_text(encoding="utf-8")


@pytest.fixture
def candidate_class_html() -> str:
    """Return raw HTML of article_candidate_class.html."""
    return (FIXTURES_DIR / "article_candidate_class.html").read_text(encoding="utf-8")


@pytest.fixture
def missing_body_html() -> str:
    """Return raw HTML of article_missing_body.html."""
    return (FIXTURES_DIR / "article_missing_body.html").read_text(encoding="utf-8")


@pytest.fixture
def jsonld_body_html() -> str:
    """Return raw HTML of article_jsonld_body.html."""
    return (FIXTURES_DIR / "article_jsonld_body.html").read_text(encoding="utf-8")


@pytest.fixture
def sample_news_item_snippet() -> NewsItem:
    """Sample NewsItem with only short metadata snippet (insufficient content)."""
    return NewsItem(
        title="DeepMind Unveils Next-Gen AI System",
        description="A short news snippet announcing a new neural reasoning architecture.",
        url="https://technews.example.com/articles/deepmind-breakthrough",
        source_name="TechNews",
        source_type="gnews",
        author="Dr. Alan Turing",
        published_at="2026-09-29T14:30:00Z",
        category="Artificial Intelligence",
        image_url="https://example.com/thumb.jpg",
        collected_at="2026-09-29T15:00:00Z",
    )


@pytest.fixture
def sample_news_item_full_content() -> NewsItem:
    """Sample NewsItem with sufficient existing content (>= 250 chars, >= 40 words)."""
    full_body = (
        "Researchers at Google DeepMind today unveiled a revolutionary artificial intelligence "
        "architecture designed to tackle multi-step algorithmic reasoning with unprecedented efficiency. "
        "The new approach reduces floating point operations by over forty percent while dramatically "
        "outperforming previous frontier baselines on standard competitive programming benchmarks. "
        "Commercial deployment is slated to begin later this quarter across developer workstations globally."
    )
    return NewsItem(
        title="DeepMind Reasoning Architecture Breakthrough",
        description=full_body,
        url="https://technews.example.com/articles/full-story",
        source_name="TechNews Daily",
        source_type="rss",
        author="Editorial Board",
        published_at="2026-09-29T14:30:00Z",
        category="Artificial Intelligence",
        image_url="https://example.com/full.jpg",
        collected_at="2026-09-29T15:00:00Z",
    )


@pytest.fixture
def sample_news_item_truncated() -> NewsItem:
    """Sample NewsItem with truncated snippet marker like [+1400 chars]."""
    truncated_body = (
        "A major breakthrough was reported in renewable storage technologies earlier this morning "
        "by energy consortia in Northern Europe. The initiative seeks to expand regional grid storage... "
        "[+1820 chars]"
    )
    return NewsItem(
        title="Renewable Energy Storage Consortium",
        description=truncated_body,
        url="https://energy.example.com/storage",
        source_name="NewsData Provider",
        source_type="newsdata",
        category="Technology",
        collected_at="2026-09-29T15:00:00Z",
    )
