"""Unit tests for Step 3 normalizers (UnicodeNormalizer, WhitespaceNormalizer, TextNormalizer)."""
import pytest

from backend.step3_content_cleaning.normalizers.text_normalizer import TextNormalizer
from backend.step3_content_cleaning.normalizers.unicode_normalizer import UnicodeNormalizer
from backend.step3_content_cleaning.normalizers.whitespace_normalizer import WhitespaceNormalizer


# ============================================================================
# Unicode Normalizer Tests
# ============================================================================

def test_unicode_normalizer_quotes_and_apostrophes():
    normalizer = UnicodeNormalizer()
    text = "“Smart quotes” and ‘smart apostrophe’s’ plus «guillemets»."
    normalized = normalizer.normalize(text)
    assert normalized == '"Smart quotes" and \'smart apostrophe\'s\' plus "guillemets".'


def test_unicode_normalizer_dashes_and_hyphens():
    normalizer = UnicodeNormalizer()
    text = "Breakthrough—announced today–by researchers−collaborators."
    normalized = normalizer.normalize(text)
    assert normalized == "Breakthrough-announced today-by researchers-collaborators."


def test_unicode_normalizer_non_breaking_and_exotic_spaces():
    normalizer = UnicodeNormalizer()
    # \u00a0 is non-breaking space, \u2009 is thin space
    text = "Word1\u00a0Word2\u2009Word3"
    normalized = normalizer.normalize(text)
    assert normalized == "Word1 Word2 Word3"


def test_unicode_normalizer_strips_invisible_characters():
    normalizer = UnicodeNormalizer()
    # \u200b is zero-width space, \ufeff is BOM
    text = "Clean\u200bText\ufeffHere\u00adNow"
    normalized = normalizer.normalize(text)
    assert normalized == "CleanTextHereNow"


def test_unicode_normalizer_preserves_international_characters():
    normalizer = UnicodeNormalizer()
    text = "Café résumé München São Paulo 東京 Москва"
    normalized = normalizer.normalize(text)
    assert normalized == "Café résumé München São Paulo 東京 Москва"


# ============================================================================
# Whitespace Normalizer Tests
# ============================================================================

def test_whitespace_normalizer_repeated_spaces_and_tabs():
    normalizer = WhitespaceNormalizer()
    text = "Researchers     discovered\t\ta new      synthetic    compound."
    normalized = normalizer.normalize(text)
    assert normalized == "Researchers discovered a new synthetic compound."


def test_whitespace_normalizer_line_endings_and_blank_lines():
    normalizer = WhitespaceNormalizer(max_consecutive_blank_lines=2)
    text = "Paragraph 1\r\n\r\n\r\n\r\n\r\nParagraph 2\n\n\n\nParagraph 3"
    normalized = normalizer.normalize(text)
    # Consecutive blank lines capped at 2 newlines (standard double newline between paragraphs)
    assert normalized == "Paragraph 1\n\nParagraph 2\n\nParagraph 3"


def test_whitespace_normalizer_preserves_paragraph_boundaries():
    normalizer = WhitespaceNormalizer()
    text = "Headline\n\nParagraph one.\n\nParagraph two.\n\nParagraph three."
    normalized = normalizer.normalize(text)
    assert normalized == "Headline\n\nParagraph one.\n\nParagraph two.\n\nParagraph three."


def test_whitespace_normalizer_handles_empty():
    normalizer = WhitespaceNormalizer()
    assert normalizer.normalize("") == ""
    assert normalizer.normalize("   \t  \n  ") == ""
    assert normalizer.normalize(None) == ""


# ============================================================================
# Composite Text Normalizer Tests
# ============================================================================

def test_text_normalizer_pipeline():
    normalizer = TextNormalizer()
    text = "“Scientists     reported\t\ta—breakthrough”\n\n\n\nIn   fluid   dynamics."
    normalized = normalizer.normalize(text)
    assert normalized == '"Scientists reported a-breakthrough"\n\nIn fluid dynamics.'
