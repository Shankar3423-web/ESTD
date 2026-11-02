"""ESTD — Extract and Persist 10 Articles across 5 Categories.

Runs the complete continuous pipeline:
Step 1 (Source Collection: RSS & APIs)
  ↓
Step 2 (Article Extraction)
  ↓
Step 3 (Content Cleaning)
  ↓
Step 4 (Duplicate Detection & Cosine Similarity)
  ↓
Step 5 (PostgreSQL Persistence in `news_articles`)

Ingests exactly 2 unique, valid articles for each of the 5 categories (Total: 10 articles).
Then queries and outputs the database records directly from PostgreSQL.
"""
import asyncio
import sys
from pathlib import Path

# Ensure paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, text
from backend.common.constants.categories import VALID_CATEGORIES
from backend.step1_source_collection.services.source_collection_service import SourceCollectionService
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle, CleaningStatus
from backend.step4_duplicate_detection.services.duplicate_detection_service import DuplicateDetectionService
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService
from backend.step5_knowledge_source.exceptions import ArticleDuplicateError
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle


TARGET_PER_CATEGORY = 2


async def process_and_persist_article(
    item: NewsItem,
    extraction_service: ExtractionService,
    cleaning_service: ContentCleaningService,
    knowledge_service: KnowledgeSourceService,
) -> tuple[bool, str, any]:
    """Execute Step 2 -> Step 3 -> Step 4 -> Step 5 for a single candidate NewsItem."""
    # Step 2: Extraction (Force full webpage scrape to avoid snippet-only storage)
    try:
        extracted = await extraction_service.extract_article(item, force_fetch=True)
    except Exception as exc:
        return False, f"Step 2 Extraction failed: {exc}", None

    if extracted.extraction_status == "EXTRACTION_FAILED" or not extracted.content or len(extracted.content.strip()) < 500:
        return False, f"Step 2 content insufficient ({len(extracted.content or '')} chars < 500 min)", None

    # Step 3: Cleaning
    cleaned = cleaning_service.clean_article(extracted)
    if cleaned.cleaning_status != CleaningStatus.SUCCESS or not cleaned.cleaned_content or len(cleaned.cleaned_content.strip()) < 500:
        return False, f"Step 3 Cleaning insufficient ({len(cleaned.cleaned_content or '')} chars)", None

    # Step 4: Duplicate Detection
    try:
        with get_db_session() as session:
            dedup_service = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=True,
                    persist_unique_articles=True,
                )
            )
            dedup_result = dedup_service.check_article(cleaned, session=session)
            session.commit()
    except Exception as exc:
        return False, f"Step 4 Deduplication failed: {exc}", None

    if dedup_result.status != "unique":
        return False, f"Step 4 Flagged as duplicate ({dedup_result.decision.duplicate_reason}, scope={dedup_result.decision.detection_scope})", None

    # Step 5: PostgreSQL Persistence
    try:
        persisted = knowledge_service.persist_from_step4(dedup_result)
        return True, "SUCCESS", persisted
    except ArticleDuplicateError as dup_err:
        return False, f"Step 5 Duplicate prevented by DB: {dup_err}", None
    except Exception as exc:
        return False, f"Step 5 Persistence failed: {exc}", None


