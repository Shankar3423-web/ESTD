"""Ingest Authentic Sports Articles Across All Canonical Subcategories.

Covers:
- Cricket (9): Telugu Ranji Trophy (Mohammed Siraj, Hyderabad)
- Tennis (11): English ATP Zverev / Alcaraz Shanghai Masters
- Badminton (12): English Denmark Open (Sindhu, Lakshya Sen)
- Motorsport (13): English IndyCar Sebring Test (Alex Palou)
- Hockey (14): English Asian Games Hockey (Ishika Sambharwal)
- Athletics & Olympic Sports (15): English Neeraj Chopra LA Dreams
- Esports & Competitive Gaming (16): English SKO 2026 Championship
- Other Sports (17): English US Chess Championship (Caruana, Wesley So)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.services.duplicate_detection_service import DuplicateDetectionService
from backend.step5_knowledge_source.exceptions import ArticleDuplicateError
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.schemas.generation_request import ArticleGenerationRequest
from backend.step7_content_generation.services.mcp_generation_service import MCPGenerationService
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator

ARTICLES_TO_INGEST = [
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "language": "te",
        "title": "సిరాజ్ సేన విధ్వంసం.. హైదరాబాద్‌కు ఘన విజయం!",
        "url": "https://telugu.oneindia.com/sports/ranji-trophy-2026-mohammed-siraj-led-hyderabad-thrash-tripura-by-an-innings-tanay-shined-with-9-wi-510489.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 11:45:00 GMT",
    },
    {
        "subcategory_name": "Tennis",
        "subcategory_code": "SPORTS_TENNIS",
        "expected_sub_id": 11,
        "language": "en",
        "title": "Alexander Zverev confirmed as ATP year-end No. 1 after Carlos Alcaraz crashes out of Shanghai Masters",
        "url": "https://www.hindustantimes.com/sports/tennis/alexander-zverev-confirmed-as-atp-year-end-no-1-after-carlos-alcaraz-crashes-out-of-shanghai-masters-101791810410503.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 10:00:00 GMT",
    },
    {
        "subcategory_name": "Badminton",
        "subcategory_code": "SPORTS_BADMINTON",
        "expected_sub_id": 12,
        "language": "en",
        "title": "Sindhu faces nemesis An Se-young, Lakshya gets Chou test at Denmark Open",
        "url": "https://www.hindustantimes.com/sports/badminton/sindhu-faces-nemesis-an-se-young-lakshya-gets-chou-test-at-denmark-open-101791780476853.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 09:30:00 GMT",
    },
    {
        "subcategory_name": "Motorsport",
        "subcategory_code": "SPORTS_MOTORSPORT",
        "expected_sub_id": 13,
        "language": "en",
        "title": "Shake It Up: Alex Palou Puts IR-28 Through Pounding Test at Sebring",
        "url": "https://www.indycar.com/news/2026/10/10-12-palou-ir28-test-sebring",
        "source_name": "IndyCar Official",
        "source_type": "rss",
        "published_at": "Mon, 12 Oct 2026 18:00:00 GMT",
    },
    {
        "subcategory_name": "Hockey",
        "subcategory_code": "SPORTS_HOCKEY",
        "expected_sub_id": 14,
        "language": "en",
        "title": "Asian Games 2026: Gold medallist hockey player Ishika Sambharwal felicitated in Bhiwani",
        "url": "https://www.tribuneindia.com/news/haryana/asian-games-2026-gold-medallist-hockey-player-ishika-sambharwal-felicitated-in-bhiwani/",
        "source_name": "The Tribune India",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 08:15:00 GMT",
    },
    {
        "subcategory_name": "Athletics & Olympic Sports",
        "subcategory_code": "SPORTS_ATHLETICS",
        "expected_sub_id": 15,
        "language": "en",
        "title": "Humble beginnings to LA hopes, Neeraj relishes dream run",
        "url": "https://www.hindustantimes.com/sports/others/humble-beginnings-to-la-hopes-neeraj-relishes-dream-run-101791738491478.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 07:00:00 GMT",
    },
    {
        "subcategory_name": "Esports & Competitive Gaming",
        "subcategory_code": "SPORTS_ESPORTS",
        "expected_sub_id": 16,
        "language": "en",
        "title": "SKO 2026 Season 2 Main Tournament to Be Held on Oct. 18",
        "url": "https://www.invenglobal.com/articles/27022/sko-2026-season-2-main-tournament-to-be-held-on-oct-18",
        "source_name": "Inven Global",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 06:30:00 GMT",
    },
    {
        "subcategory_name": "Other Sports",
        "subcategory_code": "SPORTS_OTHER",
        "expected_sub_id": 17,
        "language": "en",
        "title": "Day Of Endgames Sees Caruana Join So At Top; Lee Sole Leader In Women's",
        "url": "https://www.chess.com/news/view/2026-us-chess-championships-round-4",
        "source_name": "Chess.com",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 01:00:00 GMT",
    },
]

async def run_ingestion():
    print("=" * 80)
    print("ESTD — INGESTING CANONICAL SPORTS SUBCATEGORIES (STEPS 1 TO 8)")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    knowledge_service = KnowledgeSourceService()
    mcp_service = MCPService()
    mcp_gen_service = MCPGenerationService(mcp_service=mcp_service)
    step8_orchestrator = Step8Orchestrator()

    results = []

    for idx, target in enumerate(ARTICLES_TO_INGEST, start=1):
        sub_name = target["subcategory_name"]
        print(f"\n[{idx}/{len(ARTICLES_TO_INGEST)}] Processing Subcategory: {sub_name} (ID: {target['expected_sub_id']})")
        print(f"  Source: {target['source_name']} | Lang: {target['language']}")
        print(f"  URL: {target['url']}")

        # Step 1: NewsItem
        item = NewsItem(
            title=target["title"],
            url=target["url"],
            source_name=target["source_name"],
            source_type=target["source_type"],
            category="Sports",
            subcategory=sub_name,
            published_at=target["published_at"],
            language=target["language"]
        )

        # Step 2: Extraction
        print("  [Step 2] Extracting full article...")
        try:
            extracted = await extraction_service.extract_article(item, force_fetch=True)
            print(f"    Extracted status: {extracted.extraction_status} | Length: {len(extracted.content or '')} chars")
        except Exception as e:
            print(f"    [ERROR] Step 2 Extraction failed: {e}")
            continue

        if not extracted.content or len(extracted.content.strip()) < 300:
            print(f"    [SKIP] Extracted content too short ({len(extracted.content or '')} chars)")
            continue

        # Step 3: Cleaning
        print("  [Step 3] Cleaning and normalizing...")
        cleaned = cleaning_service.clean_article(extracted)
        if cleaned.cleaning_status != CleaningStatus.SUCCESS or not cleaned.cleaned_content:
            print(f"    [SKIP] Step 3 Cleaning failed or empty")
            continue
        print(f"    Cleaned length: {len(cleaned.cleaned_content)} chars | Language: {cleaned.language}")

        # Step 4: Duplicate Detection
        print("  [Step 4] Checking duplicates...")
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
            print(f"    Dedup status: {dedup_result.status} (Reason: {dedup_result.decision.duplicate_reason})")
        except Exception as e:
            print(f"    [ERROR] Step 4 Dedup error: {e}")
            continue

        if dedup_result.status != "unique":
            print(f"    [NOTICE] Item already exists or duplicate detected. Moving forward.")
            # Even if duplicate, check if already in DB
            # We will look up existing article by URL
            with get_db_session() as session:
                from backend.database.models.news_article import NewsArticle
                existing_art = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                if existing_art:
                    art_id = existing_art.id
                    print(f"    Using existing DB article ID: {art_id}")
                else:
                    continue
        else:
            # Step 5: Knowledge Source Persistence
            print("  [Step 5] Persisting to PostgreSQL knowledge source...")
            try:
                persisted = knowledge_service.persist_from_step4(dedup_result)
                art_id = persisted.id
                print(f"    [SUCCESS] Persisted article ID: {art_id} | Subcategory ID: {persisted.subcategory_id}")
            except ArticleDuplicateError:
                with get_db_session() as session:
                    from backend.database.models.news_article import NewsArticle
                    existing_art = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                    art_id = existing_art.id if existing_art else None
                    print(f"    DB duplicate prevented. Existing article ID: {art_id}")
                if not art_id:
                    continue
            except Exception as e:
                print(f"    [ERROR] Step 5 Persistence error: {e}")
                continue

        # Step 6 & 7: Gemini AI Synthesis via MCP
        print(f"  [Step 7] Generating AI synthesis via MCP for Article ID {art_id}...")
        try:
            req = ArticleGenerationRequest(article_id=art_id)
            gen_resp = mcp_gen_service.generate_from_mcp_article(req)
            if not gen_resp.success or not gen_resp.data:
                print(f"    [ERROR] Step 7 Generation failed: {gen_resp.message}")
                continue
            generated_news = gen_resp.data
            print(f"    [SUCCESS] Generated Title: '{generated_news.title[:65]}...'")
            print(f"    Category: {generated_news.category} | Subcategory: {generated_news.subcategory}")
            print(f"    Summary: {len(generated_news.summary)} chars | Content: {len(generated_news.content)} chars")
        except Exception as e:
            print(f"    [ERROR] Step 7 Gemini error: {e}")
            continue

        # Step 8: Google Drive Staging / Document Management
        print(f"  [Step 8] Staging Google Document record...")
        try:
            with get_db_session() as session:
                doc_resp = step8_orchestrator.process_approved_content(
                    news=generated_news,
                    article_id=art_id,
                    session=session,
                    original_published_at=target["published_at"],
                )
                doc_id = getattr(doc_resp.data, "google_document_id", None) if doc_resp.data else None
                doc_url = getattr(doc_resp.data, "google_document_url", None) if doc_resp.data else None
                doc_status = doc_resp.status if doc_resp else "UNKNOWN"
                print(f"    [SUCCESS] Step 8 Status: {doc_status} | Doc ID: {doc_id}")
                results.append({
                    "subcategory": sub_name,
                    "sub_id": target["expected_sub_id"],
                    "article_id": art_id,
                    "title": target["title"][:60],
                    "generated_title": generated_news.title[:60],
                    "doc_status": doc_status,
                    "doc_id": doc_id,
                    "doc_url": doc_url
                })
        except Exception as e:
            print(f"    [ERROR] Step 8 handling error: {e}")

        # Sleep briefly between Gemini calls to respect API quotas
        await asyncio.sleep(2)

    print("\n" + "=" * 80)
    print("INGESTION SUMMARY ACROSS ALL ATTEMPTED SUBCATEGORIES")
    print("=" * 80)
    print(f"Total Successfully Completed: {len(results)}/{len(ARTICLES_TO_INGEST)}")
    for r in results:
        print(f" - [{r['subcategory']} (ID {r['sub_id']})] Article ID {r['article_id']} | '{r['generated_title']}' | Doc: {r['doc_status']}")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
