"""Content sufficiency checker to decide whether external scraping is required."""
import re
from typing import Optional, Tuple

from backend.common.logging.logger import logger
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.config import ExtractionConfig, extraction_config

# Patterns commonly indicating truncated preview snippets rather than complete article bodies
TRUNCATION_PATTERNS = [
    re.compile(r"\[\+\d+\s*chars\]", re.IGNORECASE),
    re.compile(r"\b(read more|continue reading|full story at|read full article)\b", re.IGNORECASE),
    re.compile(r"\.{3,}$"),
    re.compile(r"…$"),
]

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


class SufficiencyChecker:
    """Evaluates whether an incoming NewsItem already possesses sufficient content.

    Distinguishes between:
    - Metadata snippets: Brief summaries (typically < 200 characters or < 35 words).
    - Substantive article content: Sizable text (>= min_content_chars and >= min_content_words)
      without truncation indicators, which allows proceeding downstream without an external HTTP fetch.
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or extraction_config

    def evaluate(self, news_item: NewsItem) -> Tuple[bool, Optional[str]]:
        """Evaluate if the news item has sufficient content.

        Args:
            news_item: Step 1 normalized news item.

        Returns:
            Tuple of (is_sufficient: bool, clean_content: Optional[str]).
        """
        # Step 1 NewsItem places text in description (some RSS or API sources provide full text here)
        raw_text = news_item.description

        if not raw_text or not isinstance(raw_text, str):
            logger.info(
                f"[SUFFICIENCY] Insufficient: No text present | title='{news_item.title[:40]}...'"
            )
            return False, None

        # Strip any raw HTML tags if description contained embedded markup
        clean_text = HTML_TAG_PATTERN.sub(" ", raw_text).strip()
        clean_text = re.sub(r"\s+", " ", clean_text)

        char_count = len(clean_text)
        words = clean_text.split()
        word_count = len(words)

        # Check character and word thresholds
        meets_char_limit = char_count >= self.config.min_content_chars
        meets_word_limit = word_count >= self.config.min_content_words

        # Check for truncation markers (e.g. NewsData.io "[+1500 chars]" or "... Read more")
        is_truncated = any(pattern.search(clean_text) for pattern in TRUNCATION_PATTERNS)

        is_sufficient = meets_char_limit and meets_word_limit and not is_truncated

        logger.info(
            f"[SUFFICIENCY] Evaluated content | title='{news_item.title[:40]}...' | "
            f"chars={char_count} (min={self.config.min_content_chars}) | "
            f"words={word_count} (min={self.config.min_content_words}) | "
            f"truncated={is_truncated} | sufficient={is_sufficient}"
        )

        if is_sufficient:
            return True, clean_text

        return False, None