async def main():
    print("=" * 80)
    print("ESTD — 10 ARTICLE EXTRACTION & PERSISTENCE PIPELINE (STEPS 1 TO 5)")
    print("=" * 80)
    print(f"Categories: {VALID_CATEGORIES}")
    print(f"Goal: Extract and persist {TARGET_PER_CATEGORY} articles per category into PostgreSQL (Total: 10)\n")

    # Initialize services
    source_service = SourceCollectionService()
    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    knowledge_service = KnowledgeSourceService()

    persisted_by_category = {cat: [] for cat in VALID_CATEGORIES}

    for category in VALID_CATEGORIES:
        print("-" * 80)
        print(f"--> Ingesting Category: [{category}] (Target: {TARGET_PER_CATEGORY} articles)")
        print("-" * 80)

        # We want exactly 1 from API and 1 from RSS per category to showcase all 3 providers (GNews, NewsData, RSS)
        api_candidates: list[NewsItem] = []
        rss_candidates: list[NewsItem] = []

        # 1. Fetch from API (GNews for AI, Tech, Education; NewsData for Business, Science)
        try:
            if category in ["Artificial Intelligence", "Technology", "Education"]:
                api_resp = await source_service.collect_from_gnews(category=category, limit=5)
                print(f"  [Step 1 - GNews API] Fetched {len(api_resp.items)} items")
                api_candidates.extend(api_resp.items)
            else:
                api_resp = await source_service.collect_from_newsdata(category=category, limit=5)
                print(f"  [Step 1 - NewsData API] Fetched {len(api_resp.items)} items")
                api_candidates.extend(api_resp.items)
        except Exception as exc:
            print(f"  [Step 1 - API] Warning: {exc}")

        # 2. Fetch from RSS
        try:
            rss_resp = await source_service.collect_from_rss(category=category, limit=10)
            print(f"  [Step 1 - RSS Feed] Fetched {len(rss_resp.items)} items")
            rss_candidates.extend(rss_resp.items)
        except Exception as exc:
            print(f"  [Step 1 - RSS] Warning: {exc}")

        # Ingest 1 from API
        print(f"\n  [Ingesting API Article for {category}]")
        for item in api_candidates:
            title_clean = item.title.encode('ascii', errors='replace').decode('ascii')
            source_clean = (item.source_name or "Unknown").encode('ascii', errors='replace').decode('ascii')
            print(f"    Evaluating API item: '{title_clean[:60]}...' ({item.source_type} / {source_clean})")
            success, msg, persisted = await process_and_persist_article(
                item, extraction_service, cleaning_service, knowledge_service
            )
            if success and persisted:
                persisted_by_category[category].append(persisted)
                word_count = len(persisted.content.split())
                print(f"    --> [PERSISTED API ARTICLE] ID: {persisted.id} | Words: {word_count} | Source: {persisted.source_type} | Category: {persisted.category}")
                break
            else:
                print(f"    [SKIPPED] {msg}")

        # Ingest 1 from RSS
        print(f"\n  [Ingesting RSS Article for {category}]")
        for item in rss_candidates:
            title_clean = item.title.encode('ascii', errors='replace').decode('ascii')
            source_clean = (item.source_name or "Unknown").encode('ascii', errors='replace').decode('ascii')
            print(f"    Evaluating RSS item: '{title_clean[:60]}...' (rss / {source_clean})")
            success, msg, persisted = await process_and_persist_article(
                item, extraction_service, cleaning_service, knowledge_service
            )
            if success and persisted:
                persisted_by_category[category].append(persisted)
                word_count = len(persisted.content.split())
                print(f"    --> [PERSISTED RSS ARTICLE] ID: {persisted.id} | Words: {word_count} | Source: {persisted.source_type} | Category: {persisted.category}")
                break
            else:
                print(f"    [SKIPPED] {msg}")

        print(f"\n  Finished Category [{category}]: {len(persisted_by_category[category])}/2 persisted.")

    # ----------------------------------------------------
    # QUERY DATABASE DIRECTLY AND DISPLAY STORED ARTICLES
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("QUERYING POSTGRESQL DATABASE DIRECTLY: `news_articles` TABLE")
    print("=" * 80)

    with get_db_session() as session:
        all_articles = session.scalars(
            select(NewsArticle).order_by(NewsArticle.category, NewsArticle.id)
        ).all()

        print(f"\nTotal Articles currently stored in PostgreSQL: {len(all_articles)}\n")

        print(f"{'ID':<6} | {'Category':<24} | {'Source':<10} | {'Publisher':<22} | {'Words':<6} | {'Title'}")
        print("-" * 110)
        for art in all_articles:
            words = len(art.content.split()) if art.content else 0
            pub = (art.source_name or "Unknown")[:20]
            title_clean = art.title.encode('ascii', errors='replace').decode('ascii')
            title_disp = title_clean[:45] + ("..." if len(title_clean) > 45 else "")
            print(f"{art.id:<6} | {art.category:<24} | {art.source_type:<10} | {pub:<22} | {words:<6} | {title_disp}")

        print("\n" + "=" * 80)
        print("DETAILED RECORD AUDIT (FIRST 10 ARTICLES)")
        print("=" * 80)

        for i, art in enumerate(all_articles[:10], start=1):
            words = len(art.content.split()) if art.content else 0
            chars = len(art.content) if art.content else 0
            safe_content = art.content.encode('ascii', errors='replace').decode('ascii') if art.content else "EMPTY"
            cleaned_preview = safe_content[:220].replace("\n", " ")
            safe_title = art.title.encode('ascii', errors='replace').decode('ascii')

            print(f"\n--- [ARTICLE {i}/10] ---")
            print(f"  Database ID      : {art.id}")
            print(f"  Category         : {art.category} (Category ID FK: {art.category_id})")
            print(f"  Title            : {safe_title}")
            print(f"  Source Type      : {art.source_type}")
            print(f"  Publisher Name   : {art.source_name}")
            print(f"  Author           : {art.author or 'Not specified'}")
            print(f"  Published At UTC : {art.published_at}")
            print(f"  Collected At UTC : {art.collected_at}")
            print(f"  Created At UTC   : {art.created_at}")
            print(f"  Original URL     : {art.url}")
            print(f"  Normalized URL   : {art.normalized_url}")
            print(f"  SHA-256 Hash     : {art.content_hash}")
            print(f"  Content Metrics  : {chars} characters | {words} words")
            print(f"  Clean Content    : \"{cleaned_preview}...\"")

        # Category breakdown
        cat_counts = session.execute(
            text("SELECT category, count(*) FROM news_articles GROUP BY category ORDER BY category")
        ).all()
        print("\n" + "=" * 80)
        print("DATABASE SUMMARY BY CATEGORY:")
        for cat, cnt in cat_counts:
            print(f"  - {cat:<25}: {cnt} article(s)")

        # Source breakdown
        src_counts = session.execute(
            text("SELECT source_type, count(*) FROM news_articles GROUP BY source_type ORDER BY source_type")
        ).all()
        print("\nDATABASE SUMMARY BY SOURCE TYPE:")
        for src, cnt in src_counts:
            print(f"  - {src:<15}: {cnt} article(s)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
