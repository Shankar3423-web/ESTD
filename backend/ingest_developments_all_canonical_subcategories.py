"""ESTD Developments Category — Complete End-to-End Pipeline Ingestion & Verification.

Executes:
Step 1: Source Discovery & NewsItem
Step 2: Webpage Scraping & Extraction (Sufficiency Check)
Step 3: Content Cleaning & Normalization (Preserving Telugu Unicode, policy facts, dates)
Step 4: Deduplication (URL Normalization & SHA-256 Content Hashing)
Step 5: PostgreSQL Persistence & Read-back from news_articles
Step 6: Read-Only MCP Retrieval
Step 7: Gemini AI Factual Synthesis & Schema Validation
Step 8: Google Drive Google Docs Creation, Folder Placement & Live Read-back

Covers all 7 Canonical Developments Subcategories:
1. Government & Public Policy (ID: 25, DEV_GOV_POLICY)
2. Infrastructure & Urban Planning (ID: 26, DEV_INFRA)
3. Energy, Climate & Environment (ID: 27, DEV_ENERGY_CLIMATE)
4. Health & Medical Sciences (ID: 28, DEV_HEALTH_MED)
5. Education & Learning Policy (ID: 29, DEV_EDUCATION)
6. Science & Research Discoveries (ID: 30, DEV_SCIENCE_RESEARCH)
7. Global Affairs & Geopolitics (ID: 31, DEV_GLOBAL_AFFAIRS)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.constants.categories import ESTDCategory
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.category import Category
from backend.database.models.google_document_record import GoogleDocumentRecord
from backend.database.models.news_article import NewsArticle
from backend.database.models.subcategory import Subcategory
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
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver, CANONICAL_SUBCATEGORY_FOLDERS
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator


DEVELOPMENTS_ARTICLES_TO_INGEST: List[Dict[str, Any]] = [
    # 1. Government & Public Policy (ID: 25) - National (India)
    {
        "subcategory_name": "Government & Public Policy",
        "subcategory_code": "DEV_GOV_POLICY",
        "expected_sub_id": 25,
        "scope": "national",
        "language": "en",
        "title": "Mayawati demands regularisation of contractual employees working in Uttar Pradesh departments",
        "url": "https://www.thehindu.com/news/national/uttar-pradesh/mayawati-demands-regularisation-of-contractual-employees-working-in-uttar-pradesh-departments/article71584367.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 11:22:26 +0530",
    },
    # 2. Government & Public Policy (ID: 25) - Regional (Telangana / Telugu Unicode)
    {
        "subcategory_name": "Government & Public Policy",
        "subcategory_code": "DEV_GOV_POLICY",
        "expected_sub_id": 25,
        "scope": "regional",
        "language": "te",
        "title": "స్థానిక ఎన్నికల్లో ఓటు ఉందా, ఇలా చెక్ చేసుకోండి - లేకపోతే వెంటనే..!!",
        "url": "https://telugu.oneindia.com/news/andhra-pradesh/state-election-commission-modernises-portal-ahead-of-local-body-polls-here-the-details-510771.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 11:17:44 +0530",
    },
    # 3. Infrastructure & Urban Planning (ID: 26) - Regional (Telangana / Hyderabad)
    {
        "subcategory_name": "Infrastructure & Urban Planning",
        "subcategory_code": "DEV_INFRA",
        "expected_sub_id": 26,
        "scope": "regional",
        "language": "en",
        "title": "Convention hall or hotel? Midnight biryani, menu card trigger police raid at Barkas venue",
        "url": "https://telanganatoday.com/convention-hall-or-hotel-midnight-biryani-menu-card-trigger-police-raid-at-barkas-venue",
        "source_name": "Telangana Today",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 03:48:25 +0000",
    },
    # 4. Infrastructure & Urban Planning (ID: 26) - National (India / Hyderabad)
    {
        "subcategory_name": "Infrastructure & Urban Planning",
        "subcategory_code": "DEV_INFRA",
        "expected_sub_id": 26,
        "scope": "national",
        "language": "en",
        "title": "Hyderabad’s Uppal stadium turns sea of blue as city hosts international cricket after two years",
        "url": "https://www.thehindu.com/news/cities/Hyderabad/hyderabads-uppal-stadium-turns-sea-of-blue-as-city-hosts-international-cricket-after-two-years/article71584857.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 00:16:51 +0530",
    },
    # 5. Energy, Climate & Environment (ID: 27) - National (India)
    {
        "subcategory_name": "Energy, Climate & Environment",
        "subcategory_code": "DEV_ENERGY_CLIMATE",
        "expected_sub_id": 27,
        "scope": "national",
        "language": "en",
        "title": "Mining project threatens future of rare Jeypore ground gecko",
        "url": "https://www.thehindu.com/sci-tech/energy-and-environment/mining-project-threatens-future-of-rare-jeypore-ground-gecko/article71582605.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 00:21:26 +0530",
    },
    # 6. Health & Medical Sciences (ID: 28) - International
    {
        "subcategory_name": "Health & Medical Sciences",
        "subcategory_code": "DEV_HEALTH_MED",
        "expected_sub_id": 28,
        "scope": "international",
        "language": "en",
        "title": "WHO Director-General visits Jordan to recognize strong collaboration on health system delivery, emergency relief and advancing mental health",
        "url": "https://www.who.int/news/item/25-02-2026-who-director-general-visits-jordan-to-recognize-strong-collaboration-on-health-system-delivery--emergency-relief-and-advancing-mental-health",
        "source_name": "World Health Organization",
        "source_type": "rss",
        "published_at": "Wed, 25 Feb 2026 18:06:55 Z",
    },
    # 7. Health & Medical Sciences (ID: 28) - National (India)
    {
        "subcategory_name": "Health & Medical Sciences",
        "subcategory_code": "DEV_HEALTH_MED",
        "expected_sub_id": 28,
        "scope": "national",
        "language": "en",
        "title": "Licences of three Mumbai blood banks suspended for offering gifts",
        "url": "https://www.thehindu.com/news/cities/mumbai/licences-of-three-mumbai-blood-banks-suspended-for-offering-gifts/article71584515.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 10:31:19 +0530",
    },
    # 8. Education & Learning Policy (ID: 29) - National (India)
    {
        "subcategory_name": "Education & Learning Policy",
        "subcategory_code": "DEV_EDUCATION",
        "expected_sub_id": 29,
        "scope": "national",
        "language": "en",
        "title": "NCTE issues clarification on fake notice claiming 50% graduation marks mandatory for TGT appointments",
        "url": "https://indianexpress.com/article/education/ncte-issues-clarification-over-fake-tgt-50-graduation-marks-are-mandatory-for-tgt-appointments-notice-10922509/",
        "source_name": "The Indian Express",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 05:44:03 +0000",
    },
    # 9. Science & Research Discoveries (ID: 30) - International
    {
        "subcategory_name": "Science & Research Discoveries",
        "subcategory_code": "DEV_SCIENCE_RESEARCH",
        "expected_sub_id": 30,
        "scope": "international",
        "language": "en",
        "title": "Consumers need clearer answers before they can trust precision fermentation, new report finds",
        "url": "https://phys.org/news/2026-10-consumers-clearer-precision-fermentation.html",
        "source_name": "Phys.org",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 23:40:01 EDT",
    },
    # 10. Global Affairs & Geopolitics (ID: 31) - International
    {
        "subcategory_name": "Global Affairs & Geopolitics",
        "subcategory_code": "DEV_GLOBAL_AFFAIRS",
        "expected_sub_id": 31,
        "scope": "international",
        "language": "en",
        "title": "Haiti sanctions renewed: Starving the gangs of bullets",
        "url": "https://news.un.org/feed/view/en/story/2026/10/1168598",
        "source_name": "UN News",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 12:00:00 +0000",
    },
]


async def run_pipeline():
    print("=" * 80)
    print("ESTD DEVELOPMENTS CATEGORY — FULL PIPELINE INGESTION & DOCUMENT CREATION")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    # Initialize shared pipeline services
    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    knowledge_service = KnowledgeSourceService()
    mcp_service = MCPService()
    mcp_gen_service = MCPGenerationService(mcp_service=mcp_service)
    gdrive_service = GoogleDriveService()
    folder_resolver = DriveFolderResolver(gdrive_service=gdrive_service)
    step8_orchestrator = Step8Orchestrator(
        gdrive_service=gdrive_service,
        folder_resolver=folder_resolver,
    )

    results: List[Dict[str, Any]] = []

    for idx, target in enumerate(DEVELOPMENTS_ARTICLES_TO_INGEST, start=1):
        sub_name = target["subcategory_name"]
        print(f"\n[{idx}/{len(DEVELOPMENTS_ARTICLES_TO_INGEST)}] Processing: {sub_name} (ID: {target['expected_sub_id']})")
        print(f"  Source: {target['source_name']} | Scope: {target['scope']} | Lang: {target['language']}")
        print(f"  URL: {target['url']}")

        # STEP 1: NewsItem
        item = NewsItem(
            title=target["title"],
            url=target["url"],
            source_name=target["source_name"],
            source_type=target["source_type"],
            category="Developments",
            subcategory=sub_name,
            published_at=target["published_at"],
            language=target["language"],
            region="IN" if target["scope"] in ("national", "regional") else "US",
        )

        # STEP 2: Extraction
        print("  [Step 2] Webpage scraping & content extraction...")
        try:
            extracted = await extraction_service.extract_article(item, force_fetch=True)
            body_len = len(extracted.content or "")
            print(f"    Status: {extracted.extraction_status.value} | Extracted: {body_len} chars | Method: {extracted.extraction_method.value}")
        except Exception as exc:
            print(f"    [ERROR] Step 2 Extraction failed: {exc}")
            continue

        if not extracted.content or len(extracted.content.strip()) < 200:
            print(f"    [SKIP] Extracted content too short ({body_len} chars)")
            continue

        # STEP 3: Cleaning & Normalization
        print("  [Step 3] Content cleaning & Unicode normalization...")
        cleaned = cleaning_service.clean_article(extracted)
        if cleaned.cleaning_status != CleaningStatus.SUCCESS or not cleaned.cleaned_content:
            print(f"    [SKIP] Step 3 Cleaning failed or returned empty")
            continue
        print(f"    Cleaned length: {len(cleaned.cleaned_content)} chars | Lang: {cleaned.language}")

        # STEP 4: Deduplication
        print("  [Step 4] Checking duplicate protection...")
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
        except Exception as exc:
            print(f"    [ERROR] Step 4 Dedup error: {exc}")
            continue

        art_id = None
        if dedup_result.status != "unique":
            print("    [NOTICE] Duplicate detected, retrieving existing PostgreSQL row...")
            with get_db_session() as session:
                existing = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                if existing:
                    art_id = existing.id
                    print(f"    Using existing article ID: {art_id}")
                else:
                    continue
        else:
            # STEP 5: Persistence to PostgreSQL Knowledge Source
            print("  [Step 5] Persisting to PostgreSQL knowledge source (news_articles)...")
            try:
                persisted = knowledge_service.persist_from_step4(dedup_result)
                art_id = persisted.id
                print(f"    [SUCCESS] Persisted article ID: {art_id} | Category ID: {persisted.category_id} | Subcategory ID: {persisted.subcategory_id}")
            except ArticleDuplicateError:
                with get_db_session() as session:
                    existing = session.query(NewsArticle).filter(NewsArticle.url == target["url"]).first()
                    art_id = existing.id if existing else None
                    print(f"    DB duplicate prevented. Existing article ID: {art_id}")
                if not art_id:
                    continue
            except Exception as exc:
                print(f"    [ERROR] Step 5 Persistence error: {exc}")
                continue

        # STEP 6: MCP Read-Only Retrieval Verification
        print(f"  [Step 6] MCP Read-Only Retrieval for Article ID {art_id}...")
        try:
            mcp_data = mcp_gen_service.fetch_article_via_mcp(art_id)
            print(f"    [SUCCESS] MCP returned: '{mcp_data.get('title', '')[:50]}...' | Category: {mcp_data.get('category')} | Subcat: {mcp_data.get('subcategory')}")
        except Exception as exc:
            print(f"    [ERROR] Step 6 MCP retrieval failed: {exc}")
            continue

        # STEP 7: Gemini AI Structured Content Generation
        print(f"  [Step 7] Generating AI synthesis via Gemini...")
        try:
            req = ArticleGenerationRequest(article_id=art_id)
            gen_resp = mcp_gen_service.generate_from_mcp_article(req)
            if not gen_resp.success or not gen_resp.data:
                print(f"    [ERROR] Step 7 Generation failed: {gen_resp.message}")
                continue
            generated_news = gen_resp.data
            print(f"    [SUCCESS] Generated Title: '{generated_news.title[:60]}...'")
            print(f"    Summary: {len(generated_news.summary)} chars | Content: {len(generated_news.content)} chars")
            print(f"    Category: {generated_news.category} | Subcategory: {generated_news.subcategory}")
        except Exception as exc:
            print(f"    [ERROR] Step 7 Gemini error: {exc}")
            continue

        # STEP 8: Google Drive Document Creation & Verification
        print(f"  [Step 8] Creating Google Document in Google Drive...")
        doc_id = None
        doc_url = None
        doc_status = "UNKNOWN"
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
                sub_folder_id = getattr(doc_resp.data, "google_drive_subcategory_folder_id", None) if doc_resp.data else None
                print(f"    [SUCCESS] Doc Status: {doc_status} | Doc ID: {doc_id} | Subfolder ID: {sub_folder_id}")

            # Verify by reading back metadata from Google Drive API
            if doc_id and not doc_id.startswith("mock_"):
                try:
                    doc_meta = gdrive_service.get_file_metadata(doc_id)
                    print(f"    [LIVE READ-BACK] Verified Google Doc: '{doc_meta.get('name')}' (Trashed: {doc_meta.get('trashed')})")
                    print(f"    Parents: {doc_meta.get('parents')}")
                except Exception as meta_exc:
                    print(f"    [WARNING] Read-back from Drive failed: {meta_exc}")

            results.append({
                "subcategory": sub_name,
                "sub_id": target["expected_sub_id"],
                "article_id": art_id,
                "title": target["title"][:50],
                "generated_title": generated_news.title[:50],
                "doc_status": doc_status,
                "doc_id": doc_id,
                "doc_url": doc_url,
                "language": target["language"],
                "scope": target["scope"],
            })
        except Exception as exc:
            print(f"    [ERROR] Step 8 handling error: {exc}")

        # Sleep briefly between Gemini and Google Drive calls to respect rate limits
        await asyncio.sleep(2)

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION SUMMARY ACROSS ALL 7 CANONICAL DEVELOPMENTS SUBCATEGORIES")
    print("=" * 80)
    print(f"Total Successfully Completed: {len(results)}/{len(DEVELOPMENTS_ARTICLES_TO_INGEST)}")
    for r in results:
        print(f" - [{r['subcategory']} (ID {r['sub_id']})] Art ID {r['article_id']} | Doc ID: {r['doc_id']} | Status: {r['doc_status']}")

    return results


if __name__ == "__main__":
    asyncio.run(run_pipeline())
