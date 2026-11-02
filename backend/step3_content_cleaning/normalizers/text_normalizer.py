"""Composite text normalizer combining Unicode and whitespace normalization."""
from typing import Optional

from backend.step3_content_cleaning.config import CleaningConfig, cleaning_config
from backend.step3_content_cleaning.normalizers.unicode_normalizer import UnicodeNormalizer
from backend.step3_content_cleaning.normalizers.whitespace_normalizer import WhitespaceNormalizer


class TextNormalizer:
    """High-level text normalizer executing Unicode and whitespace normalization."""

    def __init__(
        self,
        config: Optional[CleaningConfig] = None,
        unicode_normalizer: Optional[UnicodeNormalizer] = None,
        whitespace_normalizer: Optional[WhitespaceNormalizer] = None,
    ):
        self.config = config or cleaning_config
        self.unicode_normalizer = unicode_normalizer or UnicodeNormalizer()
        self.whitespace_normalizer = whitespace_normalizer or WhitespaceNormalizer(
            max_consecutive_blank_lines=self.config.max_consecutive_blank_lines
        )

    def normalize(self, text: Optional[str]) -> str:
        """Run complete text normalization pipeline.

        1. Unicode normalization (quotes, dashes, non-breaking spaces).
        2. Whitespace normalization (tabs, repeated spaces, blank lines).
        """
        if not text:
            return ""

        result = text

        if self.config.enable_unicode_normalization:
            result = self.unicode_normalizer.normalize(result)

        if self.config.enable_whitespace_normalization:
            result = self.whitespace_normalizer.normalize(result)

        return result
