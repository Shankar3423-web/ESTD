"""Extract and Persist Today's Regional (Telugu/Hindi/Indian) Entertainment Articles by Subcategory with Full Google Docs Generation.

Executes Steps 1 to 8 for all 8 canonical Entertainment subcategories:
1. Source Collection: Pull regional candidate items from curated Telugu, Hindi, and Indian RSS feeds + GNews (country='in').
2. Webpage Scraping & Body Extraction (Step 2)
3. Content Cleaning & Normalization (Step 3)
4. Duplicate Detection (Step 4)
5. Knowledge Source Persistence in PostgreSQL news_articles (Step 5)
6. MCP-First Retrieval & Eligibility Verification (Step 6)
7. Gemini AI Synthesis of Fact-Grounded Regional News (Step 7)
8. Google Docs Creation in Google Drive Category/Subcategory Folder (Step 8)
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

# Enable UTF-8 encoding on standard streams to safely log Telugu and Hindi scripts
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import httpx
from sqlalchemy import select

from backend.common.config.settings import get_settings
from backend.common.constants.categories import ESTDCategory
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.google_document_record import GoogleDocumentRecord
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
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


REGIONAL_ENTERTAINMENT_SUBCATEGORIES = [
    {
        "name": "Movies & Cinema",
        "code": "ENT_MOVIES",
        "preferred_sources": ["filmibeat_telugu", "oneindia_telugu", "filmibeat_hindi", "ndtv_movies", "indian_express_ent"],
        "search_query": '("tollywood" OR "bollywood" OR "telugu cinema" OR "hindi cinema" OR "box office") AND (movie OR film OR release)',
    },
    {
        "name": "TV & OTT",
        "code": "ENT_TV_OTT",
        "preferred_sources": ["filmibeat_telugu", "news18_ent", "indian_express_ent", "hindustan_times_ent"],
        "search_query": '(ott OR "web series" OR "bigg boss" OR "aha video" OR sonyliv OR jiohotstar OR "netflix india") AND (telugu OR hindi OR india)',
    },
    {
        "name": "Celebrities & Pop Culture",
        "code": "ENT_CELEBS",
        "preferred_sources": ["oneindia_hindi", "filmibeat_telugu", "news18_ent", "hindustan_times_ent"],
        "search_query": '(actor OR actress OR star OR celebrity) AND (tollywood OR bollywood OR telugu OR hindi)',
    },
    {
        "name": "Music",
        "code": "ENT_MUSIC",
        "preferred_sources": ["news18_ent", "indian_express_ent", "hindustan_times_ent"],
        "search_query": '(song OR "music director" OR singer OR thaman OR anirudh OR "a r rahman" OR "playback singer" OR "music video") AND (telugu OR hindi OR bollywood OR tollywood)',
    },
    {
        "name": "Gaming & Digital Entertainment",
        "code": "ENT_GAMING",
        "preferred_sources": ["news18_ent", "indian_express_ent"],
        "search_query": '(gaming OR esports OR bgmi OR "game developer" OR streamer) AND (india OR indian)',
    },
    {
        "name": "Awards & Events",
        "code": "ENT_AWARDS",
        "preferred_sources": ["ndtv_movies", "news18_ent", "indian_express_ent"],
        "search_query": '(awards OR siima OR filmfare OR "national film awards" OR "audio launch" OR "pre release event" OR "trailer launch") AND (telugu OR hindi OR india)',
    },
    {
        "name": "Creators & Influencers",
        "code": "ENT_CREATORS",
        "preferred_sources": ["news18_ent", "hindustan_times_ent", "indian_express_ent"],
        "search_query": '(youtuber OR influencer OR "content creator" OR streamer) AND (india OR telugu OR hindi)',
    },
    {
        "name": "Digital Storytelling & Culture",
        "code": "ENT_DIGITAL_CULTURE",
        "preferred_sources": ["news18_ent", "indian_express_ent"],
        "search_query": '(podcast OR "digital culture" OR webtoon OR animation OR anime OR viral) AND (india OR telugu OR hindi)',
    },
]


async def fetch_regional_candidates_for_subcategory(
    subcat_info: dict,
    rss_service: RSSCollectionService,
    gnews_adapter: GNewsAdapter,
) -> List[NewsItem]:
    """Gather candidate articles strictly from regional feeds and targeted Indian search."""
    subcat_name = subcat_info["name"]
    pref_source_ids = subcat_info.get("preferred_sources", [])
    search_query = subcat_info["search_query"]

    candidates: List[NewsItem] = []
    seen_urls = set()

    # 1. Pull from preferred regional RSS feeds first
    registry = get_source_registry()
    for src_id in pref_source_ids:
        src = registry.get_source_by_id(src_id)
        if not src or not src.enabled:
            continue
        try:
            items = await rss_service.collect_from_source(src, limit=8)
            for item in items:
                if item.url not in seen_urls:
                    item.subcategory = subcat_name
                    seen_urls.add(item.url)
                    candidates.append(item)
        except Exception as exc:
            logger.warning(f"Error fetching from regional RSS source {src_id}: {exc}")

    # 2. Query GNews targeting India ('country=in') with regional terms
    api_key = gnews_adapter._settings.get_gnews_api_key()
    if api_key and len(candidates) < 12:
        try:
            url = f"{gnews_adapter.BASE_URL}/search"
            params = {
                "q": search_query,
                "country": "in",
                "lang": "en",
                "apikey": api_key,
                "max": 6,
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
                                    source_name=(a.get("source") or {}).get("name") or "GNews India",
                                    source_type="gnews",
                                    category="Entertainment",
                                    subcategory=subcat_name,
                                    published_at=a.get("publishedAt"),
                                    image_url=a.get("image"),
                                )
                            )
                elif resp.status_code == 429:
                    logger.warning(f"GNews rate-limit (429) hit for subcategory {subcat_name}")
        except Exception as exc:
            logger.warning(f"GNews India query error for subcategory '{subcat_name}': {exc}")

    return candidates


async def process_subcategory_to_gdocs(
    subcat_info: dict,
    candidate_items: List[NewsItem],
    extraction_service: ExtractionService,
    cleaning_service: ContentCleaningService,
    knowledge_service: KnowledgeSourceService,
    mcp_gen_service: MCPGenerationService,
    step8_orchestrator: Step8Orchestrator,
) -> Optional[dict]:
    """Process candidate regional items until 1 article successfully traverses Steps 2-8."""
    subcat_name = subcat_info["name"]
    print(f"\n{'='*75}")
    print(f" PROCESSING REGIONAL SUBCATEGORY: [{subcat_name}] ({subcat_info['code']})")
    print(f"{'='*75}")
    print(f"  Candidate regional items found: {len(candidate_items)}")

    for idx, item in enumerate(candidate_items, start=1):
        clean_title = item.title.encode("ascii", errors="replace").decode("ascii")
        print(f"\n  [Candidate {idx}/{len(candidate_items)}] '{clean_title[:65]}...'")
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
            req = ArticleGenerationRequest(
                article_id=persisted.id,
                custom_instructions="Synthesize in fluent professional English suitable for national entertainment reporting while preserving all regional context, Telugu/Hindi names, movie titles, and verified facts."
            )
            gen_resp = mcp_gen_service.generate_from_mcp_article(req)
            if not gen_resp.success or not gen_resp.data:
                print(f"    [ERROR] Step 7 Gemini generation failed")
                continue
            generated_news = gen_resp.data
            gen_title_clean = generated_news.title.encode("ascii", errors="replace").decode("ascii")
            print(f"    [SUCCESS] Step 7 Generated: '{gen_title_clean[:65]}...' (Model: {gen_resp.model_used})")
        except Exception as e:
            print(f"    [ERROR] Step 7 Gemini generation error: {e}")
            continue

        # Step 8: Google Docs Creation in Google Drive Subcategory Folder
        print(f"    [Step 8] Creating formatted Google Doc in Google Drive...")
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
                        "generated_title": gen_title_clean,
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
    print("ESTD — EXTRACT & PROCESS 1 REGIONAL ARTICLE PER ENTERTAINMENT SUBCATEGORY")
    print(f"Current Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("Target Scope: Telugu, Hindi, Bollywood, Tollywood & Indian Entertainment")
    print("=" * 80)

    # Initialize services
    rss_service = RSSCollectionService()
    gnews_adapter = GNewsAdapter()
    extraction_service = ExtractionService()
    cleaning_service = ContentCleaningService()
    knowledge_service = KnowledgeSourceService()
    mcp_service = MCPService()
    mcp_gen_service = MCPGenerationService(mcp_service=mcp_service)
    step8_orchestrator = Step8Orchestrator()

    # Pre-initialize folder hierarchy in Google Drive
    print("\n[*] Initializing / Verifying Google Drive Folder Hierarchy...")
    step8_orchestrator.folder_resolver.initialize_hierarchy(force_refresh=False)
    print("    [PASS] Hierarchy verified.")

    results: List[dict] = []

    for subcat_info in REGIONAL_ENTERTAINMENT_SUBCATEGORIES:
        candidates = await fetch_regional_candidates_for_subcategory(
            subcat_info=subcat_info,
            rss_service=rss_service,
            gnews_adapter=gnews_adapter,
        )

        res = await process_subcategory_to_gdocs(
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

        # Brief sleep between subcategories to avoid external API rate spikes
        await asyncio.sleep(1.0)

    print("\n" + "=" * 80)
    print(f"REGIONAL EXECUTION COMPLETE: {len(results)}/{len(REGIONAL_ENTERTAINMENT_SUBCATEGORIES)} SUBCATEGORIES PROCESSED")
    print("=" * 80)
    for r in results:
        print(f"[{r['subcategory']}] (DB ID: {r['article_id']})")
        print(f"  Source: {r['source_name']}")
        print(f"  Title:  {r['generated_title']}")
        print(f"  GDoc:   {r['google_document_url']}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
