import sys
from pathlib import Path

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

FEEDS = [
    {
        "subcat": "Economy & Macroeconomics",
        "code": "BIZ_MACROECONOMY",
        "id": 36,
        "name": "BBC News - Business",
        "scope": "international",
        "lang": "en",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
    },
    {
        "subcat": "Economy & Macroeconomics",
        "code": "BIZ_MACROECONOMY",
        "id": 36,
        "name": "Business Standard - Economy",
        "scope": "national",
        "lang": "en",
        "url": "https://www.business-standard.com/rss/economy-policy-102.rss",
    },
    {
        "subcat": "Financial Markets & Banking",
        "code": "BIZ_MARKETS",
        "id": 32,
        "name": "Business Standard - Markets",
        "scope": "national",
        "lang": "en",
        "url": "https://www.business-standard.com/rss/markets-106.rss",
    },
    {
        "subcat": "Financial Markets & Banking",
        "code": "BIZ_MARKETS",
        "id": 32,
        "name": "Sakshi - Business",
        "scope": "regional",
        "lang": "te",
        "url": "https://www.sakshi.com/rss/business.xml",
    },
    {
        "subcat": "Startups & Venture Capital",
        "code": "BIZ_STARTUPS",
        "id": 33,
        "name": "Inc42",
        "scope": "national",
        "lang": "en",
        "url": "https://inc42.com/feed/",
    },
    {
        "subcat": "Corporate Strategy & Earnings",
        "code": "BIZ_CORP_STRATEGY",
        "id": 34,
        "name": "Economic Times - Companies",
        "scope": "national",
        "lang": "en",
        "url": "https://economictimes.indiatimes.com/news/company/corporate-trends/rssfeeds/2143429.cms",
    },
    {
        "subcat": "Personal Finance & Wealth Management",
        "code": "BIZ_PERSONAL_FINANCE",
        "id": 35,
        "name": "LiveMint - Money",
        "scope": "national",
        "lang": "en",
        "url": "https://www.livemint.com/rss/money",
    },
    {
        "subcat": "Trade, Supply Chain & Industry",
        "code": "BIZ_TRADE_INDUSTRY",
        "id": 37,
        "name": "Economic Times - Industry",
        "scope": "national",
        "lang": "en",
        "url": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
    },
]

def main():
    headers = {"User-Agent": "Mozilla/5.0 ESTD-News/1.0"}
    for f in FEEDS:
        print("=" * 80)
        print(f"Subcategory: {f['subcat']} (ID: {f['id']}) | Source: {f['name']} ({f['scope']}/{f['lang']})")
        print("=" * 80)
        try:
            req = urllib.request.Request(f["url"], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = feedparser.parse(resp.read())
            entries = data.entries[:3]
            for i, e in enumerate(entries, 1):
                print(f"[{i}] Title: {e.title}")
                print(f"    URL:   {e.link}")
                print(f"    Date:  {e.get('published', 'N/A')}")
        except Exception as exc:
            print(f"Error fetching feed: {exc}")

if __name__ == "__main__":
    main()
