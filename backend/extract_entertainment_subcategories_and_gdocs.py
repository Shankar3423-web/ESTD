"""Extract and Persist Today's Entertainment Articles by Subcategory with Full Google Docs Generation.

Steps executed per subcategory:
1. Source Collection: Pull candidate items from today's curated RSS feeds and News APIs.
2. Webpage Scraping & Body Extraction (Step 2)
3. Content Cleaning & Normalization (Step 3)
4. Duplicate Detection (Step 4)
5. Knowledge Source Persistence in PostgreSQL news_articles (Step 5)
6. MCP-First Retrieval & Eligibility Verification (Step 6)
7. Gemini AI Synthesis of Fact-Grounded News (Step 7)
8. Google Docs Creation in Google Drive Category/Subcategory Folder (Step 8)
"""
import asyncio
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


ENTERTAINMENT_SUBCATEGORIES = [
    {"name": "Movies & Cinema", "code": "ENT_MOVIES", "search_query": "movies OR cinema OR film OR box office"},
    {"name": "TV & OTT", "code": "ENT_TV_OTT", "search_query": "tv series OR streaming OR netflix OR prime video OR ott"},
    {"name": "Celebrities & Pop Culture", "code": "ENT_CELEBS", "search_query": "celebrity OR pop culture OR hollywood OR star"},
    {"name": "Music", "code": "ENT_MUSIC", "search_query": "music OR album OR billboard OR song OR concert OR tour"},
    {"name": "Gaming & Digital Entertainment", "code": "ENT_GAMING", "search_query": "gaming OR video games OR nintendo OR playstation OR xbox OR esports"},
    {"name": "Awards & Events", "code": "ENT_AWARDS", "search_query": "awards OR film festival OR oscars OR emmy OR grammy OR red carpet"},
    {"name": "Creators & Influencers", "code": "ENT_CREATORS", "search_query": "creator OR influencer OR youtube OR streamer OR tiktok"},
    {"name": "Digital Storytelling & Culture", "code": "ENT_DIGITAL_CULTURE", "search_query": "digital culture OR podcast OR anime OR fandom OR webtoon"},
]


async def fetch_candidates_for_subcategory(
    subcat_name: str,
    search_query: str,
    rss_service: RSSCollectionService,
    gnews_adapter: GNewsAdapter,
    newsdata_adapter: NewsDataAdapter,
) -> List[NewsItem]:
    """Gather candidate articles from curated RSS feeds and external APIs for a subcategory."""
    candidates: List[NewsItem] = []
    seen_urls = set()

    # 1. Check curated RSS feeds matching this subcategory directly
    try:
        registry = get_source_registry()
        rss_sources = registry.get_sources_by_subcategory(subcat_name, enabled_only=True)
        for src in rss_sources:
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

    # 2. Query GNews for targeted subcategory news
    api_key = gnews_adapter._settings.get_gnews_api_key()
    if api_key:
        try:
            url = f"{gnews_adapter.BASE_URL}/top-headlines"
            params = {
                "category": "entertainment",
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
                                    category="Entertainment",
                                    subcategory=subcat_name,
                                    published_at=a.get("publishedAt"),
                                    image_url=a.get("image"),
                                )
                            )
        except Exception as exc:
            logger.warning(f"GNews query error for subcategory '{subcat_name}': {exc}")

    # 3. Fallback: Query NewsData if candidates are still low
    newsdata_key = newsdata_adapter._settings.get_newsdata_api_key()
    if len(candidates) < 2 and newsdata_key:
        try:
            url = newsdata_adapter.BASE_URL
            params = {
                "apikey": newsdata_key,
                "category": "entertainment",
                "q": search_query.split(" OR ")[0],
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
                                    category="Entertainment",
                                    subcategory=subcat_name,
                                    published_at=r.get("pubDate"),
                                    image_url=r.get("image_url"),
                                )
                            )
        except Exception as exc:
            logger.warning(f"NewsData query error for subcategory '{subcat_name}': {exc}")

    return candidates


