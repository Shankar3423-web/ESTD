import asyncio
import sys
from pathlib import Path

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

FEEDS = [
    ("The Hindu Business", "https://www.thehindu.com/business/feeder/default.rss", "Economy & Macroeconomics"),
    ("Indian Express Business", "https://indianexpress.com/section/business/feed/", "Financial Markets & Banking"),
    ("The Guardian Business", "https://www.theguardian.com/business/rss", "Economy & Macroeconomics"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml", "Financial Markets & Banking"),
]

async def check():
    ext = ExtractionService()
    headers = {"User-Agent": "Mozilla/5.0 ESTD-News/1.0"}
    for name, f_url, subcat in FEEDS:
        try:
            req = urllib.request.Request(f_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                d = feedparser.parse(r.read())
            if not d.entries:
                print(f"{name:<25} | NO ENTRIES")
                continue
            entry = d.entries[0]
            item = NewsItem(title=entry.title, url=entry.link, category="Business & Finance", subcategory=subcat, source_name=name, source_type="rss", published_at="2026-10-15T00:00:00Z")
            res = await ext.extract_article(item, force_fetch=True)
            chars = len(res.content or "")
            title_snippet = (res.title or "")[:45]
            print(f"{name:<25} | status: {res.extraction_status.value} | chars: {chars} | title: {title_snippet}")
        except Exception as exc:
            print(f"{name:<25} | ERROR: {exc}")

if __name__ == "__main__":
    asyncio.run(check())
