"""ESTD News Provider Definitions."""
from enum import Enum


class NewsProvider(str, Enum):
    """Supported news providers for Step 1."""
    GNEWS = "gnews"
    NEWSDATA = "newsdata"
    RSS = "rss"
