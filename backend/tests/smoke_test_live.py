"""Optional live API verification script using credentials from backend/.env.

Never prints or logs API keys.
Run:
    python tests/smoke_test_live.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.config.settings import get_settings
from backend.common.exceptions.custom_exceptions import (
    ConfigurationError,
    ExternalAPIError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
)
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter


async def smoke_test():
    settings = get_settings()
    print("=" * 60)
    print("ESTD Step 1 Source Collection — Live API Smoke Test")
    print("=" * 60)

    # 1. Verify GNews
    print("\n[1/2] Testing GNews API...")
    try:
        gnews_adapter = GNewsAdapter(settings=settings)
        items = await gnews_adapter.fetch_news(category="Technology", limit=2)
        print(f"  --> SUCCESS: Received {len(items)} normalized NewsItem(s) from GNews.")
        if items:
            first = items[0]
            print(f"      Title: '{first.title[:60]}...'")
            print(f"      Source: '{first.source_name}' | Type: '{first.source_type}' | Category: '{first.category}'")
            print(f"      Published At: {first.published_at} | Collected At: {first.collected_at}")
    except ConfigurationError as ce:
        print(f"  --> SKIPPED (Configuration): {ce.message}")
    except ProviderAuthenticationError as pae:
        print(f"  --> AUTH FAILED: {pae.message} (Check if GNEWS_API_KEY is valid/active)")
    except ProviderRateLimitError as rle:
        print(f"  --> RATE LIMITED: {rle.message}")
    except ExternalAPIError as eae:
        print(f"  --> API ERROR: {eae.message}")
    except Exception as exc:
        print(f"  --> UNEXPECTED ERROR: {type(exc).__name__}: {exc}")

    # 2. Verify NewsData.io
    print("\n[2/2] Testing NewsData.io API...")
    try:
        newsdata_adapter = NewsDataAdapter(settings=settings)
        items = await newsdata_adapter.fetch_news(category="Technology", limit=2)
        print(f"  --> SUCCESS: Received {len(items)} normalized NewsItem(s) from NewsData.io.")
        if items:
            first = items[0]
            print(f"      Title: '{first.title[:60]}...'")
            print(f"      Source: '{first.source_name}' | Type: '{first.source_type}' | Category: '{first.category}'")
            print(f"      Published At: {first.published_at} | Collected At: {first.collected_at}")
    except ConfigurationError as ce:
        print(f"  --> SKIPPED (Configuration): {ce.message}")
    except ProviderAuthenticationError as pae:
        print(f"  --> AUTH FAILED: {pae.message} (Check if NEWSDATA_API_KEY is valid/active)")
    except ProviderRateLimitError as rle:
        print(f"  --> RATE LIMITED: {rle.message}")
    except ExternalAPIError as eae:
        print(f"  --> API ERROR: {eae.message}")
    except Exception as exc:
        print(f"  --> UNEXPECTED ERROR: {type(exc).__name__}: {exc}")

    print("\n" + "=" * 60)
    print("Smoke test finished.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(smoke_test())
