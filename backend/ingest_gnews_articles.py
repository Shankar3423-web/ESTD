"""ESTD — Ingest GNews Articles into PostgreSQL through Steps 1-5."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, text
from backend.common.constants.categories import VALID_CATEGORIES
from backend.step1_source_collection.services.source_collection_service import SourceCollectionService
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step3_content_cleaning.models.cleaned_article import CleaningStatus
from backend.step4_duplicate_detection.services.duplicate_detection_service import DuplicateDetectionService
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService
from backend.step5_knowledge_source.exceptions import ArticleDuplicateError
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle


async def main():
    print("=" * 80)
    print("ESTD — GNEWS INGESTION PIPELINE (STEPS 1 TO 5)")
    print("=" * 80)

    source_service = SourceCollectionService()
    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    knowledge_service = KnowledgeSourceService()

    gnews_ingested = []

    for category in VALID_CATEGORIES:
        print(f"\n[GNews] Fetching for Category: [{category}]...")
        try:
            resp = await source_service.collect_from_gnews(category=category, limit=5)
            print(f"  Received {len(resp.items)} items from GNews API")
        except Exception as exc:
            print(f"  Error fetching from GNews for {category}: {exc}")
            continue

        for item in resp.items:
            print(f"    Evaluating GNews: '{item.title[:60]}...' (Publisher: {item.source_name})")
            
            # Step 2: Extraction (force webpage scrape)
            try:
                extracted = await extraction_service.extract_article(item, force_fetch=True)
            except Exception as e:
                print(f"      [SKIP] Step 2 error: {e}")
                continue

            if extracted.extraction_status == "EXTRACTION_FAILED" or not extracted.content or len(extracted.content.strip()) < 500:
                print(f"      [SKIP] Insufficient content extracted ({len(extracted.content or '')} chars < 500 min)")
                continue

            # Step 3: Cleaning
            cleaned = cleaning_service.clean_article(extracted)
            if cleaned.cleaning_status != CleaningStatus.SUCCESS or not cleaned.cleaned_content or len(cleaned.cleaned_content.strip()) < 500:
                print(f"      [SKIP] Cleaning rejected content")
                continue

            # Step 4: Duplicate Detection
            try:
                with get_db_session() as session:
                    dedup_service = DuplicateDetectionService(
                        config=DuplicateDetectionConfig(enable_historical_detection=True, persist_unique_articles=True)
                    )
                    dedup_result = dedup_service.check_article(cleaned, session=session)
                    session.commit()
            except Exception as e:
                print(f"      [SKIP] Dedup error: {e}")
                continue

            if dedup_result.status != "unique":
                print(f"      [SKIP] Duplicate detected ({dedup_result.decision.duplicate_reason})")
                continue

            # Step 5: Persistence
            try:
                persisted = knowledge_service.persist_from_step4(dedup_result)
                gnews_ingested.append(persisted)
                word_count = len(persisted.content.split()) if persisted.content else 0
                print(f"      [SUCCESS] Persisted to PostgreSQL! ID: {persisted.id} | Words: {word_count} | Source: {persisted.source_type}")
                break  # Ingest 1 GNews per category
            except ArticleDuplicateError:
                print(f"      [SKIP] Duplicate prevented by DB")
                continue
            except Exception as e:
                print(f"      [SKIP] Persistence error: {e}")
                continue

    # Query DB to show the updated status
    print("\n" + "=" * 80)
    print("UPDATED POSTGRESQL DATABASE SUMMARY BY SOURCE TYPE:")
    print("=" * 80)
    with get_db_session() as session:
        src_counts = session.execute(
            text("SELECT source_type, count(*) FROM news_articles GROUP BY source_type ORDER BY source_type")
        ).all()
        for src, cnt in src_counts:
            print(f"  - {src:<15}: {cnt} article(s)")

        total = session.scalar(select(func.count(NewsArticle.id)))
        print(f"\n  Total articles in PostgreSQL: {total}")

        # Show GNews articles specifically
        gnews_articles = session.scalars(
            select(NewsArticle).where(NewsArticle.source_type == "gnews").order_by(NewsArticle.id)
        ).all()
        print(f"\nStored GNews Articles ({len(gnews_articles)}):")
        for ga in gnews_articles:
            words = len(ga.content.split()) if ga.content else 0
            print(f"  - ID: {ga.id:<4} | Category: {ga.category:<24} | Publisher: {ga.source_name:<20} | Words: {words:<5} | Title: {ga.title[:55]}...")


if __name__ == "__main__":
    asyncio.run(main())
