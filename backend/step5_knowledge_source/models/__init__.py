"""Step 5 models package linking to canonical database models."""
from backend.database.models.category import Category
from backend.database.models.news_article import NewsArticle

__all__ = ["Category", "NewsArticle"]
