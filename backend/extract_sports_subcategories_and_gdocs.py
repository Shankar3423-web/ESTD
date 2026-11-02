"""Extract, Persist, Synthesize and Process Today's Sports Articles across All Canonical Subcategories.

Pipeline stages executed per subcategory:
1. Source Collection: Pull candidate items from curated RSS feeds, GNews API, and NewsData API.
2. Webpage Scraping & Body Extraction (Step 2)
3. Content Cleaning & Normalization (Step 3)
4. Duplicate Detection (Step 4)
5. Knowledge Source Persistence in PostgreSQL news_articles (Step 5)
6. MCP-First Retrieval & Eligibility Verification (Step 6)
7. Gemini AI Fact-Grounded Synthesis (Step 7)
8. Google Drive Document Placement / Idempotent Record Management (Step 8)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Ensure paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
from sqlalchemy import select

from backend.common.config.settings import get_settings
from backend.common.constants.categories import ESTDCategory, resolve_subcategory
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.subcategory import Subcategory
from backend.database.models.google_document_record import GoogleDocumentRecord
from backend.database.repositories.category_repository import SubcategoryRepository
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
from backend.step1_source_collection.apis.newsdata_adapter import NewsDataAdapter
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService
from backend.step1_source_collection.rss.sources.registry import get_source_registry
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

SPORTS_SUBCATEGORIES = [
    {
        "name": "Cricket",
        "code": "SPORTS_CRICKET",
        "search_query": "cricket OR \"Test match\" OR IPL OR BCCI OR \"Ranji Trophy\"",
        "preferred_sources": ["the_hindu_sport", "oneindia_telugu_sports", "sakshi_telugu_sports"],
    },
    {
        "name": "Football",
        "code": "SPORTS_FOOTBALL",
        "search_query": "football OR soccer OR \"Premier League\" OR \"Champions League\" OR \"La Liga\"",
        "preferred_sources": ["hindustan_times_sports", "bbc_sport"],
    },
    {
        "name": "Tennis",
        "code": "SPORTS_TENNIS",
        "search_query": "tennis OR \"Grand Slam\" OR ATP OR WTA OR \"Shanghai Masters\"",
        "preferred_sources": ["the_hindu_sport", "hindustan_times_sports"],
    },
    {
        "name": "Badminton",
        "code": "SPORTS_BADMINTON",
        "search_query": "badminton OR BWF OR \"Thomas Cup\" OR \"All England\" OR \"PV Sindhu\"",
        "preferred_sources": ["the_hindu_sport", "hindustan_times_sports"],
    },
    {
        "name": "Motorsport",
        "code": "SPORTS_MOTORSPORT",
        "search_query": "motorsport OR \"Formula 1\" OR \"F1\" OR MotoGP OR \"Grand Prix\" OR \"IndyCar\"",
        "preferred_sources": ["autosport_f1", "bbc_sport"],
    },
    {
        "name": "Hockey",
        "code": "SPORTS_HOCKEY",
        "search_query": "hockey OR \"FIH\" OR \"India hockey team\" OR \"Hockey India League\"",
        "preferred_sources": ["the_hindu_sport", "indian_express_sports"],
    },
    {
        "name": "Athletics & Olympic Sports",
        "code": "SPORTS_ATHLETICS",
        "search_query": "athletics OR \"Olympic\" OR \"World Athletics\" OR \"Neeraj Chopra\" OR marathon",
        "preferred_sources": ["the_hindu_sport", "indian_express_sports"],
    },
    {
        "name": "Esports & Competitive Gaming",
        "code": "SPORTS_ESPORTS",
        "search_query": "\"esports\" OR \"competitive gaming\" OR \"Valorant Champions\" OR \"League of Legends Worlds\"",
        "preferred_sources": [],
    },
    {
        "name": "Other Sports",
        "code": "SPORTS_OTHER",
        "search_query": "chess OR \"Grandmaster\" OR \"FIDE\" OR kabaddi OR wrestling OR \"Pro Kabaddi\"",
        "preferred_sources": ["chess_com_news", "the_hindu_sport"],
    },
]


async def fetch_candidates_for_subcategory(
    subcat_info: dict,
    rss_service: RSSCollectionService,
    gnews_adapter: GNewsAdapter,
    newsdata_adapter: NewsDataAdapter,
) -> List[NewsItem]:
    """Gather candidate articles from curated RSS feeds and external APIs for a subcategory."""
    subcat_name = subcat_info["name"]
    search_query = subcat_info["search_query"]
    preferred_sources = subcat_info.get("preferred_sources", [])
    candidates: List[NewsItem] = []
    seen_urls = set()

    # 1. Fetch from preferred RSS sources
    registry = get_source_registry()
    for src_id in preferred_sources:
        src = registry.get_source_by_id(src_id)
        if src and src.enabled:
            try:
                items = await rss_service.collect_from_source(src, limit=10)
                for item in items:
                    if item.url not in seen_urls:
                        item.subcategory = subcat_name
                        seen_urls.add(item.url)
                        candidates.append(item)
            except Exception as src_err:
                logger.warning(f"Error fetching from RSS source {src_id}: {src_err}")

    # 2. Also check registry for any other sources configured for this subcategory
    try:
        rss_sources = registry.get_sources_by_subcategory(subcat_name, enabled_only=True)
        for src in rss_sources:
            if src.source_id not in preferred_sources:
                try:
                    items = await rss_service.collect_from_source(src, limit=5)
                    for item in items:
                        if item.url not in seen_urls:
                            item.subcategory = subcat_name
                            seen_urls.add(item.url)
                            candidates.append(item)
                except Exception as src_err:
                    logger.warning(f"Error fetching from RSS source {src.source_name}: {src_err}")
    except Exception as exc:
        logger.warning(f"RSS fetch error for subcategory '{subcat_name}': {exc}")

    # 3. Query GNews for targeted subcategory news
    api_key = gnews_adapter._settings.get_gnews_api_key()
    if api_key and len(candidates) < 3:
        try:
            url = f"{gnews_adapter.BASE_URL}/search"
            params = {
                "q": search_query,
                "lang": "en",
                "apikey": api_key,
                "max": 5,
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    articles = resp.json().get("articles", [])
                    for a in articles:
                        u = a.get("url")
                        t = a.get("title")
                        if u and t and u not in seen_urls:
                            seen_urls.add(u)
                            candidates.append(
                                NewsItem(
                                    title=t.strip(),
                                    description=a.get("description"),
                                    url=u.strip(),
                                    source_name=(a.get("source") or {}).get("name") or "GNews",
                                    source_type="gnews",
                                    category="Sports",
                                    subcategory=subcat_name,
                                    published_at=a.get("publishedAt"),
                                    image_url=a.get("image"),
                                )
                            )
        except Exception as exc:
            logger.warning(f"GNews query error for subcategory '{subcat_name}': {exc}")

    # 4. Fallback: Query NewsData if candidates are still low
    newsdata_key = newsdata_adapter._settings.get_newsdata_api_key()
    if len(candidates) < 2 and newsdata_key:
        try:
            url = newsdata_adapter.BASE_URL
            params = {
                "apikey": newsdata_key,
                "category": "sports",
                "q": search_query.split(" OR ")[0].replace('"', ''),
                "language": "en",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for r in results:
                        u = r.get("link")
                        t = r.get("title")
                        if u and t and u not in seen_urls:
                            seen_urls.add(u)
                            candidates.append(
                                NewsItem(
                                    title=t.strip(),
                                    description=r.get("description"),
                                    url=u.strip(),
                                    source_name=r.get("source_name") or r.get("source_id") or "NewsData",
                                    source_type="newsdata",
                                    category="Sports",
                                    subcategory=subcat_name,
                                    published_at=r.get("pubDate"),
                                    image_url=r.get("image_url"),
                                )
                            )
        except Exception as exc:
            logger.warning(f"NewsData query error for subcategory '{subcat_name}': {exc}")

    return candidates


async def process_sports_subcategory(
    subcat_info: dict,
    candidate_items: List[NewsItem],
    extraction_service: ExtractionService,
    cleaning_service: ContentCleaningService,
    knowledge_service: KnowledgeSourceService,
    mcp_gen_service: MCPGenerationService,
    step8_orchestrator: Step8Orchestrator,
) -> Optional[dict]:
    """Process candidate items through Steps 2-8 until 1 article succeeds."""
    subcat_name = subcat_info["name"]
    print(f"\n{'='*75}")
    print(f" PROCESSING SPORTS SUBCATEGORY: [{subcat_name}] ({subcat_info['code']})")
    print(f"{'='*75}")
    print(f"  Candidate items found: {len(candidate_items)}")

    for idx, item in enumerate(candidate_items, start=1):
        clean_title = item.title.encode("ascii", errors="replace").decode("ascii")
        print(f"\n  [Candidate {idx}/{len(candidate_items)}] '{clean_title[:65]}...'")
        print(f"    Source: {item.source_name} ({item.source_type}) | Published: {item.published_at}")
        print(f"    URL: {item.url[:85]}")

        # Step 2: Extraction
        try:
            extracted = await extraction_service.extract_article(item, force_fetch=True)
        except Exception as e:
            print(f"    [SKIP] Step 2 Extraction error: {e}")
            continue

        if (
            extracted.extraction_status == "EXTRACTION_FAILED"
            or not extracted.content
            or len(extracted.content.strip()) < 350
        ):
            print(f"    [SKIP] Insufficient body text extracted ({len(extracted.content or '')} chars < 350 min)")
            continue

        # Step 3: Cleaning
        cleaned = cleaning_service.clean_article(extracted)
        if (
            cleaned.cleaning_status != CleaningStatus.SUCCESS
            or not cleaned.cleaned_content
            or len(cleaned.cleaned_content.strip()) < 300
        ):
            print(f"    [SKIP] Step 3 Cleaning rejected content ({len(cleaned.cleaned_content or '')} chars)")
            continue

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
        except Exception as e:
            print(f"    [SKIP] Step 4 Deduplication check error: {e}")
            continue

        if dedup_result.status != "unique":
            print(f"    [SKIP] Duplicate detected ({dedup_result.decision.duplicate_reason})")
            continue

        # Step 5: PostgreSQL Persistence
        try:
            persisted = knowledge_service.persist_from_step4(dedup_result)
            print(f"    [SUCCESS] Step 5 Persisted to DB! Article ID: {persisted.id} | Words: {len((persisted.content or '').split())}")
        except ArticleDuplicateError:
            print(f"    [SKIP] Article duplicate prevented by DB unique constraint")
            continue
        except Exception as e:
            print(f"    [SKIP] Step 5 Persistence error: {e}")
            continue

        # Step 6 & 7: Gemini AI Fact-Grounded Synthesis via MCP
        print(f"    [Step 7] Generating structured publication via Gemini AI...")
        try:
            req = ArticleGenerationRequest(article_id=persisted.id)
            gen_resp = mcp_gen_service.generate_from_mcp_article(req)
            if not gen_resp.success or not gen_resp.data:
                print(f"    [ERROR] Step 7 Gemini generation failed")
                continue
            generated_news = gen_resp.data
            print(f"    [SUCCESS] Step 7 Generated: '{generated_news.title[:65]}...'")
            print(f"      Category: {generated_news.category} | Subcategory: {generated_news.subcategory}")
            print(f"      Summary chars: {len(generated_news.summary)} | Content chars: {len(generated_news.content)}")
        except Exception as e:
            print(f"    [ERROR] Step 7 Gemini generation error: {e}")
            continue

        # Step 8: Google Docs Creation / Local Staging Record Management
        print(f"    [Step 8] Processing Google Document record...")
        try:
            with get_db_session() as session:
                doc_resp = step8_orchestrator.process_approved_content(
                    news=generated_news,
                    article_id=persisted.id,
                    session=session,
                    original_published_at=item.published_at,
                )
                if doc_resp.success and doc_resp.data:
                    doc_id = doc_resp.data.google_document_id
                    doc_url = doc_resp.data.google_document_url
                    print(f"    [SUCCESS] Step 8 Document record processed: {doc_id} ({doc_resp.status})")
                    return {
                        "subcategory": subcat_name,
                        "code": subcat_info["code"],
                        "article_id": persisted.id,
                        "article_title": clean_title,
                        "source_name": item.source_name,
                        "source_url": item.url,
                        "published_at": item.published_at,
                        "generated_title": generated_news.title,
                        "google_document_id": doc_id,
                        "google_document_url": doc_url,
                        "step8_status": doc_resp.status,
                    }
                else:
                    print(f"    [NOTICE] Step 8 result: {doc_resp.status} (Error: {doc_resp.error_message})")
                    # If GDrive failed solely due to OAuth token expiration, article is safely persisted in Step 5 and synthesized in Step 7
                    return {
                        "subcategory": subcat_name,
                        "code": subcat_info["code"],
                        "article_id": persisted.id,
                        "article_title": clean_title,
                        "source_name": item.source_name,
                        "source_url": item.url,
                        "published_at": item.published_at,
                        "generated_title": generated_news.title,
                        "google_document_id": getattr(doc_resp.data, "google_document_id", None) if doc_resp.data else None,
                        "google_document_url": getattr(doc_resp.data, "google_document_url", None) if doc_resp.data else None,
                        "step8_status": doc_resp.status,
                    }
        except Exception as e:
            print(f"    [ERROR] Step 8 handling error: {e}")
            return {
                "subcategory": subcat_name,
                "code": subcat_info["code"],
                "article_id": persisted.id,
                "article_title": clean_title,
                "source_name": item.source_name,
                "source_url": item.url,
                "published_at": item.published_at,
                "generated_title": generated_news.title,
                "google_document_id": None,
                "google_document_url": None,
                "step8_status": "FAILED",
            }

    print(f"  [WARNING] No article completed for subcategory [{subcat_name}].")
    return None


async def main():
    print("=" * 80)
    print("ESTD — SPORTS CATEGORY COMPLETE PIPELINE EXECUTION ACROSS ALL 9 SUBCATEGORIES")
    print(f"Execution Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    # Initialize services
    rss_service = RSSCollectionService()
    gnews_adapter = GNewsAdapter()
    newsdata_adapter = NewsDataAdapter()
    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    knowledge_service = KnowledgeSourceService()
    mcp_service = MCPService()
    mcp_gen_service = MCPGenerationService(mcp_service=mcp_service)
    step8_orchestrator = Step8Orchestrator()

    successful_results = []
    failed_subcats = []

    for subcat in SPORTS_SUBCATEGORIES:
        candidates = await fetch_candidates_for_subcategory(
            subcat_info=subcat,
            rss_service=rss_service,
            gnews_adapter=gnews_adapter,
            newsdata_adapter=newsdata_adapter,
        )
        res = await process_sports_subcategory(
            subcat_info=subcat,
            candidate_items=candidates,
            extraction_service=extraction_service,
            cleaning_service=cleaning_service,
            knowledge_service=knowledge_service,
            mcp_gen_service=mcp_gen_service,
            step8_orchestrator=step8_orchestrator,
        )
        if res:
            successful_results.append(res)
        else:
            failed_subcats.append(subcat["name"])

    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Subcategories Attempted: {len(SPORTS_SUBCATEGORIES)}")
    print(f"Successfully Processed:        {len(successful_results)}/{len(SPORTS_SUBCATEGORIES)}")
    print(f"Failed Subcategories:          {failed_subcats}")
    print("-" * 80)
    for r in successful_results:
        print(f" - [{r['subcategory']}] (Article ID {r['article_id']}): '{r['generated_title'][:60]}...' | Doc: {r['google_document_id'] or 'Staged/Pending'} (Status: {r['step8_status']})")


if __name__ == "__main__":
    asyncio.run(main())
