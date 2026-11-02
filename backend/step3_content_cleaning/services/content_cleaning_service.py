"""ContentCleaningService orchestrating HTML cleanup, boilerplate removal, and normalization."""
import time
from typing import List, Optional

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.logging.logger import logger
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step3_content_cleaning.cleaners.boilerplate_cleaner import BoilerplateCleaner
from backend.step3_content_cleaning.cleaners.html_cleaner import HTMLCleaner
from backend.step3_content_cleaning.cleaners.paragraph_cleaner import ParagraphCleaner
from backend.step3_content_cleaning.config import CleaningConfig, cleaning_config
from backend.step3_content_cleaning.exceptions.cleaning_exceptions import (
    CleaningException,
)
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.normalizers.unicode_normalizer import UnicodeNormalizer
from backend.step3_content_cleaning.normalizers.whitespace_normalizer import WhitespaceNormalizer


class ContentCleaningService:
    """Core service orchestrating deterministic Step 3 article cleaning and normalization."""

    def __init__(
        self,
        config: Optional[CleaningConfig] = None,
        html_cleaner: Optional[HTMLCleaner] = None,
        boilerplate_cleaner: Optional[BoilerplateCleaner] = None,
        paragraph_cleaner: Optional[ParagraphCleaner] = None,
        unicode_normalizer: Optional[UnicodeNormalizer] = None,
        whitespace_normalizer: Optional[WhitespaceNormalizer] = None,
    ):
        self.config = config or cleaning_config
        self.html_cleaner = html_cleaner or HTMLCleaner()
        self.boilerplate_cleaner = boilerplate_cleaner or BoilerplateCleaner()
        self.paragraph_cleaner = paragraph_cleaner or ParagraphCleaner(
            deduplicate_repeated=self.config.enable_repeated_paragraph_removal
        )
        self.unicode_normalizer = unicode_normalizer or UnicodeNormalizer()
        self.whitespace_normalizer = whitespace_normalizer or WhitespaceNormalizer(
            max_consecutive_blank_lines=self.config.max_consecutive_blank_lines
        )

    def clean_article(self, article: ExtractedArticle) -> CleanedArticle:
        """Process a single ExtractedArticle through the cleaning and normalization pipeline.

        Deterministic pipeline:
        1. Input Validation
        2. HTML/Text Cleanup
        3. Boilerplate Removal
        4. Unicode Normalization
        5. Whitespace Normalization
        6. Paragraph Cleanup & Deduplication
        7. Output Validation
        8. Produce CleanedArticle
        """
        start_time = time.perf_counter()
        logger.info(
            f"[CLEANING_SERVICE] Cleaning started | title='{article.title[:50]}' | "
            f"category='{article.category}' | url='{article.url}'"
        )

        # 1. Input Validation
        if not article.content or not isinstance(article.content, str) or not article.content.strip():
            logger.warning(
                f"[CLEANING_SERVICE] Empty or missing content | url='{article.url}' | "
                f"title='{article.title[:50]}'"
            )
            return CleanedArticle.from_failure(
                article,
                error_message="Article content is empty or contains no readable text.",
            )

        if article.category not in VALID_CATEGORIES:
            return CleanedArticle.from_failure(
                article,
                error_message=f"Invalid category '{article.category}'. Must be one of: {', '.join(VALID_CATEGORIES)}",
            )

        try:
            current_text = article.content

            # 2. HTML/Text Cleanup
            if self.config.enable_html_cleaning:
                current_text = self.html_cleaner.clean(current_text)

            # 3. Boilerplate Removal
            if self.config.enable_boilerplate_cleaning:
                current_text = self.boilerplate_cleaner.remove_boilerplate(current_text)

            # 4. Unicode Normalization
            if self.config.enable_unicode_normalization:
                current_text = self.unicode_normalizer.normalize(current_text)

            # 5. Whitespace Normalization
            if self.config.enable_whitespace_normalization:
                current_text = self.whitespace_normalizer.normalize(current_text)

            # 6. Paragraph Cleanup & Conservative Repeated-Paragraph Removal
            if self.config.enable_paragraph_cleanup:
                current_text = self.paragraph_cleaner.clean_paragraphs(current_text)

            # Final whitespace normalization pass
            if self.config.enable_whitespace_normalization:
                current_text = self.whitespace_normalizer.normalize(current_text)

            # 7. Output Validation
            if not current_text or not current_text.strip():
                logger.warning(
                    f"[CLEANING_SERVICE] Content reduced to empty after cleaning | url='{article.url}'"
                )
                return CleanedArticle.from_failure(
                    article,
                    error_message="Content was completely reduced to empty after cleaning and boilerplate removal.",
                )

            stripped_text = current_text.strip()
            if len(stripped_text) < self.config.min_cleaned_content_length:
                logger.warning(
                    f"[CLEANING_SERVICE] Content below minimum character threshold ({len(stripped_text)} < "
                    f"{self.config.min_cleaned_content_length}) | url='{article.url}'"
                )
                return CleanedArticle.from_failure(
                    article,
                    error_message=(
                        f"Cleaned content length ({len(stripped_text)} chars) is below "
                        f"minimum threshold ({self.config.min_cleaned_content_length} chars)."
                    ),
                )

            words_count = len(stripped_text.split())
            if words_count < self.config.min_cleaned_words_count:
                logger.warning(
                    f"[CLEANING_SERVICE] Content below minimum word count ({words_count} < "
                    f"{self.config.min_cleaned_words_count}) | url='{article.url}'"
                )
                return CleanedArticle.from_failure(
                    article,
                    error_message=(
                        f"Cleaned content word count ({words_count} words) is below "
                        f"minimum threshold ({self.config.min_cleaned_words_count} words)."
                    ),
                )

            # 8. Success: Produce CleanedArticle
            duration_ms = (time.perf_counter() - start_time) * 1000
            orig_len = len(article.content or "")
            cleaned_len = len(stripped_text)
            logger.info(
                f"[CLEANING_SERVICE] Cleaning completed successfully | url='{article.url}' | "
                f"orig_len={orig_len} | cleaned_len={cleaned_len} | duration={duration_ms:.2f}ms"
            )

            return CleanedArticle.from_extracted_article(article, stripped_text)

        except CleaningException as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[CLEANING_SERVICE] Cleaning exception | url='{article.url}' | error='{exc.message}'"
            )
            return CleanedArticle.from_failure(article, error_message=exc.message)

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"[CLEANING_SERVICE] Unexpected error during cleaning | url='{article.url}'"
            )
            return CleanedArticle.from_failure(
                article,
                error_message=f"Unexpected cleaning failure: {str(exc)}",
            )

    def clean_batch(self, articles: List[ExtractedArticle]) -> List[CleanedArticle]:
        """Process a batch of ExtractedArticle objects with per-article failure isolation."""
        logger.info(f"[CLEANING_SERVICE] Starting batch cleaning for {len(articles)} articles")
        results = [self.clean_article(article) for article in articles]
        successful_count = sum(1 for r in results if r.cleaning_status == CleaningStatus.SUCCESS)
        logger.info(
            f"[CLEANING_SERVICE] Completed batch cleaning | total={len(results)} | "
            f"successful={successful_count} | failed={len(results) - successful_count}"
        )
        return results
