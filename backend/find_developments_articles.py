import asyncio
import sys
from pathlib import Path
import feedparser
import httpx

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService

FEEDS_TO_CHECK = [
    # 1. Government & Public Policy - National
    ("Government & Public Policy", "DEV_GOV_POLICY", 25, "national", "en", "The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss"),
    # 1b. Government & Public Policy - Regional Telugu
    ("Government & Public Policy", "DEV_GOV_POLICY", 25, "regional", "te", "Oneindia Telugu", "https://telugu.oneindia.com/rss/telugu-news-fb.xml"),
    # 2. Infrastructure & Urban Planning - Regional (Telangana / Hyderabad)
    ("Infrastructure & Urban Planning", "DEV_INFRA", 26, "regional", "en", "Telangana Today", "https://telanganatoday.com/hyderabad/feed"),
    # 2b. Infrastructure & Urban Planning - National
    ("Infrastructure & Urban Planning", "DEV_INFRA", 26, "national", "en", "The Hindu", "https://www.thehindu.com/news/cities/Hyderabad/feeder/default.rss"),
    # 3. Energy, Climate & Environment - National / Global
    ("Energy, Climate & Environment", "DEV_ENERGY_CLIMATE", 27, "national", "en", "The Hindu", "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss"),
    # 4. Health & Medical Sciences - International
    ("Health & Medical Sciences", "DEV_HEALTH_MED", 28, "international", "en", "World Health Organization", "https://www.who.int/rss-feeds/news-english.xml"),
    # 4b. Health & Medical Sciences - National
    ("Health & Medical Sciences", "DEV_HEALTH_MED", 28, "national", "en", "The Hindu", "https://www.thehindu.com/sci-tech/health/feeder/default.rss"),
    # 5. Education & Learning Policy - National
    ("Education & Learning Policy", "DEV_EDUCATION", 29, "national", "en", "The Indian Express", "https://indianexpress.com/section/education/feed/"),
    # 6. Science & Research Discoveries - International
    ("Science & Research Discoveries", "DEV_SCIENCE_RESEARCH", 30, "international", "en", "Phys.org", "https://phys.org/rss-feed/"),
    # 7. Global Affairs & Geopolitics - International
    ("Global Affairs & Geopolitics", "DEV_GLOBAL_AFFAIRS", 31, "international", "en", "UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
]

async def check_articles():
    extraction_service = ExtractionService()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ESTD/1.0"}
    
    selected_articles = []
    
    for subcat, code, sub_id, scope, lang, source_name, feed_url in FEEDS_TO_CHECK:
        print(f"\nScanning feed for [{subcat}] ({scope}) from {source_name}...")
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(feed_url)
                parsed = feedparser.parse(resp.content)
                entries = parsed.entries[:5]
                
                tested_and_found = False
                for entry in entries:
                    title = entry.title
                    link = entry.link
                    pub = getattr(entry, "published", "")
                    
                    item = NewsItem(
                        title=title,
                        url=link,
                        source_name=source_name,
                        source_type="rss",
                        category="Developments",
                        subcategory=subcat,
                        published_at=pub,
                        language=lang,
                        region="IN" if scope in ("national", "regional") else "US",
                    )
                    
                    try:
                        ext = await extraction_service.extract_article(item, force_fetch=True)
                        content_len = len(ext.content or "")
                        if content_len >= 300:
                            print(f"  [SUCCESS] '{title[:50]}...' -> {content_len} chars (Link: {link})")
                            selected_articles.append({
                                "subcategory_name": subcat,
                                "subcategory_code": code,
                                "expected_sub_id": sub_id,
                                "scope": scope,
                                "language": lang,
                                "title": title,
                                "url": link,
                                "source_name": source_name,
                                "source_type": "rss",
                                "published_at": pub,
                                "content_len": content_len,
                            })
                            tested_and_found = True
                            break
                        else:
                            print(f"  [SHORT] '{title[:40]}' ({content_len} chars)")
                    except Exception as e:
                        print(f"  [EXTRACT ERROR] '{title[:40]}': {e}")
                
                if not tested_and_found:
                    print(f"  [WARNING] No article with >=300 chars found in top 5 entries for {subcat}")
        except Exception as e:
            print(f"  [FEED ERROR] {e}")

    print("\n" + "=" * 80)
    print(f"SELECTED ARTICLES ({len(selected_articles)}/{len(FEEDS_TO_CHECK)}):")
    print("=" * 80)
    import json
    with open("selected_dev_articles.json", "w", encoding="utf-8") as f:
        json.dump(selected_articles, f, indent=2, ensure_ascii=False)
    print("Saved to selected_dev_articles.json")

if __name__ == "__main__":
    asyncio.run(check_articles())
