"""ESTD Tech News Category — Complete End-to-End Pipeline Ingestion & Verification.

Executes:
Step 1: Source Discovery & NewsItem
Step 2: Webpage Scraping & Extraction (Sufficiency Check)
Step 3: Content Cleaning & Normalization (Preserving code, versions, and Telugu Unicode)
Step 4: Deduplication (URL Normalization & SHA-256 Content Hashing)
Step 5: PostgreSQL Persistence & Read-back from news_articles
Step 6: Read-Only MCP Retrieval
Step 7: Gemini AI Factual Synthesis & Schema Validation
Step 8: Google Drive Google Docs Creation, Folder Placement & Live Read-back

Covers all 7 Canonical Tech Subcategories:
1. Artificial Intelligence (ID: 18, TECH_AI)
2. Software & Cloud (ID: 19, TECH_SOFTWARE_CLOUD)
3. Consumer Technology & Gadgets (ID: 20, TECH_CONSUMER_GADGETS)
4. Cybersecurity & Privacy (ID: 21, TECH_CYBERSECURITY)
5. Developer Technologies & Open Source (ID: 22, TECH_DEV_TOOLS)
6. Emerging Tech & Semiconductors (ID: 23, TECH_EMERGING_HARDWARE)
7. Digital Platforms & Big Tech (ID: 24, TECH_PLATFORMS)
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


TECH_ARTICLES_TO_INGEST: List[Dict[str, Any]] = [
    # 1. Artificial Intelligence (ID: 18) - International
    {
        "subcategory_name": "Artificial Intelligence",
        "subcategory_code": "TECH_AI",
        "expected_sub_id": 18,
        "scope": "international",
        "language": "en",
        "title": "Open models have real benefits. Do they outweigh the risks?",
        "url": "https://www.technologyreview.com/2026/10/13/1105432/open-models-have-real-benefits-do-they-outweigh-the-risks/",
        "source_name": "MIT Technology Review",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 12:00:00 GMT",
    },
    # 2. Artificial Intelligence (ID: 18) - National (India)
    {
        "subcategory_name": "Artificial Intelligence",
        "subcategory_code": "TECH_AI",
        "expected_sub_id": 18,
        "scope": "national",
        "language": "en",
        "title": "AI safety under scrutiny: Key incidents involving rogue agents",
        "url": "https://www.thehindu.com/sci-tech/technology/ai-safety-under-scrutiny-key-incidents-involving-rogue-agents/article71582869.ece",
        "source_name": "The Hindu",
        "source_type": "rss",
        "published_at": "Mon, 12 Oct 2026 15:30:00 GMT",
    },
    # 3. Software & Cloud (ID: 19) - International
    {
        "subcategory_name": "Software & Cloud",
        "subcategory_code": "TECH_SOFTWARE_CLOUD",
        "expected_sub_id": 19,
        "scope": "international",
        "language": "en",
        "title": "Microsoft: Recent Windows updates may trigger Remote Desktop connectivity disruptions",
        "url": "https://www.bleepingcomputer.com/news/microsoft/microsoft-recent-windows-updates-may-trigger-remote-desktop-issues/",
        "source_name": "BleepingComputer",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 14:15:00 GMT",
    },
    # 4. Consumer Technology & Gadgets (ID: 20) - National (India)
    {
        "subcategory_name": "Consumer Technology & Gadgets",
        "subcategory_code": "TECH_CONSUMER_GADGETS",
        "expected_sub_id": 20,
        "scope": "national",
        "language": "en",
        "title": "Nothing CMF debuts wireless speakers that look like milk cartons",
        "url": "https://indianexpress.com/article/technology/tech-news-technology/nothing-cmf-wireless-speakers-debut-10920785/",
        "source_name": "The Indian Express",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 11:00:00 GMT",
    },
    # 5. Consumer Technology & Gadgets (ID: 20) - Regional (India - Telugu Unicode)
    {
        "subcategory_name": "Consumer Technology & Gadgets",
        "subcategory_code": "TECH_CONSUMER_GADGETS",
        "expected_sub_id": 20,
        "scope": "regional",
        "language": "te",
        "title": "OnePlus 12: వన్ ప్లస్ 12 ఫీచర్స్ ఎలా ఉన్నాయంటే.!",
        "url": "https://telugu.oneindia.com/technology/what-are-the-features-of-oneplus-12-373215.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 10:30:00 GMT",
    },
    # 6. Cybersecurity & Privacy (ID: 21) - International
    {
        "subcategory_name": "Cybersecurity & Privacy",
        "subcategory_code": "TECH_CYBERSECURITY",
        "expected_sub_id": 21,
        "scope": "international",
        "language": "en",
        "title": "AI-Found Linux Kernel Flaw Gives Local Users Root, and Can Break a Guest Out to the Host",
        "url": "https://thehackernews.com/2026/10/ai-found-linux-kernel-flaw-gives-local.html",
        "source_name": "The Hacker News",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 09:00:00 GMT",
    },
    # 7. Cybersecurity & Privacy (ID: 21) - Regional (India - Telugu Unicode)
    {
        "subcategory_name": "Cybersecurity & Privacy",
        "subcategory_code": "TECH_CYBERSECURITY",
        "expected_sub_id": 21,
        "scope": "regional",
        "language": "te",
        "title": "WhatsApp: 69 లక్షల ఖాతాలను నిషేధించిన వాట్సాప్..",
        "url": "https://telugu.oneindia.com/technology/whatsapp-banned-69-lakh-accounts-in-december-2023-373781.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 08:30:00 GMT",
    },
    # 8. Developer Technologies & Open Source (ID: 22) - International
    {
        "subcategory_name": "Developer Technologies & Open Source",
        "subcategory_code": "TECH_DEV_TOOLS",
        "expected_sub_id": 22,
        "scope": "international",
        "language": "en",
        "title": "GitHub's model for secret detection: Finding more secrets with less noise",
        "url": "https://github.blog/ai-and-ml/githubs-model-for-secret-detection-finding-more-secrets-with-less-noise/",
        "source_name": "GitHub Blog",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 13:00:00 GMT",
    },
    # 9. Emerging Tech & Semiconductors (ID: 23) - International
    {
        "subcategory_name": "Emerging Tech & Semiconductors",
        "subcategory_code": "TECH_EMERGING_HARDWARE",
        "expected_sub_id": 23,
        "scope": "international",
        "language": "en",
        "title": "Nvidia GPU prices spike in Japan; prices up to 41% higher than Amazon US",
        "url": "https://www.tomshardware.com/pc-components/gpus/nvidia-gpu-prices-spike-in-japan-prices-up-to-41-percent-higher-than-amazon-us-rtx-5060-ti-sees-the-biggest-increase-among-the-rtx-50-series-stack",
        "source_name": "Tom's Hardware",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 15:00:00 GMT",
    },
    # 10. Emerging Tech & Semiconductors (ID: 23) - Regional (India - Telugu Unicode)
    {
        "subcategory_name": "Emerging Tech & Semiconductors",
        "subcategory_code": "TECH_EMERGING_HARDWARE",
        "expected_sub_id": 23,
        "scope": "regional",
        "language": "te",
        "title": "Betavolt: ఛార్జింగ్ లేకుండా 50 ఏళ్లు పనిచేయనున్న స్మార్ట్ ఫోన్లు.. అద్భుతాన్ని ఆవిష్కరించిన బీటావోల్ట్..!",
        "url": "https://telugu.oneindia.com/technology/chinese-startup-betavolt-has-announced-that-it-has-developed-a-battery-that-can-last-for-50-years-371897.html",
        "source_name": "Oneindia Telugu",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 07:45:00 GMT",
    },
    # 11. Digital Platforms & Big Tech (ID: 24) - International
    {
        "subcategory_name": "Digital Platforms & Big Tech",
        "subcategory_code": "TECH_PLATFORMS",
        "expected_sub_id": 24,
        "scope": "international",
        "language": "en",
        "title": "Justice Department says North Koreans have infiltrated dozens of U.S. companies",
        "url": "https://techcrunch.com/2026/10/13/justice-department-says-north-koreans-have-infiltrated-dozens-of-u-s-companies/",
        "source_name": "TechCrunch",
        "source_type": "rss",
        "published_at": "Mon, 12 Oct 2026 20:00:00 GMT",
    },
    # 12. Digital Platforms & Big Tech (ID: 24) - National (India)
    {
        "subcategory_name": "Digital Platforms & Big Tech",
        "subcategory_code": "TECH_PLATFORMS",
        "expected_sub_id": 24,
        "scope": "national",
        "language": "en",
        "title": "Bumble swipes right on $1.3 billion go-private deal amid online dating industry reset",
        "url": "https://indianexpress.com/article/technology/tech-news-technology/bumble-swipes-right-on-1-3-billion-go-private-deal-amid-online-dating-industry-reset-10920777/",
        "source_name": "The Indian Express",
        "source_type": "rss",
        "published_at": "Tue, 13 Oct 2026 10:15:00 GMT",
    },
]


async def run_pipeline():
    print("=" * 80)
    print("ESTD TECH CATEGORY — FULL PIPELINE INGESTION & DOCUMENT CREATION")
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

    for idx, target in enumerate(TECH_ARTICLES_TO_INGEST, start=1):
        sub_name = target["subcategory_name"]
        print(f"\n[{idx}/{len(TECH_ARTICLES_TO_INGEST)}] Processing: {sub_name} (ID: {target['expected_sub_id']})")
        print(f"  Source: {target['source_name']} | Scope: {target['scope']} | Lang: {target['language']}")
        print(f"  URL: {target['url']}")

        # STEP 1: NewsItem
        item = NewsItem(
            title=target["title"],
            url=target["url"],
            source_name=target["source_name"],
            source_type=target["source_type"],
            category="Tech",
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
    print("PIPELINE EXECUTION SUMMARY ACROSS ALL 7 CANONICAL TECH SUBCATEGORIES")
    print("=" * 80)
    print(f"Total Successfully Completed: {len(results)}/{len(TECH_ARTICLES_TO_INGEST)}")
    for r in results:
        print(f" - [{r['subcategory']} (ID {r['sub_id']})] Art ID {r['article_id']} | Doc ID: {r['doc_id']} | Status: {r['doc_status']}")

    return results


if __name__ == "__main__":
    asyncio.run(run_pipeline())
