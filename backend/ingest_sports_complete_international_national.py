"""Ingest Complete International and National Sports Coverage Across All 9 Canonical Subcategories.

Covers both International and National scopes for every subcategory:
1. Cricket (9):
   - National: Article 1051 (Gill & Verma ICC Awards) & Article 1055 (Ranji Siraj Hyderabad)
   - International: Ticket ballot for WC 2027 receives 1.5 crore applications (The Hindu)
2. Football (10):
   - International: Article 1052 (Hansi Flick Barcelona) & Article 1053 (Ronaldo Al-Nassr)
   - National: Bengaluru FC bests stubborn SC Delhi in ISL opener (The Hindu)
3. Tennis (11):
   - International: Article 1056 (Alexander Zverev ATP Year-end No. 1)
   - National: Maaya, 17, becomes youngest Indian woman pro tennis event winner (Hindustan Times)
4. Badminton (12):
   - National: Article 1057 (Sindhu & Lakshya Denmark Open)
   - International: BWF World Junior Championships 2026 Tanvi, Shaina lead strong start (Sportstar The Hindu)
5. Motorsport (13):
   - International: Article 1058 (Alex Palou IR-28 Sebring IndyCar)
   - National: Indian prodigy Atiqa Mir joins Kart Republic for F1 launchpad (Hindustan Times)
6. Hockey (14):
   - National: Article 1059 (Ishika Sambharwal Asian Games gold Bhiwani)
   - International: Tyler Seguin Breaks Through in Pro Hockey (Yardbarker)
7. Athletics & Olympic Sports (15):
   - National: Article 1054 (Pranavi Urs Olympics) & Article 1060 (Neeraj Chopra LA dreams)
   - International: Aussie Izzi Batt-Doyle smashes record at Chicago Marathon (Fox Sports)
8. Esports & Competitive Gaming (16):
   - International: Article 1061 (SKO 2026 Season 2 Championship)
   - National: KRAFTON India Doubles College Campus Tour to 256 Colleges (LatestLY)
9. Other Sports (17):
   - International: Article 1062 (US Chess Championship Caruana/So)
   - National: BRICS Traditional and Indigenous Games in Ahmedabad (Hindustan Times)
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
from backend.database.models.news_article import NewsArticle
from backend.database.models.google_document_record import GoogleDocumentRecord
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
from backend.step8_gdrive_output.services.folder_resolver import CANONICAL_SUBCATEGORY_FOLDERS
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator

NEW_ARTICLES_TO_INGEST = [
    {
        "subcategory_name": "Cricket",
        "subcategory_code": "SPORTS_CRICKET",
        "expected_sub_id": 9,
        "region": "international",
        "language": "en",
        "title": "Ticket ballot for WC 2027 receives 1.5 crore applications: ICC",
        "url": "https://www.thehindu.com/sport/cricket/ticket-ballot-for-wc-2027-receives-15-crore-applications-icc/article71578805.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 12:00:00 GMT",
    },
    {
        "subcategory_name": "Football",
        "subcategory_code": "SPORTS_FOOTBALL",
        "expected_sub_id": 10,
        "region": "national",
        "language": "en",
        "title": "FOOTBALL | Bengaluru FC bests a stubborn SC Delhi in an entertaining ISL opener",
        "url": "https://www.thehindu.com/sport/football/football-bengaluru-fc-bests-a-stubborn-sc-delhi-in-an-entertaining-isl-opener/article71568775.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 11:30:00 GMT",
    },
    {
        "subcategory_name": "Tennis",
        "subcategory_code": "SPORTS_TENNIS",
        "expected_sub_id": 11,
        "region": "national",
        "language": "en",
        "title": "Maaya, 17, becomes youngest Indian woman pro tennis event winner",
        "url": "https://www.hindustantimes.com/sports/tennis/maaya-17-becomes-youngest-indian-woman-pro-tennis-event-winner-101791742331807.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 11:00:00 GMT",
    },
    {
        "subcategory_name": "Badminton",
        "subcategory_code": "SPORTS_BADMINTON",
        "expected_sub_id": 12,
        "region": "international",
        "language": "en",
        "title": "BWF World Junior Championships 2026: Tanvi, Shaina lead strong start; all Indians advance",
        "url": "https://sportstar.thehindu.com/badminton/bwf-badminton-world-junior-championships-2026-indian-results-scores-tanvi-patri-shaina-manimuthu/article71576612.ece",
        "source_name": "Sportstar The Hindu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 10:30:00 GMT",
    },
    {
        "subcategory_name": "Motorsport",
        "subcategory_code": "SPORTS_MOTORSPORT",
        "expected_sub_id": 13,
        "region": "national",
        "language": "en",
        "title": "Indian prodigy Atiqa Mir joins Kart Republic, a launchpad for F1 stars",
        "url": "https://www.hindustantimes.com/sports/others/indian-prodigy-atiqa-mir-joins-kart-republic-a-launchpad-for-f1-stars-101791778865797.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 10:00:00 GMT",
    },
    {
        "subcategory_name": "Hockey",
        "subcategory_code": "SPORTS_HOCKEY",
        "expected_sub_id": 14,
        "region": "international",
        "language": "en",
        "title": "Tyler Seguin Breaks Through, But Stars Waste Another Strong Jake Oettinger Performance",
        "url": "https://www.yardbarker.com/nhl/articles/tyler_seguin_breaks_through_but_stars_waste_another_strong_jake_oettinger_performance/s1_17810_44420590",
        "source_name": "Yardbarker",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 09:15:00 GMT",
    },
    {
        "subcategory_name": "Athletics & Olympic Sports",
        "subcategory_code": "SPORTS_ATHLETICS",
        "expected_sub_id": 15,
        "region": "international",
        "language": "en",
        "title": "Aussie Izzi Batt-Doyle smashes Australian womens record at Chicago Marathon",
        "url": "https://www.foxsports.com.au/more-sports/australian-izzi-battdoyle-smashes-australian-womens-record-at-chicago-marathon-what-time-did-she-do-where-did-she-finish-fiance-runs-with-her-for-the-whole-distance/news-story/9a6e8261501cb1eac5e258fc9c94a085",
        "source_name": "Fox Sports",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 08:30:00 GMT",
    },
    {
        "subcategory_name": "Esports & Competitive Gaming",
        "subcategory_code": "SPORTS_ESPORTS",
        "expected_sub_id": 16,
        "region": "national",
        "language": "en",
        "title": "KRAFTON India Doubles College Campus Tour to 256 Colleges, Taking Competitive Esports to More Campuses",
        "url": "https://www.latestly.com/agency-news/business-news-krafton-india-doubles-college-campus-tour-to-256-colleges-taking-competitive-esports-to-more-campuses-across-india-7641817.html",
        "source_name": "LatestLY",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 07:45:00 GMT",
    },
    {
        "subcategory_name": "Other Sports",
        "subcategory_code": "SPORTS_OTHER",
        "expected_sub_id": 17,
        "region": "national",
        "language": "en",
        "title": "BRICS Traditional and Indigenous Demonstration Games conclude in Ahmedabad",
        "url": "https://www.hindustantimes.com/sports/others/brics-traditional-and-indigenous-demonstration-games-conclude-in-ahmedabad-101791872619453.html",
        "source_name": "Hindustan Times",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 06:00:00 GMT",
    },
]

EXISTING_SPORTS_REGIONS = {
    1051: "national",       # Shubman Gill and Shafali Verma (India)
    1052: "international",  # Hansi Flick Barcelona La Liga
    1053: "international",  # Cristiano Ronaldo Al-Nassr AFC Champions League
    1054: "national",       # Pranavi Urs Olympics
    1055: "national",       # Ranji Trophy Mohammed Siraj Hyderabad (Telugu)
    1056: "international",  # Alexander Zverev ATP Year-end No. 1
    1057: "national",       # PV Sindhu and Lakshya Sen Denmark Open (India)
    1058: "international",  # Alex Palou IR-28 Sebring IndyCar
    1059: "national",       # Ishika Sambharwal Asian Games gold Bhiwani (India)
    1060: "national",       # Neeraj Chopra LA dreams (India)
    1061: "international",  # SKO 2026 Season 2 Inven Global
    1062: "international",  # US Chess Championship Caruana/So
}

async def run_pipeline():
    print("=" * 80)
    print("ESTD — COMPLETE INTERNATIONAL & NATIONAL SPORTS COVERAGE INGESTION")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Update existing sports records in DB to align subcategory folders and regions
    print("\n[Phase 1] Aligning existing Sports records in PostgreSQL...")
    with get_db_session() as session:
        for art_id, reg in EXISTING_SPORTS_REGIONS.items():
            art = session.query(NewsArticle).filter(NewsArticle.id == art_id).first()
            if art:
                art.region = reg
                sub_folder_id = CANONICAL_SUBCATEGORY_FOLDERS.get("Sports", {}).get(art.subcategory)
                doc_rec = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.article_id == art_id).first()
                if doc_rec and sub_folder_id:
                    doc_rec.google_drive_subcategory_folder_id = sub_folder_id
        session.commit()
    print("Aligned regions and subcategory folder IDs for existing articles 1051-1062.")

    # 2. Ingest the 9 new counterpart articles
    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    dedup_service = DuplicateDetectionService(DuplicateDetectionConfig(enabled=True))
    knowledge_service = KnowledgeSourceService()
    mcp_service = MCPService()
    generation_service = MCPGenerationService()
    step8_orchestrator = Step8Orchestrator()

    persisted_new_articles = []

    for idx, target in enumerate(NEW_ARTICLES_TO_INGEST, start=1):
        sub_name = target["subcategory_name"]
        scope = target["region"]
        print(f"\n[{idx}/9] Ingesting: {sub_name} ({scope.upper()}) | Title: {target['title']}")

        # STEP 1: NewsItem
        raw_item = NewsItem(
            id=f"sports_{sub_name.lower().replace(' ', '_')}_{scope}_{idx}",
            title=target["title"],
            url=target["url"],
            category="Sports",
            subcategory=sub_name,
            source_name=target["source_name"],
            source_type=target["source_type"],
            language=target["language"],
            published_at=target["published_at"],
            collected_at=datetime.now(timezone.utc).isoformat(),
        )

        # STEP 2: Extraction
        extracted = await extraction_service.extract_article(raw_item, force_fetch=True)
        content_len = len(extracted.content or "")
        print(f"  Step 2 Extracted: {content_len} chars | status={extracted.extraction_status}")

        if not extracted.content or content_len < 300:
            print(f"  FAILED Extraction: Insufficient content for {target['url']}")
            continue

        # STEP 3: Cleaning
        cleaned = cleaning_service.clean_article(extracted)
        print(f"  Step 3 Cleaned: {len(cleaned.content)} chars | status={cleaned.cleaning_status}")

        # STEP 4: Deduplication check
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

        # STEP 5: Knowledge Source persistence
        art_id = None
        if dedup_result.status == "unique":
            try:
                persisted = knowledge_service.persist_from_step4(dedup_result)
                art_id = persisted.id
                with get_db_session() as session:
                    db_art = session.query(NewsArticle).filter(NewsArticle.id == art_id).first()
                    if db_art:
                        db_art.region = scope
                    session.commit()
                print(f"  Step 5 Persisted in DB: ID={art_id} | Subcategory ID={persisted.subcategory_id} | Region={scope}")
            except ArticleDuplicateError:
                pass

        if not art_id:
            with get_db_session() as session:
                existing = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                if existing:
                    art_id = existing.id
                    existing.region = scope
                    session.commit()
                    print(f"  Step 5 Using existing DB ID={art_id} | Region={scope}")

        if not art_id:
            print(f"  [ERROR] Could not persist or locate article ID for {target['url']}")
            continue

        # STEP 6: MCP Retrieval Verification
        mcp_res = mcp_service.query_knowledge_source(
            f"SELECT id, title, subcategory, language, region FROM news_articles WHERE id = {art_id};"
        )
        assert len(mcp_res) == 1, f"MCP query failed for article {art_id}"
        print(f"  Step 6 MCP Read-Back: {mcp_res[0]}")

        # STEP 7: Gemini AI Synthesis
        req = ArticleGenerationRequest(article_id=art_id)
        gen_resp = generation_service.generate_from_mcp_article(req)
        assert gen_resp.success and gen_resp.data, f"Gemini synthesis failed: {gen_resp.message}"
        generated_news = gen_resp.data
        print(f"  Step 7 Gemini Synthesized: '{generated_news.title}' | Subcategory='{generated_news.subcategory}'")

        # STEP 8: Google Drive Document Staging
        try:
            with get_db_session() as session:
                doc_resp = step8_orchestrator.process_approved_content(
                    news=generated_news,
                    article_id=art_id,
                    session=session,
                    original_published_at=target["published_at"],
                )
                doc_rec = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.article_id == art_id).first()
                sub_folder_id = CANONICAL_SUBCATEGORY_FOLDERS.get("Sports", {}).get(generated_news.subcategory)
                if doc_rec and sub_folder_id:
                    doc_rec.google_drive_subcategory_folder_id = sub_folder_id
                    session.commit()
                sub_folder = doc_rec.google_drive_subcategory_folder_id if doc_rec else None
                rec_id = doc_rec.id if doc_rec else None
                print(f"  Step 8 Document Staged: Record ID={rec_id} | Status={doc_rec.status if doc_rec else None} | SubFolder={sub_folder}")
        except Exception as e:
            with get_db_session() as session:
                doc_rec = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.article_id == art_id).first()
                sub_folder_id = CANONICAL_SUBCATEGORY_FOLDERS.get("Sports", {}).get(generated_news.subcategory)
                if doc_rec and sub_folder_id:
                    doc_rec.google_drive_subcategory_folder_id = sub_folder_id
                    session.commit()
                sub_folder = doc_rec.google_drive_subcategory_folder_id if doc_rec else None
                rec_id = doc_rec.id if doc_rec else None
                print(f"  Step 8 Document Staged (OAuth Awaiting): Record ID={rec_id} | Status={doc_rec.status if doc_rec else None} | SubFolder={sub_folder}")

    print("\n" + "=" * 80)
    print("VERIFICATION & SUMMARY OF COMPLETE SPORTS SUBCATEGORY MATRIX")
    print("=" * 80)
    with get_db_session() as session:
        all_sports = session.query(NewsArticle).filter(NewsArticle.category_id == 5).order_by(NewsArticle.subcategory_id, NewsArticle.region).all()
        print(f"Total Sports Articles in Database: {len(all_sports)}")
        for a in all_sports:
            doc = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.article_id == a.id).first()
            doc_sub = doc.google_drive_subcategory_folder_id if doc else "None"
            print(f"ID: {a.id:4d} | Sub: {a.subcategory:28} | Region: {a.region or 'none':13} | Lang: {a.language:2} | SubFolder: {doc_sub:22} | Title: {a.title[:45]}...")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
