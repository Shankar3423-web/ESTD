import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8")

import feedparser
import urllib.request
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService

TEST_FEEDS = [
    ("Economy & Macroeconomics", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Financial Markets & Banking", "https://www.business-standard.com/rss/markets-106.rss"),
    ("Startups & Venture Capital", "https://inc42.com/feed/"),
    ("Corporate Strategy & Earnings", "https://economictimes.indiatimes.com/news/company/corporate-trends/rssfeeds/2143429.cms"),
    ("Personal Finance & Wealth Management", "https://www.livemint.com/rss/money"),
    ("Trade, Supply Chain & Industry", "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms"),
    ("Telugu Regional Markets", "https://www.sakshi.com/rss/business.xml"),
]

async def run_extraction():
    print("=" * 80)
    print("TESTING FULL-TEXT SCRAPING & EXTRACTION FOR BUSINESS & FINANCE")
    print("=" * 80)

    extractor = ExtractionService()
    cleaner = ContentCleaningService()
    headers = {"User-Agent": "Mozilla/5.0 ESTD-News/1.0"}

    for subcat, feed_url in TEST_FEEDS:
        print(f"\nSubcategory: {subcat}")
        print(f"Feed: {feed_url}")
        try:
            req = urllib.request.Request(feed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = feedparser.parse(resp.read())
            if not data.entries:
                print(" [SKIP] No entries in feed")
                continue
            
            entry = data.entries[0]
            url = entry.link
            print(f" Article Title: {entry.title}")
            print(f" Article URL:   {url}")

            news_item = NewsItem(
                id=f"test_{subcat[:4]}",
                title=entry.title,
                url=url,
                category="Business & Finance",
                subcategory=subcat,
                source_name=data.feed.get("title", "Test Publisher"),
                source_type="rss",
                published_at=datetime.now(timezone.utc).isoformat(),
                description=entry.get("summary", ""),
            )

            ext_result = await extractor.extract_article(news_item, force_fetch=True)
            print(f" Extraction Status: {ext_result.extraction_status}")
            print(f" Extracted Title:  {ext_result.title}")
            content_len = len(ext_result.content or "")
            word_count = len((ext_result.content or "").split())
            print(f" Extracted Length: {content_len} chars, {word_count} words")

            # Test cleaning
            if ext_result.content:
                clean_res = cleaner.clean_article(ext_result)
                print(f" Cleaned Status:   {clean_res.cleaning_status}")
                print(f" Cleaned Length:   {len(clean_res.content)} chars")
                has_currency = any(s in clean_res.content for s in ["$", "₹", "Rs", "percent", "%", "crore", "billion", "million", "రూ."])
                print(f" Financial terms preserved: {has_currency}")
        except Exception as exc:
            print(f" [ERROR] Extraction failed: {exc}")

if __name__ == "__main__":
    asyncio.run(run_extraction())
