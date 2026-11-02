import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.services.duplicate_detection_service import DuplicateDetectionService
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.schemas.generation_request import ArticleGenerationRequest
from backend.step7_content_generation.services.mcp_generation_service import MCPGenerationService
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator

async def ingest_software_cloud():
    print("=" * 80)
    print("INGESTING SOFTWARE & CLOUD ARTICLE (STEPS 1 TO 8)")
    print("=" * 80)

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

    item = NewsItem(
        title="Cloudflare acquires Deno to improve its Workers programming model",
        url="https://techcrunch.com/2026/10/10/cloudflare-acquires-deno-to-improve-its-workers-programming-model/",
        source_name="TechCrunch",
        source_type="rss",
        category="Tech",
        subcategory="Software & Cloud",
        language="en",
        region="US",
        published_at="Fri, 10 Oct 2026 16:00:00 GMT",
    )

    print("[Step 2] Extracting article...")
    extracted = await extraction_service.extract_article(item, force_fetch=True)
    print(f"Extracted: {len(extracted.content or '')} chars | Status: {extracted.extraction_status.value}")

    print("[Step 3] Cleaning and normalizing...")
    cleaned = cleaning_service.clean_article(extracted)
    print(f"Cleaned: {len(cleaned.cleaned_content)} chars | Status: {cleaned.cleaning_status.value}")

    print("[Step 4] Checking duplicates...")
    with get_db_session() as session:
        dedup_service = DuplicateDetectionService(
            config=DuplicateDetectionConfig(enable_historical_detection=True, persist_unique_articles=True)
        )
        dedup_result = dedup_service.check_article(cleaned, session=session)
        session.commit()
    print(f"Dedup status: {dedup_result.status}")

    if dedup_result.status == "unique":
        print("[Step 5] Persisting to PostgreSQL news_articles...")
        persisted = knowledge_service.persist_from_step4(dedup_result)
        art_id = persisted.id
        print(f"Persisted Article ID: {art_id} | Subcategory ID: {persisted.subcategory_id}")
    else:
        with get_db_session() as session:
            existing = session.query(NewsArticle).filter(NewsArticle.url == item.url).first()
            art_id = existing.id
            print(f"Using existing Article ID: {art_id}")

    print(f"[Step 6] MCP Read-Only Retrieval for Article ID {art_id}...")
    mcp_row = mcp_gen_service.fetch_article_via_mcp(art_id)
    print(f"MCP Row Title: {mcp_row.get('title')[:60]} | Category: {mcp_row.get('category')} | Subcat: {mcp_row.get('subcategory')}")

    print(f"[Step 7] Generating AI synthesis via Gemini for Article ID {art_id}...")
    req = ArticleGenerationRequest(article_id=art_id)
    gen_resp = mcp_gen_service.generate_from_mcp_article(req)
    if not gen_resp.success or not gen_resp.data:
        raise RuntimeError(f"Generation failed: {gen_resp.message}")
    gen_news = gen_resp.data
    print(f"Generated Title: {gen_news.title}")
    print(f"Summary: {len(gen_news.summary)} chars | Content: {len(gen_news.content)} chars")

    print("[Step 8] Creating Google Document in Google Drive...")
    with get_db_session() as session:
        doc_resp = step8_orchestrator.process_approved_content(
            news=gen_news,
            article_id=art_id,
            session=session,
            original_published_at=item.published_at,
        )
        doc_id = doc_resp.data.google_document_id
        doc_url = doc_resp.data.google_document_url
        sub_folder = doc_resp.data.google_drive_subcategory_folder_id
        print(f"SUCCESS! Doc ID: {doc_id} | Subfolder ID: {sub_folder}")
        print(f"Doc URL: {doc_url}")

    # Read back metadata from Drive
    meta = gdrive_service.get_file_metadata(doc_id)
    print(f"Live Read-back Verified: '{meta.get('name')}' (Parents: {meta.get('parents')})")

if __name__ == "__main__":
    asyncio.run(ingest_software_cloud())
