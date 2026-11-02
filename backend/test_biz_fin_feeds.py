import sys
import feedparser
import urllib.request
from typing import Dict, List

# Ensure utf-8 stdout
sys.stdout.reconfigure(encoding="utf-8")

CANDIDATE_FEEDS = [
    # 1. Financial Markets & Banking
    {"id": "et_markets", "name": "Economic Times - Markets", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "subcat": "Financial Markets & Banking", "scope": "national", "lang": "en"},
    {"id": "bs_markets", "name": "Business Standard - Markets", "url": "https://www.business-standard.com/rss/markets-106.rss", "subcat": "Financial Markets & Banking", "scope": "national", "lang": "en"},
    {"id": "livemint_markets", "name": "LiveMint - Markets", "url": "https://www.livemint.com/rss/markets", "subcat": "Financial Markets & Banking", "scope": "national", "lang": "en"},
    {"id": "mc_markets", "name": "Moneycontrol - Business", "url": "https://www.moneycontrol.com/rss/business.xml", "subcat": "Financial Markets & Banking", "scope": "national", "lang": "en"},

    # 2. Startups & Venture Capital
    {"id": "et_startups", "name": "Economic Times - Startups", "url": "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/11993050.cms", "subcat": "Startups & Venture Capital", "scope": "national", "lang": "en"},
    {"id": "inc42_startups", "name": "Inc42", "url": "https://inc42.com/feed/", "subcat": "Startups & Venture Capital", "scope": "national", "lang": "en"},
    {"id": "yourstory_startups", "name": "YourStory", "url": "https://yourstory.com/feed", "subcat": "Startups & Venture Capital", "scope": "national", "lang": "en"},

    # 3. Corporate Strategy & Earnings
    {"id": "et_companies", "name": "Economic Times - Companies", "url": "https://economictimes.indiatimes.com/news/company/corporate-trends/rssfeeds/2143429.cms", "subcat": "Corporate Strategy & Earnings", "scope": "national", "lang": "en"},
    {"id": "bs_companies", "name": "Business Standard - Companies", "url": "https://www.business-standard.com/rss/companies-101.rss", "subcat": "Corporate Strategy & Earnings", "scope": "national", "lang": "en"},
    {"id": "livemint_companies", "name": "LiveMint - Companies", "url": "https://www.livemint.com/rss/companies", "subcat": "Corporate Strategy & Earnings", "scope": "national", "lang": "en"},

    # 4. Personal Finance & Wealth Management
    {"id": "et_wealth", "name": "Economic Times - Wealth", "url": "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms", "subcat": "Personal Finance & Wealth Management", "scope": "national", "lang": "en"},
    {"id": "bs_pf", "name": "Business Standard - Personal Finance", "url": "https://www.business-standard.com/rss/personal-finance-103.rss", "subcat": "Personal Finance & Wealth Management", "scope": "national", "lang": "en"},
    {"id": "livemint_money", "name": "LiveMint - Money", "url": "https://www.livemint.com/rss/money", "subcat": "Personal Finance & Wealth Management", "scope": "national", "lang": "en"},

    # 5. Economy & Macroeconomics
    {"id": "bs_economy", "name": "Business Standard - Economy", "url": "https://www.business-standard.com/rss/economy-policy-102.rss", "subcat": "Economy & Macroeconomics", "scope": "national", "lang": "en"},
    {"id": "cnbc_economy", "name": "CNBC - Economy", "url": "https://search.cnbc.com/rs/search/combined hazard/economy/rss", "subcat": "Economy & Macroeconomics", "scope": "international", "lang": "en"},
    {"id": "bbc_business", "name": "BBC News - Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "subcat": "Economy & Macroeconomics", "scope": "international", "lang": "en"},

    # 6. Trade, Supply Chain & Industry
    {"id": "et_industry", "name": "Economic Times - Industry", "url": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms", "subcat": "Trade, Supply Chain & Industry", "scope": "national", "lang": "en"},
    {"id": "bs_industry", "name": "Business Standard - Industry", "url": "https://www.business-standard.com/rss/industry-105.rss", "subcat": "Trade, Supply Chain & Industry", "scope": "national", "lang": "en"},

    # 7. Regional (Telugu)
    {"id": "sakshi_business", "name": "Sakshi - Business", "url": "https://www.sakshi.com/rss/business.xml", "subcat": "Financial Markets & Banking", "scope": "regional", "lang": "te"},
    {"id": "eenadu_business", "name": "Eenadu - Business", "url": "https://www.eenadu.net/rss/business.xml", "subcat": "Financial Markets & Banking", "scope": "regional", "lang": "te"},
]

def test_feeds():
    print("=" * 80)
    print("TESTING CANDIDATE BUSINESS & FINANCE RSS FEEDS (WITH UTF-8)")
    print("=" * 80)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ESTD-News/1.0"
    }

    results = []
    for f in CANDIDATE_FEEDS:
        url = f["url"]
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
                parsed = feedparser.parse(content)
                entries = parsed.entries
                status = "OK" if len(entries) > 0 else "EMPTY"
                sample_title = entries[0].title if entries else "N/A"
                sample_link = entries[0].link if entries else "N/A"
                print(f"[{status:<5}] {f['name']:<35} ({f['scope']}/{f['lang']}) -> {len(entries)} items. Sample: {sample_title[:55]}...")
                results.append({
                    "id": f["id"],
                    "name": f["name"],
                    "url": url,
                    "subcat": f["subcat"],
                    "scope": f["scope"],
                    "lang": f["lang"],
                    "status": status,
                    "count": len(entries),
                    "sample_title": sample_title,
                    "sample_link": sample_link,
                })
        except Exception as exc:
            print(f"[FAIL ] {f['name']:<35} -> Error: {exc}")
            results.append({
                "id": f["id"],
                "name": f["name"],
                "url": url,
                "subcat": f["subcat"],
                "scope": f["scope"],
                "lang": f["lang"],
                "status": f"ERROR: {exc}",
                "count": 0,
            })

    print("\n" + "=" * 80)
    print(f"SUMMARY: {sum(1 for r in results if r['status'] == 'OK')} / {len(results)} feeds operational")
    print("=" * 80)

if __name__ == "__main__":
    test_feeds()
