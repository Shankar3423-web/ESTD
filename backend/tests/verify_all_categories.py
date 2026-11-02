"""Live verification script for all 5 categories on GNews and NewsData.io."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.config.settings import get_settings
from backend.common.constants.categories import VALID_CATEGORIES
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter


async def verify_all():
    settings = get_settings()
    gnews = GNewsAdapter(settings=settings)
    newsdata = NewsDataAdapter(settings=settings)

    print("\n--- Testing GNews for all 5 categories ---")
    for cat in VALID_CATEGORIES:
        try:
            items = await gnews.fetch_news(cat, limit=1)
            title = items[0].title[:45] if items else "No items returned"
            print(f"  [GNews] {cat:25}: SUCCESS ({len(items)} item) -> '{title}...'")
        except Exception as e:
            print(f"  [GNews] {cat:25}: FAILED -> {e}")

    print("\n--- Testing NewsData.io for all 5 categories ---")
    for cat in VALID_CATEGORIES:
        try:
            items = await newsdata.fetch_news(cat, limit=1)
            title = items[0].title[:45] if items else "No items returned"
            print(f"  [NewsData] {cat:25}: SUCCESS ({len(items)} item) -> '{title}...'")
        except Exception as e:
            print(f"  [NewsData] {cat:25}: FAILED -> {e}")


if __name__ == "__main__":
    asyncio.run(verify_all())
