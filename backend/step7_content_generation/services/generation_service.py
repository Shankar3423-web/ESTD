"""Core service for transforming knowledge-source articles into validated ESTD news."""
import time
from typing import Optional

from backend.common.constants.categories import ESTDCategory
from backend.common.logging.logger import logger
from backend.step7_content_generation.client.gemini_client import GeminiClient
from backend.step7_content_generation.config.gemini_settings import (
    GeminiSettings,
    get_gemini_settings,
)
from backend.step7_content_generation.prompts.news_generation_prompt import (
    build_news_generation_prompt,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.validators.generation_validator import (
    GenerationValidator,
)


class GenerationService:
    """Service handling prompt construction, Gemini invocation, and output validation."""

    def __init__(
        self,
        settings: Optional[GeminiSettings] = None,
        client: Optional[GeminiClient] = None,
        validator: Optional[GenerationValidator] = None,
    ):
        self.settings = settings or get_gemini_settings()
        self.client = client or GeminiClient(self.settings)
        self.validator = validator or GenerationValidator()

    def generate_news(
        self,
        title: str,
        content: str,
        category: str,
        source_name: Optional[str] = None,
        source_url: str = "",
        author: Optional[str] = None,
        published_at: Optional[str] = None,
        description: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> GeneratedNews:
        """Transform raw source article content into validated GeneratedNews.

        Args:
            title: Headline of source article.
            content: Body text of source article.
            category: Canonical ESTD category.
            source_name: Name of publisher.
            source_url: Canonical original article URL.
            author: Author name if known.
            published_at: Publication timestamp string if known.
            description: Original summary if available.
            custom_instructions: Optional editorial focus directions.
            subcategory: Canonical ESTD subcategory if available.

        Returns:
            Fully validated GeneratedNews instance.

        Raises:
            GenerationValidationError: If generated content fails structural or grounding checks.
            GenerationException: On API or network failure.
        """
        logger.info(
            f"Building generation prompt | category='{category}' | subcategory='{subcategory}' | title='{title[:40]}...' | source='{source_name}'"
        )
        prompt = build_news_generation_prompt(
            title=title,
            content=content,
            category=category,
            source_name=source_name,
            source_url=source_url,
            author=author,
            published_at=published_at,
            description=description,
            custom_instructions=custom_instructions,
            subcategory=subcategory,
        )

        start_time = time.monotonic()
        generated: GeneratedNews = self.client.generate_structured(
            prompt=prompt,
            response_schema=GeneratedNews,
        )
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info(f"AI content generated in {elapsed_ms:.1f}ms. Validating output...")

        if not getattr(generated, "subcategory", None) and subcategory:
            generated.subcategory = subcategory

        # Authoritatively enforce runtime UTC timestamp (prevent LLM from hallucinating training-cutoff dates)
        from datetime import datetime, timezone
        generated.generated_at = datetime.now(timezone.utc)

        # Strict validation
        self.validator.validate_generated_news(
            news=generated,
            expected_category=category,
            expected_url=source_url,
            source_content=content,
        )

        logger.info(
            f"Generated content validation passed | title='{generated.title[:40]}...' | category='{generated.category}' | subcategory='{generated.subcategory}'"
        )
        return generated
