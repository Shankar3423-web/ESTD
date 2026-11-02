"""Live RSS verification script testing all 5 ESTD categories against real feeds."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.constants.categories import VALID_CATEGORIES
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService


async def verify_live_rss():
    print("=" * 70)
    print("ESTD Step 1 Source Collection — Live RSS Verification (All 5 Categories)")
    print("=" * 70)

    service = RSSCollectionService(timeout_seconds=10.0)
    results = {}

    for cat in VALID_CATEGORIES:
        print(f"\nFetching RSS for Category: '{cat}'...")
        try:
            resp = await service.collect_by_category(category=cat, limit=2)
            results[cat] = {
                "status": "PASS",
                "count": resp.count,
                "first_title": resp.items[0].title if resp.items else "None",
                "first_url": resp.items[0].url if resp.items else "None",
                "source_name": resp.items[0].source_name if resp.items else "None",
                "source_type": resp.items[0].source_type if resp.items else "None",
                "published_at": resp.items[0].published_at if resp.items else "None",
                "collected_at": resp.items[0].collected_at if resp.items else "None",
            }
            print(f"  [PASS] {resp.count} items collected")
            if resp.items:
                item = resp.items[0]
                print(f"         Title: '{item.title[:60]}...'")
                print(f"         Source: '{item.source_name}' | Type: '{item.source_type}' | Category: '{item.category}'")
                print(f"         URL: {item.url}")
                print(f"         Published: {item.published_at} | Collected: {item.collected_at}")
        except Exception as err:
            results[cat] = {"status": "FAIL", "error": str(err)}
            print(f"  [FAIL] Error: {err}")

    print("\n" + "=" * 70)
    print("SUMMARY CHECKLIST:")
    for cat, data in results.items():
        print(f"  {cat:25} -> {data['status']} ({data.get('count', 0)} items)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_live_rss())
