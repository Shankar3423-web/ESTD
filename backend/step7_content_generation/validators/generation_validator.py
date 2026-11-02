"""Validation logic for Step 7 Gemini AI generated news articles."""
import re
from typing import Optional, Set
from urllib.parse import urlparse

from backend.common.constants.categories import ESTDCategory, VALID_CATEGORIES
from backend.step7_content_generation.exceptions import GenerationValidationError
from backend.step7_content_generation.schemas.generated_news import GeneratedNews


class GenerationValidator:
    """Validates structural correctness, journalistic standards, and source grounding of generated articles."""

    @staticmethod
    def validate_url(url: str) -> bool:
        """Verify that a URL is well-formed with valid HTTP/HTTPS scheme and netloc."""
        if not url or not isinstance(url, str):
            return False
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme in ("http", "https") and parsed.netloc)
        except Exception:
            return False

    @classmethod
    def validate_generated_news(
        cls,
        news: GeneratedNews,
        expected_category: Optional[str] = None,
        expected_url: Optional[str] = None,
        source_content: Optional[str] = None,
    ) -> None:
        """Perform comprehensive validation on a GeneratedNews object.

        Raises:
            GenerationValidationError: If any validation rule is violated.
        """
        if not isinstance(news, GeneratedNews):
            raise GenerationValidationError("Generated content is not a valid GeneratedNews instance.")

        # 1. Title validation
        if not news.title or not news.title.strip():
            raise GenerationValidationError("Generated title is missing or empty.")
        if len(news.title.strip()) < 5:
            raise GenerationValidationError("Generated title is too short (< 5 characters).")

        # 2. Summary validation
        if not news.summary or not news.summary.strip():
            raise GenerationValidationError("Generated summary is missing or empty.")
        if len(news.summary.strip()) < 20:
            raise GenerationValidationError("Generated summary is too short (< 20 characters).")

        # 3. Content validation
        if not news.content or not news.content.strip():
            raise GenerationValidationError("Generated content body is missing or empty.")
        clean_body = news.content.strip()
        if len(clean_body) < 100:
            raise GenerationValidationError("Generated content body is too short (< 100 characters).")

        # 3b. Quality check: Content must not be a mere copy of the executive summary
        clean_summary = news.summary.strip()
        if clean_body.lower() == clean_summary.lower():
            raise GenerationValidationError("Generated article body is identical to executive summary.")

        # 3c. Quality check: Detect trivial paragraph repetition padding
        paragraphs = [p.strip() for p in clean_body.split("\n\n") if len(p.strip()) > 30]
        if len(paragraphs) >= 3 and len(set(paragraphs)) == 1:
            raise GenerationValidationError("Generated article body contains repeated duplicate paragraphs.")

        # 4. Category validation
        cat_value = news.category.value if isinstance(news.category, ESTDCategory) else str(news.category)
        if cat_value not in VALID_CATEGORIES:
            raise GenerationValidationError(
                f"Generated category '{cat_value}' is invalid. Must be one of: {list(VALID_CATEGORIES)}."
            )
        if expected_category and cat_value != expected_category:
            raise GenerationValidationError(
                f"Category mismatch: expected '{expected_category}', but generated '{cat_value}'."
            )

        # 5. Source Attribution validation
        if not news.source_name or not news.source_name.strip():
            raise GenerationValidationError("Generated source_name is missing or empty.")

        # 6. Source URL validation
        if not news.source_url or not news.source_url.strip():
            raise GenerationValidationError("Generated source_url is missing or empty.")
        if not cls.validate_url(news.source_url):
            raise GenerationValidationError(f"Generated source_url is invalid: '{news.source_url}'.")
        if expected_url and news.source_url.strip() != expected_url.strip():
            raise GenerationValidationError(
                f"Source URL mismatch: expected '{expected_url}', but generated '{news.source_url}'."
            )

        # 7. Grounding verification (anti-hallucination check)
        if source_content and len(source_content.strip()) >= 50:
            cls.verify_grounding(news, source_content)

    @classmethod
    def verify_grounding(
        cls,
        news: GeneratedNews,
        source_content: str,
        min_overlap_ratio: float = 0.05,
    ) -> None:
        """Verify that generated news is grounded in the source text via lexical overlap."""
        def extract_words(text: str) -> Set[str]:
            tokens = re.findall(r"\b[A-Za-z0-9]{3,}\b", text.lower())
            stop_words = {
                "the", "and", "for", "that", "this", "with", "from", "have", "were",
                "been", "their", "which", "will", "about", "more", "into", "also",
                "after", "than", "they", "them", "some", "what", "when", "where",
            }
            return {t for t in tokens if t not in stop_words}

        source_words = extract_words(source_content)
        if not source_words:
            return

        gen_words = extract_words(f"{news.title} {news.summary} {news.content}")
        overlap = source_words.intersection(gen_words)
        ratio = len(overlap) / len(source_words)

        if len(overlap) == 0:
            raise GenerationValidationError(
                "Source grounding failure: Generated content shares zero significant terms with source material."
            )