async def process_subcategory_article(
    subcat_info: dict,
    candidate_items: List[NewsItem],
    extraction_service: ExtractionService,
    cleaning_service: ContentCleaningService,
    knowledge_service: KnowledgeSourceService,
    mcp_gen_service: MCPGenerationService,
    step8_orchestrator: Step8Orchestrator,
) -> Optional[dict]:
    """Process candidates until 1 article successfully traverses Steps 2-8."""
    subcat_name = subcat_info["name"]
    print(f"\n{'='*75}")
    print(f" PROCESSING SUBCATEGORY: [{subcat_name}] ({subcat_info['code']})")
    print(f"{'='*75}")
    print(f"  Candidate items found: {len(candidate_items)}")

    for idx, item in enumerate(candidate_items, start=1):
        clean_title = item.title.encode("ascii", errors="replace").decode("ascii")
        print(f"\n  [Candidate {idx}/{len(candidate_items)}] '{clean_title[:60]}...'")
        print(f"    Source: {item.source_name} ({item.source_type}) | Published: {item.published_at}")

        # Step 2: Extraction (force fetch to scrape full webpage body)
        try:
            extracted = await extraction_service.extract_article(item, force_fetch=True)
        except Exception as e:
            print(f"    [SKIP] Step 2 Extraction error: {e}")
            continue

        if (
            extracted.extraction_status == "EXTRACTION_FAILED"
            or not extracted.content
            or len(extracted.content.strip()) < 400
        ):
            print(f"    [SKIP] Insufficient body text extracted ({len(extracted.content or '')} chars < 400 min)")
            continue

        # Step 3: Cleaning
        cleaned = cleaning_service.clean_article(extracted)
        if (
            cleaned.cleaning_status != CleaningStatus.SUCCESS
            or not cleaned.cleaned_content
            or len(cleaned.cleaned_content.strip()) < 350
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
            print(f"    [SUCCESS] Step 7 Generated: '{generated_news.title[:65]}...' (Model: {gen_resp.model_used})")
        except Exception as e:
            print(f"    [ERROR] Step 7 Gemini generation error: {e}")
            continue

        # Step 8: Google Docs Creation in Google Drive Subcategory Folder
        print(f"    [Step 8] Creating Google Document in Google Drive...")
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
                    print(f"    [SUCCESS] Step 8 Google Document Created!")
                    print(f"      Document ID:  {doc_id}")
                    print(f"      Document URL: {doc_url}")
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
                    }
                else:
                    print(f"    [ERROR] Step 8 failed: {doc_resp.status}")
        except Exception as e:
            print(f"    [ERROR] Step 8 Google Drive creation error: {e}")
            continue

    print(f"  [WARNING] No article successfully completed for subcategory [{subcat_name}].")
    return None


async def main():
    print("=" * 80)
    print("ESTD — EXTRACT & PROCESS 1 ARTICLE PER ENTERTAINMENT SUBCATEGORY")
    print(f"Current Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
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

    # Pre-initialize folder hierarchy in Google Drive
    print("\n[*] Initializing / Verifying Google Drive Folder Hierarchy...")
    step8_orchestrator.folder_resolver.initialize_hierarchy(force_refresh=False)
    print("    [PASS] Root and Category folders verified.")

    results: List[dict] = []

    for subcat_info in ENTERTAINMENT_SUBCATEGORIES:
        candidates = await fetch_candidates_for_subcategory(
            subcat_name=subcat_info["name"],
            search_query=subcat_info["search_query"],
            rss_service=rss_service,
            gnews_adapter=gnews_adapter,
            newsdata_adapter=newsdata_adapter,
        )
        res = await process_subcategory_article(
            subcat_info=subcat_info,
            candidate_items=candidates,
            extraction_service=extraction_service,
            cleaning_service=cleaning_service,
            knowledge_service=knowledge_service,
            mcp_gen_service=mcp_gen_service,
            step8_orchestrator=step8_orchestrator,
        )
        if res:
            results.append(res)

    print("\n" + "=" * 80)
    print("FINAL EXECUTION SUMMARY — ENTERTAINMENT SUBCATEGORIES PROCESSED")
    print("=" * 80)
    print(f"Total Subcategories Attempted: {len(ENTERTAINMENT_SUBCATEGORIES)}")
    print(f"Total Successfully Completed:  {len(results)}/{len(ENTERTAINMENT_SUBCATEGORIES)}\n")

    for r in results:
        print(f"• Subcategory: [{r['subcategory']}] ({r['code']})")
        print(f"  Article ID:     {r['article_id']}")
        print(f"  Original Title: {r['article_title'][:70]}")
        print(f"  Source:         {r['source_name']} | Published: {r['published_at']}")
        print(f"  Doc Title:      {r['generated_title'][:70]}")
        print(f"  Google Doc ID:  {r['google_document_id']}")
        print(f"  Google Doc URL: {r['google_document_url']}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
