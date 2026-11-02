"""ExtractionService orchestrating content sufficiency evaluation, fetching, and extraction."""
import asyncio
import time
from typing import List, Optional

from backend.common.logging.logger import logger
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.config import ExtractionConfig, extraction_config
from backend.step2_article_extraction.exceptions.extraction_exceptions import (
    ExtractionException,
)
from backend.step2_article_extraction.extractors.article_extractor import ArticleExtractor
from backend.step2_article_extraction.extractors.sufficiency_checker import SufficiencyChecker
from backend.step2_article_extraction.fetchers.article_fetcher import ArticleFetcher
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle


class ExtractionService:
    """Core service for Step 2 Article Extraction pipeline."""

    def __init__(
        self,
        config: Optional[ExtractionConfig] = None,
        fetcher: Optional[ArticleFetcher] = None,
        extractor: Optional[ArticleExtractor] = None,
        sufficiency_checker: Optional[SufficiencyChecker] = None,
    ):
        self.config = config or extraction_config
        self.fetcher = fetcher or ArticleFetcher(config=self.config)
        self.extractor = extractor or ArticleExtractor()
        self.sufficiency_checker = sufficiency_checker or SufficiencyChecker(config=self.config)

    async def extract_article(
        self,
        news_item: NewsItem,
        force_fetch: bool = False,
    ) -> ExtractedArticle:
        """Process a single NewsItem through Step 2 extraction.

        1. Evaluates if incoming item already has sufficient content (no-scrape path).
        2. If force_fetch=True or content insufficient, fetches webpage HTML via HTTP GET.
        3. Extracts metadata and article body text from HTML.
        4. Handles and isolates failures gracefully without raising unhandled exceptions.

        Args:
            news_item: Step 1 normalized news item.
            force_fetch: If True, forces webpage fetch even if description is present.

        Returns:
            ExtractedArticle containing preserved Step 1 fields and Step 2 extraction results.
        """
        start_time = time.perf_counter()
        logger.info(
            f"[EXTRACTION_SERVICE] Processing article | title='{news_item.title[:50]}' | "
            f"category='{news_item.category}' | provider='{news_item.source_type}' | url='{news_item.url}'"
        )

        # 1. Content Sufficiency Check
        is_sufficient, existing_content = self.sufficiency_checker.evaluate(news_item)
        should_fetch = force_fetch or self.config.prefer_scrape_for_news_feeds or not is_sufficient

        if not should_fetch and is_sufficient and existing_content:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[EXTRACTION_SERVICE] Existing content sufficient (no fetch required) | "
                f"url='{news_item.url}' | duration={duration_ms:.2f}ms"
            )
            return ExtractedArticle.from_existing_content(news_item, existing_content)

        # 2. Scrape Required Path: Fetch HTML + Extract
        logger.info(f"[EXTRACTION_SERVICE] Fetching full webpage article | url='{news_item.url}'")

        try:
            html = await self.fetcher.fetch_html(news_item.url)
            extracted_data = self.extractor.extract(html, url=news_item.url)

            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[EXTRACTION_SERVICE] Article successfully extracted | url='{news_item.url}' | "
                f"content_length={len(extracted_data['content'])} | duration={duration_ms:.2f}ms"
            )

            return ExtractedArticle.from_extracted(
                news_item=news_item,
                content=extracted_data["content"],
                title=extracted_data.get("title"),
                canonical_url=extracted_data.get("canonical_url"),
                author=extracted_data.get("author"),
                published_at=extracted_data.get("published_at"),
                image_url=extracted_data.get("image_url"),
                source_name=extracted_data.get("source_name"),
            )

        except ExtractionException as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[EXTRACTION_SERVICE] Extraction failed | url='{news_item.url}' | "
                f"error='{exc.message}' | duration={duration_ms:.2f}ms"
            )
            return ExtractedArticle.from_failure(news_item, error_message=exc.message)

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"[EXTRACTION_SERVICE] Unexpected error during extraction | url='{news_item.url}' | "
                f"duration={duration_ms:.2f}ms"
            )
            return ExtractedArticle.from_failure(
                news_item,
                error_message=f"Unexpected extraction failure: {str(exc)}",
            )

    async def extract_batch(self, news_items: List[NewsItem]) -> List[ExtractedArticle]:
        """Extract a batch of news items with per-article failure isolation.

        Ensures that failures in one article do not impact others in the batch.

        Args:
            news_items: List of Step 1 NewsItems.

        Returns:
            List of ExtractedArticle objects matching input length and order.
        """
        logger.info(f"[EXTRACTION_SERVICE] Starting batch extraction for {len(news_items)} articles")
        tasks = [self.extract_article(item) for item in news_items]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        logger.info(f"[EXTRACTION_SERVICE] Completed batch extraction for {len(results)} articles")
        return list(results)
