"""ESTD Business & Finance Category — Complete End-to-End Pipeline Ingestion & Verification.

Executes:
Step 1: Source Discovery & NewsItem
Step 2: Webpage Scraping & Extraction (Sufficiency Check)
Step 3: Content Cleaning & Normalization (Preserving ₹, $, %, balance sheet terms, Telugu Unicode)
Step 4: Deduplication (URL Normalization & SHA-256 Content Hashing)
Step 5: PostgreSQL Persistence & Read-back from news_articles
Step 6: Read-Only MCP Retrieval
Step 7: Gemini AI Factual Synthesis & Schema Validation
Step 8: Google Drive Google Docs Creation, Folder Placement & Live Read-back

Covers all 6 Canonical Business & Finance Subcategories across International, National, and Regional scopes:
1. Financial Markets & Banking (ID: 32, BIZ_MARKETS)
2. Startups & Venture Capital (ID: 33, BIZ_STARTUPS)
3. Corporate Strategy & Earnings (ID: 34, BIZ_CORP_STRATEGY)
4. Personal Finance & Wealth Management (ID: 35, BIZ_PERSONAL_FINANCE)
5. Economy & Macroeconomics (ID: 36, BIZ_MACROECONOMY)
6. Trade, Supply Chain & Industry (ID: 37, BIZ_TRADE_INDUSTRY)
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

sys.stdout.reconfigure(encoding="utf-8")

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


BUSINESS_FINANCE_ARTICLES_TO_INGEST: List[Dict[str, Any]] = [
    # 1. Economy & Macroeconomics (ID: 36) - National (India)
    {
        "subcategory_name": "Economy & Macroeconomics",
        "subcategory_code": "BIZ_MACROECONOMY",
        "expected_sub_id": 36,
        "scope": "national",
        "language": "en",
        "title": "IMF backs India's updated GDP methodology, calls revision step in right direction",
        "url": "https://www.thehindu.com/business/imf-hails-indias-updated-gdp-methodology/article71586923.ece",
        "source_name": "The Hindu - Business",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 12:00:00 +0530",
    },
    # 2. Economy & Macroeconomics (ID: 36) - International
    {
        "subcategory_name": "Economy & Macroeconomics",
        "subcategory_code": "BIZ_MACROECONOMY",
        "expected_sub_id": 36,
        "scope": "international",
        "language": "en",
        "title": "Tech stock sell-off intensifies as markets fret about UK GDP economy and IMF outlook",
        "url": "https://www.theguardian.com/business/live/2026/oct/15/tech-stock-sell-off-markets-uk-gdp-economy-august-imf-latest-news-updates",
        "source_name": "The Guardian - Business",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 09:30:00 +0000",
    },
    # 3. Financial Markets & Banking (ID: 32) - National (India)
    {
        "subcategory_name": "Financial Markets & Banking",
        "subcategory_code": "BIZ_MARKETS",
        "expected_sub_id": 32,
        "scope": "national",
        "language": "en",
        "title": "Centre to keep pushing disinvestments despite meeting target with IDBI Bank deal",
        "url": "https://indianexpress.com/article/business/centre-disinvestments-meeting-target-idbi-bank-deal-10922529/",
        "source_name": "The Indian Express - Business",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 07:00:00 +0000",
    },
    # 4. Financial Markets & Banking (ID: 32) - Regional (Telugu Unicode)
    {
        "subcategory_name": "Financial Markets & Banking",
        "subcategory_code": "BIZ_MARKETS",
        "expected_sub_id": 32,
        "scope": "regional",
        "language": "te",
        "title": "రూ.6.99 లక్షలకే.. 2026 టయోటా గ్లాంజా!",
        "url": "https://www.sakshi.com/telugu-news/business/2026-toyota-glanza-facelift-launched-india-rs-6-99-lakh-2932520",
        "source_name": "Sakshi - Business",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 10:49:09 +0530",
    },
    # 5. Startups & Venture Capital (ID: 33) - National (India)
    {
        "subcategory_name": "Startups & Venture Capital",
        "subcategory_code": "BIZ_STARTUPS",
        "expected_sub_id": 33,
        "scope": "national",
        "language": "en",
        "title": "Shamrock AI Bags $5 Mn To Help Enterprises Deploy AI Agents Reliably",
        "url": "https://inc42.com/buzz/shamrock-ai-bags-5-mn-to-help-enterprises-deploy-ai-agents-reliably/",
        "source_name": "Inc42",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 05:54:36 +0000",
    },
    # 6. Corporate Strategy & Earnings (ID: 34) - National (India)
    {
        "subcategory_name": "Corporate Strategy & Earnings",
        "subcategory_code": "BIZ_CORP_STRATEGY",
        "expected_sub_id": 34,
        "scope": "national",
        "language": "en",
        "title": "Kumar Mangalam Birla plans $30 billion push undeterred by crises",
        "url": "https://economictimes.indiatimes.com/news/company/corporate-trends/kumar-mangalam-birla-plans-30-billion-push-undeterred-by-crises/articleshow/134944242.cms",
        "source_name": "Economic Times - Companies",
        "source_type": "rss",
        "published_at": "Wed, 14 Oct 2026 19:21:20 +0530",
    },
    # 7. Personal Finance & Wealth Management (ID: 35) - National (India)
    {
        "subcategory_name": "Personal Finance & Wealth Management",
        "subcategory_code": "BIZ_PERSONAL_FINANCE",
        "expected_sub_id": 35,
        "scope": "national",
        "language": "en",
        "title": "Gold, silver recover after crash: What drove the fall, why prices recovered and what you should watch next",
        "url": "https://www.livemint.com/money/personal-finance/gold-silver-recover-after-crash-what-drove-the-fall-why-prices-recovered-and-what-you-should-watch-next-explained-11792042062780.html",
        "source_name": "LiveMint - Money",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 12:28:54 +0530",
    },
    # 8. Trade, Supply Chain & Industry (ID: 37) - National (India)
    {
        "subcategory_name": "Trade, Supply Chain & Industry",
        "subcategory_code": "BIZ_TRADE_INDUSTRY",
        "expected_sub_id": 37,
        "scope": "national",
        "language": "en",
        "title": "boAt enters Sri Lanka, Bhutan; says international revenue more than doubled in FY26",
        "url": "https://economictimes.indiatimes.com/industry/cons-products/electronics/boat-enters-sri-lanka-bhutan-says-international-revenue-more-than-doubled-in-fy26/articleshow/134959219.cms",
        "source_name": "Economic Times - Industry",
        "source_type": "rss",
        "published_at": "Thu, 15 Oct 2026 11:47:39 +0530",
    },
]


async def run_pipeline():
    print("=" * 80)
    print("ESTD BUSINESS & FINANCE CATEGORY — FULL PIPELINE INGESTION & DOCUMENT CREATION")
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

    for idx, target in enumerate(BUSINESS_FINANCE_ARTICLES_TO_INGEST, start=1):
        sub_name = target["subcategory_name"]
        print(f"\n[{idx}/{len(BUSINESS_FINANCE_ARTICLES_TO_INGEST)}] Processing: {sub_name} (ID: {target['expected_sub_id']})")
        print(f"  Source: {target['source_name']} | Scope: {target['scope']} | Lang: {target['language']}")
        print(f"  URL: {target['url']}")

        # STEP 1: NewsItem
        item = NewsItem(
            title=target["title"],
            url=target["url"],
            source_name=target["source_name"],
            source_type=target["source_type"],
            category="Business & Finance",
            subcategory=sub_name,
            published_at=target["published_at"],
            language=target["language"],
            region="IN" if target["scope"] in ("national", "regional") else "GB",
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
    print("PIPELINE EXECUTION SUMMARY ACROSS ALL 6 CANONICAL BUSINESS & FINANCE SUBCATEGORIES")
    print("=" * 80)
    print(f"Total Successfully Completed: {len(results)}/{len(BUSINESS_FINANCE_ARTICLES_TO_INGEST)}")
    for r in results:
        print(f" - [{r['subcategory']} (ID {r['sub_id']})] Art ID {r['article_id']} | Doc ID: {r['doc_id']} | Status: {r['doc_status']}")

    return results


if __name__ == "__main__":
    asyncio.run(run_pipeline())
