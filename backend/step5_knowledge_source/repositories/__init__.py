"""Step 5 repositories package linking to canonical database repositories."""
from backend.database.repositories.category_repository import CategoryRepository
from backend.database.repositories.news_article_repository import NewsArticleRepository

__all__ = ["CategoryRepository", "NewsArticleRepository"]
