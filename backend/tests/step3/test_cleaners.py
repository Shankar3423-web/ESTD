"""Unit tests for Step 3 cleaners (HTMLCleaner, BoilerplateCleaner, ParagraphCleaner)."""
import pytest

from backend.step3_content_cleaning.cleaners.boilerplate_cleaner import BoilerplateCleaner
from backend.step3_content_cleaning.cleaners.html_cleaner import HTMLCleaner
from backend.step3_content_cleaning.cleaners.paragraph_cleaner import ParagraphCleaner


# ============================================================================
# HTML Cleaner Tests
# ============================================================================

def test_html_cleaner_removes_tags_and_preserves_text():
    cleaner = HTMLCleaner()
    raw = "<p>Researchers discovered a new energy source.</p><div>Laboratory tests confirmed the result.</div>"
    cleaned = cleaner.clean(raw)
    assert "Researchers discovered a new energy source." in cleaned
    assert "Laboratory tests confirmed the result." in cleaned
    assert "<p>" not in cleaned
    assert "<div>" not in cleaned


def test_html_cleaner_discards_scripts_styles_and_nav():
    cleaner = HTMLCleaner()
    raw = (
        "<script>console.log('secret');</script>"
        "<style>body { color: red; }</style>"
        "<nav><a href='/home'>Home</a></nav>"
        "<article><p>Valid article paragraph content.</p></article>"
        "<footer><p>Footer links</p></footer>"
    )
    cleaned = cleaner.clean(raw)
    assert "console.log" not in cleaned
    assert "body { color: red; }" not in cleaned
    assert "Home" not in cleaned
    assert "Footer links" not in cleaned
    assert "Valid article paragraph content." in cleaned


def test_html_cleaner_unescapes_entities():
    cleaner = HTMLCleaner()
    raw = "<p>AT&amp;T &quot;launches&quot; 5G&#39;s &lt;Ultra&gt; network &nbsp; today.</p>"
    cleaned = cleaner.clean(raw)
    assert 'AT&T "launches" 5G\'s <Ultra> network' in cleaned


def test_html_cleaner_handles_malformed_html_gracefully():
    cleaner = HTMLCleaner()
    malformed = "<p>Unclosed paragraph <div>Missing end tags <span>Nested content"
    cleaned = cleaner.clean(malformed)
    assert "Unclosed paragraph" in cleaned
    assert "Missing end tags" in cleaned
    assert "Nested content" in cleaned


def test_html_cleaner_handles_empty_and_plain_text():
    cleaner = HTMLCleaner()
    assert cleaner.clean("") == ""
    assert cleaner.clean(None) == ""
    plain = "Just a regular text string without tags."
    assert cleaner.clean(plain) == plain


# ============================================================================
# Boilerplate Cleaner Tests
# ============================================================================

def test_boilerplate_cleaner_removes_advertisement_markers():
    cleaner = BoilerplateCleaner()
    text = (
        "ADVERTISEMENT\n\n"
        "Tech giant reported record quarterly earnings on Thursday.\n\n"
        "Sponsored Content\n\n"
        "Cloud revenues rose thirty percent year-over-year."
    )
    cleaned = cleaner.remove_boilerplate(text)
    assert "ADVERTISEMENT" not in cleaned
    assert "Sponsored Content" not in cleaned
    assert "Tech giant reported record quarterly earnings on Thursday." in cleaned
    assert "Cloud revenues rose thirty percent year-over-year." in cleaned


def test_boilerplate_cleaner_removes_cookie_banners():
    cleaner = BoilerplateCleaner()
    text = (
        "We use cookies to improve your experience on our website. Accept all cookies.\n\n"
        "Quantum computing researchers at Delft achieved coherent superposition.\n\n"
        "Cookie Policy | Manage Preferences"
    )
    cleaned = cleaner.remove_boilerplate(text)
    assert "We use cookies" not in cleaned
    assert "Cookie Policy" not in cleaned
    assert "Quantum computing researchers at Delft achieved coherent superposition." in cleaned


def test_boilerplate_cleaner_removes_newsletter_and_social_prompts():
    cleaner = BoilerplateCleaner()
    text = (
        "Astronomers detected an unusual gravitational wave signature.\n\n"
        "Sign up for our daily newsletter to get science news in your inbox.\n\n"
        "The signal matches the predicted merger of two intermediate-mass black holes.\n\n"
        "Share this article on Twitter | Follow us on LinkedIn"
    )
    cleaned = cleaner.remove_boilerplate(text)
    assert "Sign up for our daily newsletter" not in cleaned
    assert "Share this article on Twitter" not in cleaned
    assert "Astronomers detected an unusual gravitational wave signature." in cleaned
    assert "The signal matches the predicted merger" in cleaned


def test_boilerplate_cleaner_preserves_legitimate_news_mentioning_keywords():
    cleaner = BoilerplateCleaner()
    text = (
        "Google announced it will deprecate third-party advertising cookies by next year.\n\n"
        "The decision drew strong reactions from digital marketing consortia across the globe."
    )
    cleaned = cleaner.remove_boilerplate(text)
    # Legitimate multi-word article paragraphs discussing cookies/advertising MUST be preserved
    assert "Google announced it will deprecate third-party advertising cookies" in cleaned
    assert "digital marketing consortia across the globe" in cleaned


def test_boilerplate_cleaner_removes_related_and_read_more():
    cleaner = BoilerplateCleaner()
    text = (
        "Robotics lab unveiled a two-legged walker capable of dynamic balance on ice.\n\n"
        "Read more: Boston Dynamics reveals new hydraulic actuator system\n\n"
        "Field trials will begin in sub-zero alpine conditions next month."
    )
    cleaned = cleaner.remove_boilerplate(text)
    assert "Read more:" not in cleaned
    assert "Robotics lab unveiled a two-legged walker" in cleaned
    assert "Field trials will begin" in cleaned


# ============================================================================
# Paragraph Cleaner Tests
# ============================================================================

def test_paragraph_cleaner_removes_empty_and_decorative_paragraphs():
    cleaner = ParagraphCleaner(deduplicate_repeated=True)
    text = (
        "First meaningful paragraph.\n\n"
        "   \n\n"
        "---\n\n"
        "***\n\n"
        "Second meaningful paragraph.\n\n"
        "###\n\n"
        "."
    )
    cleaned = cleaner.clean_paragraphs(text)
    assert cleaned == "First meaningful paragraph.\n\nSecond meaningful paragraph."


def test_paragraph_cleaner_conservative_duplicate_removal():
    cleaner = ParagraphCleaner(deduplicate_repeated=True)
    text = (
        "Paragraph Alpha.\n\n"
        "Paragraph Beta.\n\n"
        "Paragraph Alpha.\n\n"
        "Paragraph Gamma."
    )
    cleaned = cleaner.clean_paragraphs(text)
    assert cleaned == "Paragraph Alpha.\n\nParagraph Beta.\n\nParagraph Gamma."


def test_paragraph_cleaner_preserves_order_and_lists():
    cleaner = ParagraphCleaner(deduplicate_repeated=True)
    text = (
        "Key findings from the study include:\n\n"
        "1. Atmospheric carbon concentrations stabilized slightly in regional basins.\n\n"
        "2. Reforestation initiatives showed measurable cooling effects within five years."
    )
    cleaned = cleaner.clean_paragraphs(text)
    assert "1. Atmospheric carbon concentrations" in cleaned
    assert "2. Reforestation initiatives" in cleaned
    assert cleaned.startswith("Key findings")
