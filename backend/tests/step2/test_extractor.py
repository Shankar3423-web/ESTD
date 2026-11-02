"""Unit tests for Step 2 ArticleExtractor, ContentExtractor, and MetadataExtractor."""
import pytest

from backend.step2_article_extraction.exceptions import (
    ContentExtractionError,
    EmptyWebpageError,
)
from backend.step2_article_extraction.extractors.article_extractor import (
    ArticleExtractor,
)


def test_extractor_valid_article(valid_article_html):
    """Rich article HTML extracts all metadata and multi-paragraph content cleanly."""
    extractor = ArticleExtractor()
    data = extractor.extract(
        valid_article_html,
        url="https://technews.example.com/articles/deepmind-breakthrough",
    )

    # Content
    assert data["content"] is not None
    assert "Google DeepMind" in data["content"]
    assert "competitive programming benchmarks" in data["content"]
    # Verify noise removal: sidebar ad and footer should NOT be in body
    assert "Advertisement" not in data["content"]
    assert "All rights reserved" not in data["content"]

    # Metadata
    assert data["title"] == "DeepMind Unveils Next-Gen AI System"
    assert data["author"] == "Dr. Alan Turing"
    assert data["published_at"] == "2026-09-29T14:30:00Z"
    assert data["canonical_url"] == "https://technews.example.com/articles/deepmind-breakthrough"
    assert data["image_url"] == "https://example.com/images/deepmind-breakthrough.jpg"
    assert data["source_name"] == "TechNews Daily"


def test_extractor_candidate_class_article(candidate_class_html):
    """Article container identified via candidate class (e.g. story-content) extracts properly."""
    extractor = ArticleExtractor()
    data = extractor.extract(
        candidate_class_html,
        url="https://quantum.example.com/milestone",
    )

    assert data["content"] is not None
    assert "fault-tolerant logical qubits" in data["content"]
    assert data["author"] == "Marie Curie"
    assert data["title"] == "Quantum Computing Milestones Reached in 2026"


def test_extractor_jsonld_body_extraction(jsonld_body_html):
    """Extraction leverages Schema.org JSON-LD articleBody when available."""
    extractor = ArticleExtractor()
    data = extractor.extract(
        jsonld_body_html,
        url="https://energy.example.com/solid-state",
    )

    assert data["content"] is not None
    assert "ceramic composite electrolyte" in data["content"].lower()
    assert data["author"] == "Prof. John Goodenough"
    assert data["published_at"] == "2026-09-28T09:15:00Z"


def test_extractor_missing_body_raises_error(missing_body_html):
    """Pages with only login forms/headers and no readable body raise ContentExtractionError."""
    extractor = ArticleExtractor()
    with pytest.raises(ContentExtractionError):
        extractor.extract(
            missing_body_html,
            url="https://paywall.example.com/report",
        )


def test_extractor_empty_html_raises_error():
    """Empty HTML string raises EmptyWebpageError."""
    extractor = ArticleExtractor()
    with pytest.raises(EmptyWebpageError):
        extractor.extract("", url="https://example.com/empty")


def test_extractor_malformed_html_handling():
    """Malformed HTML with unclosed tags is handled robustly without crashing."""
    malformed_html = """
    <html>
    <head><title>Malformed Headline</title></head>
    <body>
    <div class="article-body">
        <p>This is paragraph one describing unexpected developments in autonomous aerospace navigation.
        <p>This is paragraph two detailing the trajectory optimizations validated during atmospheric re-entry simulations.
        <span>Unclosed span without closing tag
    """
    extractor = ArticleExtractor()
    data = extractor.extract(malformed_html, url="https://aero.example.com/story")

    assert data["content"] is not None
    assert "aerospace navigation" in data["content"]
    assert "trajectory optimizations" in data["content"]
