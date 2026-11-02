"""Unit tests for Step 4 URL and Content normalizers."""
import pytest

from backend.step4_duplicate_detection.normalizers.text_normalizer import (
    normalize_content_for_hash,
)
from backend.step4_duplicate_detection.normalizers.url_normalizer import (
    TRACKING_PARAMS,
    normalize_url,
)


class TestURLNormalizer:
    """Test suite for deterministic URL canonicalization and tracking parameter stripping."""

    def test_scheme_and_host_lowercasing(self):
        url = "HTTPS://WWW.EXAMPLE.COM/Article/123"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/Article/123"

    def test_strips_www_prefix(self):
        url = "https://www.theverge.com/tech/news"
        normalized = normalize_url(url)
        assert normalized == "https://theverge.com/tech/news"

    def test_default_ports_stripped(self):
        assert normalize_url("http://example.com:80/path") == "https://example.com/path" or normalize_url("http://example.com:80/path") == "http://example.com/path"
        assert normalize_url("https://example.com:443/path") == "https://example.com/path"
        # Non-default port must be preserved
        assert ":8080" in normalize_url("https://example.com:8080/path")

    def test_trailing_slash_normalization(self):
        url_with_slash = "https://example.com/news/tech/"
        url_without_slash = "https://example.com/news/tech"
        assert normalize_url(url_with_slash) == normalize_url(url_without_slash)
        assert normalize_url(url_with_slash) == "https://example.com/news/tech"

    def test_root_path_preserved(self):
        assert normalize_url("https://example.com/") == "https://example.com/"

    def test_collapses_consecutive_slashes(self):
        url = "https://example.com//news///tech//article"
        assert normalize_url(url) == "https://example.com/news/tech/article"

    def test_strips_url_fragments(self):
        url = "https://example.com/article/123#comments-section"
        assert normalize_url(url) == "https://example.com/article/123"

    def test_strips_known_marketing_tracking_parameters(self):
        url = (
            "https://example.com/news/ai-launch"
            "?utm_source=twitter&utm_medium=social&utm_campaign=spring2026"
            "&fbclid=IwAR2x123&gclid=Cj0KCQj123&ref=newsletter"
        )
        assert normalize_url(url) == "https://example.com/news/ai-launch"

    def test_preserves_legitimate_content_query_parameters(self):
        url = "https://example.com/story.php?id=98765&section=technology&utm_source=email"
        normalized = normalize_url(url)
        # utm_source must be stripped, but id and section preserved
        assert "utm_source" not in normalized
        assert "id=98765" in normalized
        assert "section=technology" in normalized

    def test_query_parameters_sorted_deterministically(self):
        url_a = "https://example.com/item?category=science&id=42&year=2026"
        url_b = "https://example.com/item?year=2026&id=42&category=science"
        assert normalize_url(url_a) == normalize_url(url_b)

    def test_missing_scheme_defaults_to_https(self):
        url = "techcrunch.com/article/openai"
        assert normalize_url(url) == "https://techcrunch.com/article/openai"

    def test_handles_surrounding_whitespace(self):
        url = "   https://example.com/article/42   \n"
        assert normalize_url(url) == "https://example.com/article/42"

    def test_handles_empty_or_none_url(self):
        assert normalize_url("") == ""
        assert normalize_url("   ") == ""
        assert normalize_url(None) == ""

    def test_tracking_params_set_contains_required_keys(self):
        for key in ["utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid"]:
            assert key in TRACKING_PARAMS


class TestTextNormalizerForHash:
    """Test suite for deterministic canonical text normalization before SHA-256 hashing."""

    def test_collapses_newlines_and_spaces(self):
        text = "OpenAI   released  a new   model.\n\n\nIt features advanced reasoning.\t\t"
        expected = "openai released a new model. it features advanced reasoning."
        assert normalize_content_for_hash(text) == expected

    def test_lowercasing_is_deterministic(self):
        text_a = "BREAKING NEWS: Artificial Intelligence Breakthrough"
        text_b = "breaking news: artificial intelligence breakthrough"
        assert normalize_content_for_hash(text_a) == normalize_content_for_hash(text_b)

    def test_unicode_normalization_nfc(self):
        # Combined vs decomposed accents
        e_acute_composed = "Café"
        e_acute_decomposed = "Cafe\u0301"
        assert normalize_content_for_hash(e_acute_composed) == normalize_content_for_hash(e_acute_decomposed)

    def test_strips_leading_and_trailing_whitespace(self):
        text = "  \n\t  Content text body here.   \r\n  "
        assert normalize_content_for_hash(text) == "content text body here."

    def test_handles_none_and_empty_inputs(self):
        assert normalize_content_for_hash(None) == ""
        assert normalize_content_for_hash("") == ""
        assert normalize_content_for_hash("   \n\t ") == ""
