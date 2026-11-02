"""Pytest fixtures for Step 3 Content Cleaning & Normalization test suite."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.step2_article_extraction.models import (
    ExtractedArticle,
    ExtractionMethod,
    ExtractionStatus,
)


@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def sample_extracted_article_clean() -> ExtractedArticle:
    """Sample ExtractedArticle that is already clean plain text."""
    body = (
        "Researchers at Massachusetts Institute of Technology have unveiled a new computational framework "
        "for modeling nanoscale fluid dynamics. The breakthrough provides fresh insights into biological "
        "filtration mechanisms and could accelerate the design of next-generation synthetic membranes.\n\n"
        "Lead author Dr. Katherine Vance stated that experimental validation confirmed theoretical "
        "predictions across multiple laboratory trials over eighteen months."
    )
    return ExtractedArticle(
        title="MIT Researchers Announce Nanoscale Fluid Breakthrough",
        description="A major breakthrough in fluid dynamics at the nanoscale.",
        url="https://mitnews.example.com/2026/nanoscale-fluid",
        source_name="MIT News",
        source_type="rss",
        author="Dr. Katherine Vance",
        published_at="2026-09-30T10:00:00Z",
        category="Science",
        image_url="https://mitnews.example.com/images/nano.jpg",
        collected_at="2026-09-30T10:15:00Z",
        canonical_url="https://mitnews.example.com/2026/nanoscale-fluid",
        extraction_status=ExtractionStatus.EXTRACTED,
        extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        extracted_at="2026-09-30T10:15:05Z",
        content=body,
    )


@pytest.fixture
def sample_extracted_article_with_html() -> ExtractedArticle:
    """Sample ExtractedArticle containing HTML markup and entities."""
    html_body = (
        "<p>Google DeepMind announced its latest autonomous reasoning system today &amp; demonstrated "
        "significant performance improvements on standard mathematical benchmarks.</p>"
        "<div class='ad-banner'>Advertisement</div>"
        "<p>The new model relies on an adaptive tree-search mechanism that evaluates solution candidates "
        "in parallel, according to company engineers.</p>"
    )
    return ExtractedArticle(
        title="DeepMind Announces Autonomous Reasoning System",
        description="Performance improvements on math benchmarks.",
        url="https://technews.example.com/deepmind-math",
        source_name="TechNews",
        source_type="gnews",
        author="Alex Rivera",
        published_at="2026-09-30T12:00:00Z",
        category="Artificial Intelligence",
        collected_at="2026-09-30T12:05:00Z",
        extraction_status=ExtractionStatus.EXTRACTED,
        extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        content=html_body,
    )


@pytest.fixture
def sample_extracted_article_with_boilerplate() -> ExtractedArticle:
    """Sample ExtractedArticle containing webpage noise like ads, cookie banners, and social sharing."""
    noise_body = (
        "We use cookies to improve your experience on our website. Accept all cookies.\n\n"
        "ADVERTISEMENT\n\n"
        "European central bankers convened in Frankfurt this morning to deliberate on monetary policy "
        "adjustments following quarterly inflation data. Financial markets reacted with moderate gains.\n\n"
        "Sign up for our daily newsletter to get market updates delivered to your inbox.\n\n"
        "Analysts anticipate that borrowing rates will remain steady throughout the upcoming fiscal quarter.\n\n"
        "Share this article on Twitter | Share on LinkedIn\n\n"
        "Related stories: Five trends shaping European bond yields\n\n"
        "All rights reserved. Copyright 2026 Financial Times Inc."
    )
    return ExtractedArticle(
        title="European Central Bankers Meet on Interest Rates",
        description="Deliberations follow quarterly inflation reports.",
        url="https://finance.example.com/ecb-meeting",
        source_name="Financial Times",
        source_type="newsdata",
        author="Maria Schmidt",
        published_at="2026-09-30T09:00:00Z",
        category="Business",
        collected_at="2026-09-30T09:10:00Z",
        extraction_status=ExtractionStatus.EXTRACTED,
        content=noise_body,
    )


@pytest.fixture
def sample_extracted_article_empty_content() -> ExtractedArticle:
    """Sample ExtractedArticle with empty/None content."""
    return ExtractedArticle(
        title="Empty Article Example",
        description="Has no body content.",
        url="https://empty.example.com/article",
        source_type="rss",
        category="Technology",
        collected_at="2026-09-30T14:00:00Z",
        extraction_status=ExtractionStatus.EXTRACTION_FAILED,
        content=None,
    )
