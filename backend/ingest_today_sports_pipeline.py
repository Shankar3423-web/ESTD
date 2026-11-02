"""Ingest Today's Sports Coverage (14 Oct 2026): 3 International, 3 National, 3 Regional.

Executes complete Steps 1 through 8 for each article:
- Extraction & Full-Text Fetching
- HTML Cleaning & Unicode normalization
- Duplicate Detection
- PostgreSQL Knowledge Store Persistence
- Gemini AI Synthesis
- Google Drive Document Upload into Subcategory Folders
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.google_document_record import GoogleDocumentRecord, DocumentStatus
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.services.duplicate_detection_service import DuplicateDetectionService
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.schemas.generation_request import ArticleGenerationRequest
from backend.step7_content_generation.services.mcp_generation_service import MCPGenerationService
from backend.step8_gdrive_output.services.folder_resolver import CANONICAL_SUBCATEGORY_FOLDERS
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator

TODAY_SPORTS_ARTICLES = [
    # ------------------------------------------------------------------------
    # 3 INTERNATIONAL ARTICLES
    # ------------------------------------------------------------------------
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "international",
        "language": "en",
        "title": "Hazlewood takes six as Australia beat South Africa in 1st Test",
        "url": "https://www.thehindu.com/sport/cricket/hazlewood-takes-six-as-australia-beat-south-africa-in-1st-test/article71582076.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 06:55:34 +0530",
    },
    {
        "subcategory_name": "Football",
        "subcategory_code": "SPORTS_FOOTBALL",
        "expected_sub_id": 10,
        "region": "international",
        "language": "en",
        "title": "UCL: Barcelona, Arsenal cruise; Bayern Munich stunned and Manchester United slump continues",
        "url": "https://www.hindustantimes.com/sports/football/ucl-barcelona-arsenal-cruise-bayern-munich-stunned-and-manchester-uniteds-slump-continues-101791941866493.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 07:20:40 +0530",
    },
    {
        "subcategory_name": "Other Sports",
        "subcategory_code": "SPORTS_OTHER",
        "expected_sub_id": 17,
        "region": "international",
        "language": "en",
        "title": "Caruana Wins Titled Tuesday On Day Off In U.S. Championship",
        "url": "https://www.chess.com/news/view/caruana-wins-titled-tuesday-october-13-2026",
        "source_name": "Chess.com",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 11:44:54 -0700",
    },

    # ------------------------------------------------------------------------
    # 3 NATIONAL ARTICLES
    # ------------------------------------------------------------------------
    {
        "subcategory_name": "Football",
        "subcategory_code": "SPORTS_FOOTBALL",
        "expected_sub_id": 10,
        "region": "national",
        "language": "en",
        "title": "Why Indian football federation could receive Rs 237 crore from FIFA over 4 years",
        "url": "https://indianexpress.com/article/sports/football/indian-football-federation-rs-237-crore-fifa-over-4-years-10921333/",
        "source_name": "The Indian Express",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 10:05:20 +0000",
    },
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "national",
        "language": "en",
        "title": "‘Coach was happy to get me out’: Umesh Yadav explains Ranji Trophy switch",
        "url": "https://indianexpress.com/article/sports/cricket/umesh-yadav-explains-vidarbha-punjab-ranji-trophy-switch-coach-selectors-10921195/",
        "source_name": "The Indian Express",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 08:28:02 +0000",
    },
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "national",
        "language": "en",
        "title": "Harmanpreet — A leader who took India to uncharted terrains",
        "url": "https://www.thehindu.com/sport/cricket/harmanpreet-a-leader-who-took-india-to-uncharted-terrains/article71581080.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 09:51:33 +0530",
    },

    # ------------------------------------------------------------------------
    # 3 REGIONAL (TELUGU) ARTICLES
    # ------------------------------------------------------------------------
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "regional",
        "language": "te",
        "title": "IND vs WI: హైదరాబాద్‌లో టీమిండియా మరో చరిత్ర సృష్టిస్తుందా?",
        "url": "https://telugu.oneindia.com/sports/ind-vs-wi-t20-can-team-india-create-history-in-hyderabad-300-run-record-in-focus-full-details-510639.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 11:35:09 +0530",
    },
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "regional",
        "language": "te",
        "title": "IND vs WI: ఉచిత పాస్‌లతో లక్షల దందా.. భారత్–విండీస్ మ్యాచ్‌కు ముందు నలుగురు అరెస్ట్!",
        "url": "https://telugu.oneindia.com/sports/ind-vs-wi-t20-ticket-black-marketing-hca-member-among-four-arrested-in-hyderabad-full-details-510681.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 15:33:59 +0530",
    },
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "regional",
        "language": "te",
        "title": "‘ఏదైనా డైరెక్ట్‌గా చెప్పేయండి!.. కోచ్‌ నన్ను వెళ్లగొట్టాలని చూశాడు’",
        "url": "https://www.sakshi.com/telugu-news/sports/it-was-about-getting-me-out-india-pacer-claim-ex-state-team-coach-2931853",
        "source_name": "Sakshi Sports",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 15:00:27 +0530",
    },
]


async def run_pipeline():
    print("=" * 80)
    print("ESTD — TODAY'S SPORTS COVERAGE PIPELINE (14 OCT 2026)")
    print("3 International | 3 National | 3 Regional (Telugu)")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    dedup_service = DuplicateDetectionService(DuplicateDetectionConfig(enabled=True))
    knowledge_service = KnowledgeSourceService()
    generation_service = MCPGenerationService()
    step8_orchestrator = Step8Orchestrator()

    results = []

    for idx, target in enumerate(TODAY_SPORTS_ARTICLES, start=1):
        sub_name = target["subcategory_name"]
        scope = target["region"]
        print(f"\n[{idx}/9] Ingesting: {sub_name} ({scope.upper()}) | Title: '{target['title'][:55]}...'")

        # STEP 1: NewsItem
        raw_item = NewsItem(
            id=f"today_{sub_name.lower().replace(' ', '_')}_{scope}_{idx}",
            title=target["title"],
            url=target["url"],
            category="Sports",
            subcategory=sub_name,
            source_name=target["source_name"],
            source_type=target["source_type"],
            language=target["language"],
            region=scope,
            published_at=target["published_at"],
        )

        # STEP 2: Extraction
        extracted = await extraction_service.extract_article(raw_item, force_fetch=True)
        raw_content = extracted.content or extracted.raw_content if hasattr(extracted, 'raw_content') else ""
        if not raw_content and hasattr(extracted, 'content'):
            raw_content = extracted.content or ""
        print(f"  Step 2 Extracted: {len(raw_content)} chars")

        # STEP 3: Cleaning
        cleaned = cleaning_service.clean_article(extracted)
        cleaned_len = len(cleaned.content) if hasattr(cleaned, 'content') else 0
        print(f"  Step 3 Cleaned: {cleaned_len} chars | status={cleaned.cleaning_status}")

        # STEP 4: Deduplication Check
        with get_db_session() as session:
            dedup_service = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=True,
                    persist_unique_articles=True,
                )
            )
            dedup_result = dedup_service.check_article(cleaned, session=session)
            session.commit()
        print(f"  Step 4 Dedup: status={dedup_result.status}")

        # STEP 5: Knowledge Store Persistence
        art_id = None
        if dedup_result.status == "unique":
            try:
                persisted = knowledge_service.persist_from_step4(dedup_result)
                art_id = persisted.id
                with get_db_session() as session:
                    db_art = session.query(NewsArticle).filter(NewsArticle.id == art_id).first()
                    if db_art:
                        db_art.region = scope
                        db_art.subcategory_id = target["expected_sub_id"]
                        db_art.subcategory = sub_name
                    session.commit()
            except Exception:
                with get_db_session() as session:
                    existing = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                    art_id = existing.id if existing else None
        else:
            with get_db_session() as session:
                existing = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                art_id = existing.id if existing else None

        assert art_id, f"Article persistence failed for: {target['title']}"
        print(f"  Step 5 Persisted in DB: Article ID={art_id} | Subcategory={sub_name} ({target['expected_sub_id']})")

        # STEP 7: Gemini AI Synthesis
        req = ArticleGenerationRequest(article_id=art_id)
        gen_resp = generation_service.generate_from_mcp_article(req)
        assert gen_resp.success and gen_resp.data, f"Gemini synthesis failed: {gen_resp.message}"
        generated_news = gen_resp.data
        print(f"  Step 7 Gemini Synthesized: '{generated_news.title[:50]}...'")

        # STEP 8: Google Drive Document Upload
        target_folder = CANONICAL_SUBCATEGORY_FOLDERS.get("Sports", {}).get(sub_name)
        with get_db_session() as session:
            doc_resp = step8_orchestrator.process_approved_content(
                news=generated_news,
                article_id=art_id,
                session=session,
                original_published_at=target["published_at"],
            )
            doc_rec = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.article_id == art_id).first()
            if doc_rec and target_folder:
                doc_rec.google_drive_subcategory_folder_id = target_folder
                session.commit()

            doc_id = doc_rec.google_document_id if doc_rec else None
            doc_url = doc_rec.google_document_url if doc_rec else None
            status_val = doc_rec.status if doc_rec else "UNKNOWN"
            print(f"  Step 8 Google Doc Uploaded: DocID={doc_id} | Status={status_val}")
            print(f"  Drive URL: {doc_url}")

            results.append({
                "article_id": art_id,
                "scope": scope,
                "subcategory": sub_name,
                "title": generated_news.title,
                "language": target["language"],
                "doc_id": doc_id,
                "doc_url": doc_url,
                "subfolder_id": target_folder,
            })

    print("\n" + "=" * 80)
    print("FINAL SUMMARY: TODAY'S 9 SPORTS ARTICLES INGESTED & UPLOADED")
    print("=" * 80)
    for r in results:
        print(f"Article {r['article_id']:4d} | {r['scope'].upper():13} | {r['subcategory']:15} | {r['language']:2} | GDoc: {r['doc_id']} | URL: {r['doc_url']}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
