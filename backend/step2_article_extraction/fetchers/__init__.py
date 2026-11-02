"""Step 2 fetchers package."""
from backend.step2_article_extraction.fetchers.article_fetcher import ArticleFetcher
from backend.step2_article_extraction.fetchers.url_validator import URLValidator

__all__ = [
    "ArticleFetcher",
    "URLValidator",
]
