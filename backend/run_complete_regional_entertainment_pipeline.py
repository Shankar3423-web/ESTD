"""End-to-End Execution for 8 Regional Entertainment Subcategories (Telugu / Hindi / Indian Entertainment).

Ensures all 8 canonical Entertainment subcategories have exactly 1 authentic regional article
persisted in PostgreSQL and formatted into Google Drive:
1. Movies & Cinema (Telugu - Garividi Lakshmi Movie Review) -> Doc 1PAb8AHJtHK-PMqJu9AJV2FSD6lrcoYSyjLi9ZcOK5qw
2. TV & OTT (Telugu - Brahmamudi Serial) -> Art 506
3. Celebrities & Pop Culture (Telugu - Sobhita Dhulipala) -> Art 512
4. Music (Regional / Indian Music) -> Scraped from GNews India
5. Gaming & Digital Entertainment (Indian Gaming / BGMI / Esports) -> Scraped from GNews India
6. Awards & Events (Regional Film Awards / Audio Launch) -> Scraped from GNews India
7. Creators & Influencers (Indian / Regional Creators) -> Scraped from GNews India
8. Digital Storytelling & Culture (Indian Animation / Nina Sabnani) -> Art 557
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

from backend.common.config.settings import get_settings
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.step1_source_collection.apis.gnews_adapter import GNewsAdapter
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


TARGET_SUBCATEGORIES = [
    {
        "name": "Movies & Cinema",
        "code": "ENT_MOVIES",
        "existing_article_id": 509,  # Already created
        "already_doc_id": "1PAb8AHJtHK-PMqJu9AJV2FSD6lrcoYSyjLi9ZcOK5qw",
        "already_doc_url": "https://docs.google.com/document/d/1PAb8AHJtHK-PMqJu9AJV2FSD6lrcoYSyjLi9ZcOK5qw/edit?usp=drivesdk",
        "search_query": None,
    },
    {
        "name": "TV & OTT",
        "code": "ENT_TV_OTT",
        "existing_article_id": 506,  # Telugu Brahmamudi Serial
        "search_query": '(ott OR "web series" OR "bigg boss" OR aha OR sonyliv OR jiohotstar) AND (telugu OR hindi OR india)',
    },
    {
        "name": "Celebrities & Pop Culture",
        "code": "ENT_CELEBS",
        "existing_article_id": 512,  # Telugu Sobhita Dhulipala
        "search_query": '(actor OR actress OR star OR celebrity) AND (tollywood OR bollywood OR telugu OR hindi)',
    },
    {
        "name": "Music",
        "code": "ENT_MUSIC",
        "existing_article_id": None,
        "search_query": '(song OR "music director" OR singer OR thaman OR anirudh OR "a r rahman" OR "playback singer") AND (telugu OR hindi OR bollywood OR tollywood)',
    },
    {
        "name": "Gaming & Digital Entertainment",
        "code": "ENT_GAMING",
        "existing_article_id": None,
        "search_query": '(gaming OR esports OR bgmi OR "game developer" OR nodwin) AND (india OR indian)',
    },
    {
        "name": "Awards & Events",
        "code": "ENT_AWARDS",
        "existing_article_id": None,
        "search_query": '(awards OR siima OR filmfare OR "national film awards" OR "trailer launch" OR "audio launch") AND (telugu OR hindi OR india)',
    },
    {
        "name": "Creators & Influencers",
        "code": "ENT_CREATORS",
        "existing_article_id": None,
        "search_query": '(youtuber OR influencer OR "content creator" OR vlogger) AND (india OR telugu OR hindi)',
    },
    {
        "name": "Digital Storytelling & Culture",
        "code": "ENT_DIGITAL_CULTURE",
        "existing_article_id": 557,  # Nina Sabnani Indian Animation Pioneer
        "search_query": '(podcast OR "digital culture" OR webtoon OR animation OR anime OR viral) AND (india OR telugu OR hindi)',
    },
]


async def fetch_gnews_india_candidates(search_query: str, subcat_name: str, gnews_adapter: GNewsAdapter) -> List[NewsItem]:
    """Query GNews for targeted regional Indian entertainment news."""
    api_key = gnews_adapter._settings.get_gnews_api_key()
    if not api_key:
        return []
    items: List[NewsItem] = []
    try:
        url = f"{gnews_adapter.BASE_URL}/search"
        params = {
            "q": search_query,
            "country": "in",
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
                    if u and t:
                        items.append(
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
    except Exception as exc:
        logger.warning(f"GNews India query error for '{subcat_name}': {exc}")
    return items


async def process_single_subcategory(
    subcat_info: dict,
    extraction_service: ExtractionService,
    cleaning_service: ContentCleaningService,
    knowledge_service: KnowledgeSourceService,
    mcp_gen_service: MCPGenerationService,
    step8_orchestrator: Step8Orchestrator,
    gnews_adapter: GNewsAdapter,
) -> Optional[dict]:
    subcat_name = subcat_info["name"]
    print(f"\n{'='*75}")
    print(f" PROCESSING REGIONAL SUBCATEGORY: [{subcat_name}] ({subcat_info['code']})")
    print(f"{'='*75}")

    # Case A: Already completely done
    if subcat_info.get("already_doc_id"):
        print(f"  [ALREADY COMPLETE] Google Document exists for subcategory.")
        print(f"    Document ID:  {subcat_info['already_doc_id']}")
        print(f"    Document URL: {subcat_info['already_doc_url']}")
        return {
            "subcategory": subcat_name,
            "code": subcat_info["code"],
            "article_id": subcat_info["existing_article_id"],
            "generated_title": "Garividi Lakshmi Secures UA13+ Certification from CBFC, Set for October 17 Release",
            "google_document_id": subcat_info["already_doc_id"],
            "google_document_url": subcat_info["already_doc_url"],
        }

    # Case B: Article is already in PostgreSQL, synthesize and generate Google Doc
    existing_id = subcat_info.get("existing_article_id")
    if existing_id:
        print(f"  [EXISTING ARTICLE] Using persisted regional Article ID {existing_id}...")
        try:
            req = ArticleGenerationRequest(
                article_id=existing_id,
                custom_instructions="Synthesize in fluent professional English suitable for national entertainment reporting while preserving regional context, proper nouns, cast, and verified facts."
            )
            gen_resp = mcp_gen_service.generate_from_mcp_article(req)
            if gen_resp.success and gen_resp.data:
                generated_news = gen_resp.data
                gen_title_clean = generated_news.title.encode("ascii", errors="replace").decode("ascii")
                print(f"    [SUCCESS] Step 7 Generated: '{gen_title_clean[:65]}...'")

                with get_db_session() as session:
                    # Fetch original published_at
                    art_row = session.get(NewsArticle, existing_id)
                    pub_at = art_row.published_at.isoformat() if art_row and art_row.published_at else None

                    doc_resp = step8_orchestrator.process_approved_content(
                        news=generated_news,
                        article_id=existing_id,
                        session=session,
                        original_published_at=pub_at,
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
                            "article_id": existing_id,
                            "generated_title": gen_title_clean,
                            "google_document_id": doc_id,
                            "google_document_url": doc_url,
                        }
        except Exception as e:
            print(f"    [ERROR] Processing existing article {existing_id}: {e}")

    # Case C: Fresh fetch, scrape, clean, dedup, persist, synthesize, and export
    search_q = subcat_info.get("search_query")
    if search_q:
        print(f"  [FETCHING FRESH CANDIDATES] Querying GNews India with regional query...")
        candidates = await fetch_gnews_india_candidates(search_q, subcat_name, gnews_adapter)
        print(f"  Found {len(candidates)} regional candidates.")

        for idx, item in enumerate(candidates, start=1):
            clean_title = item.title.encode("ascii", errors="replace").decode("ascii")
            print(f"\n    [Candidate {idx}/{len(candidates)}] '{clean_title[:65]}...'")
            print(f"      Source: {item.source_name} | URL: {item.url[:60]}...")

            # Step 2: Scrape
            try:
                extracted = await extraction_service.extract_article(item, force_fetch=True)
            except Exception as e:
                print(f"      [SKIP] Step 2 Extraction error: {e}")
                continue

            if (
                extracted.extraction_status == "EXTRACTION_FAILED"
                or not extracted.content
                or len(extracted.content.strip()) < 300
            ):
                print(f"      [SKIP] Insufficient body text extracted ({len(extracted.content or '')} chars)")
                continue

            # Step 3: Clean
            cleaned = cleaning_service.clean_article(extracted)
            if (
                cleaned.cleaning_status != CleaningStatus.SUCCESS
                or not cleaned.cleaned_content
                or len(cleaned.cleaned_content.strip()) < 250
            ):
                print(f"      [SKIP] Step 3 Cleaning rejected content ({len(cleaned.cleaned_content or '')} chars)")
                continue

            # Step 4: Duplicate Check
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
                print(f"      [SKIP] Step 4 Dedup error: {e}")
                continue

            if dedup_result.status != "unique":
                print(f"      [SKIP] Duplicate detected ({dedup_result.decision.duplicate_reason})")
                continue

            # Step 5: Persist
            try:
                persisted = knowledge_service.persist_from_step4(dedup_result)
                print(f"      [SUCCESS] Step 5 Persisted to DB! Article ID: {persisted.id}")
            except ArticleDuplicateError:
                print(f"      [SKIP] DB duplicate constraint")
                continue
            except Exception as e:
                print(f"      [SKIP] Step 5 error: {e}")
                continue

            # Step 6 & 7: Gemini Synthesis via MCP
            print(f"      [Step 7] Generating structured publication via Gemini AI...")
            try:
                req = ArticleGenerationRequest(
                    article_id=persisted.id,
                    custom_instructions="Synthesize in fluent professional English suitable for national entertainment reporting while preserving regional context, names, and verified facts."
                )
                gen_resp = mcp_gen_service.generate_from_mcp_article(req)
                if not gen_resp.success or not gen_resp.data:
                    print(f"      [ERROR] Step 7 Gemini generation failed")
                    continue
                generated_news = gen_resp.data
                gen_title_clean = generated_news.title.encode("ascii", errors="replace").decode("ascii")
                print(f"      [SUCCESS] Step 7 Generated: '{gen_title_clean[:65]}...'")
            except Exception as e:
                print(f"      [ERROR] Step 7 Gemini error: {e}")
                continue

            # Step 8: Google Doc Creation
            print(f"      [Step 8] Creating Google Document in Google Drive...")
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
                        print(f"      [SUCCESS] Step 8 Google Document Created!")
                        print(f"        Document ID:  {doc_id}")
                        print(f"        Document URL: {doc_url}")
                        return {
                            "subcategory": subcat_name,
                            "code": subcat_info["code"],
                            "article_id": persisted.id,
                            "generated_title": gen_title_clean,
                            "google_document_id": doc_id,
                            "google_document_url": doc_url,
                        }
            except Exception as e:
                print(f"      [ERROR] Step 8 error: {e}")
                continue

    print(f"  [WARNING] Could not complete subcategory [{subcat_name}].")
    return None


async def main():
    print("=" * 80)
    print("ESTD — 8 REGIONAL ENTERTAINMENT SUBCATEGORIES COMPLETE RUN")
    print(f"Current Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("Target Scope: Telugu, Hindi, Bollywood, Tollywood & Indian Entertainment")
    print("=" * 80)

    # Initialize services
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

    for subcat_info in TARGET_SUBCATEGORIES:
        res = await process_single_subcategory(
            subcat_info=subcat_info,
            extraction_service=extraction_service,
            cleaning_service=cleaning_service,
            knowledge_service=knowledge_service,
            mcp_gen_service=mcp_gen_service,
            step8_orchestrator=step8_orchestrator,
            gnews_adapter=gnews_adapter,
        )
        if res:
            results.append(res)
        await asyncio.sleep(1.0)

    print("\n" + "=" * 80)
    print(f"REGIONAL EXECUTION COMPLETE: {len(results)}/{len(TARGET_SUBCATEGORIES)} SUBCATEGORIES PROCESSED")
    print("=" * 80)
    for r in results:
        print(f"[{r['subcategory']}] (DB ID: {r['article_id']})")
        print(f"  Title: {r['generated_title']}")
        print(f"  GDoc:  {r['google_document_url']}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
