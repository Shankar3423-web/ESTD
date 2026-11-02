"""Thin Pipeline Orchestration Coordinator for ESTD Backend.

Connects and executes the verified Steps 1–8 in sequence:
STEP 1: Source Collection (GNews, NewsData.io, RSS)
STEP 2: Article Extraction & Scraping
STEP 3: Content Cleaning & Normalization
STEP 4: Duplicate Detection (URL, Hash, Cosine Similarity)
STEP 5: PostgreSQL Persistence in Knowledge Source
STEP 6: MCP Access Layer Verification & Discovery
STEP 7: Gemini AI Processing & Generation
STEP 8: Google Docs Creation in Google Drive Category Folder
"""
import asyncio
from datetime import datetime, timezone
import threading
import time
import uuid
from typing import Dict, List, Optional

from backend.common.constants.categories import VALID_CATEGORIES, resolve_canonical_category
from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.google_document_record import DocumentStatus, GoogleDocumentRecord
from backend.database.models.news_article import NewsArticle
from backend.pipeline.models import (
    PipelineJobResponse,
    PipelineJobStatus,
    PipelineMetrics,
    SourceProviderStatus,
    StepDetail,
    StepStatus,
)
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.services.source_collection_service import (
    SourceCollectionService,
)
from backend.step2_article_extraction.services.extraction_service import (
    ExtractionService,
)
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)
from backend.step5_knowledge_source.exceptions import ArticleDuplicateError
from backend.step5_knowledge_source.services.knowledge_service import (
    KnowledgeSourceService,
)
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.schemas.generation_request import (
    ArticleGenerationRequest,
)
from backend.step7_content_generation.services.mcp_generation_service import (
    MCPGenerationService,
)
from backend.step8_gdrive_output.services.orchestrator import Step8Orchestrator


class PipelineOrchestrator:
    """Singleton orchestrator managing background pipeline execution jobs."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.jobs: Dict[str, PipelineJobResponse] = {}
        self.active_job_id: Optional[str] = None
        self.latest_job_id: Optional[str] = None
        self.generated_summaries: Dict[int, str] = {}

    def get_job(self, job_id: str) -> Optional[PipelineJobResponse]:
        """Retrieve job state by ID."""
        return self.jobs.get(job_id)

    def get_latest_job(self) -> Optional[PipelineJobResponse]:
        """Retrieve the most recent job state."""
        if self.latest_job_id and self.latest_job_id in self.jobs:
            return self.jobs[self.latest_job_id]
        return None

    def is_running(self) -> bool:
        """Check if any pipeline job is actively executing."""
        if not self.active_job_id:
            return False
        active_job = self.jobs.get(self.active_job_id)
        return bool(active_job and active_job.status in (PipelineJobStatus.QUEUED, PipelineJobStatus.RUNNING))

    def create_job(
        self,
        categories: Optional[List[str]] = None,
        target_per_category: int = 1,
    ) -> PipelineJobResponse:
        """Create and queue a new pipeline execution job."""
        if self.is_running():
            raise RuntimeError(f"Pipeline job '{self.active_job_id}' is already executing.")

        job_id = f"job-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        raw_cats = categories or list(VALID_CATEGORIES)
        target_categories = []
        for c in raw_cats:
            rc = resolve_canonical_category(c)
            cat_name = rc.value if rc else c
            if cat_name in VALID_CATEGORIES and cat_name not in target_categories:
                target_categories.append(cat_name)
        if not target_categories:
            target_categories = list(VALID_CATEGORIES)

        steps = {
            "step1": StepDetail(step_number=1, name="Source Collection (GNews, NewsData, RSS)", status=StepStatus.PENDING),
            "step2": StepDetail(step_number=2, name="Article Scraping / Extraction", status=StepStatus.PENDING),
            "step3": StepDetail(step_number=3, name="Content Cleaning & Normalization", status=StepStatus.PENDING),
            "step4": StepDetail(step_number=4, name="Duplicate Detection & TF-IDF Cosine Similarity", status=StepStatus.PENDING),
            "step5": StepDetail(step_number=5, name="PostgreSQL Knowledge Base Persistence", status=StepStatus.PENDING),
            "step6": StepDetail(step_number=6, name="MCP Access Layer Verification", status=StepStatus.PENDING),
            "step7": StepDetail(step_number=7, name="Gemini AI Fact-Grounded Synthesis", status=StepStatus.PENDING),
            "step8": StepDetail(step_number=8, name="Google Docs & Google Drive Output", status=StepStatus.PENDING),
        }

        sources = {
            "gnews": SourceProviderStatus(provider="gnews", name="GNews API", status="PENDING"),
            "newsdata": SourceProviderStatus(provider="newsdata", name="NewsData.io API", status="PENDING"),
            "rss": SourceProviderStatus(provider="rss", name="RSS Curated Feeds", status="PENDING"),
        }

        job = PipelineJobResponse(
            job_id=job_id,
            status=PipelineJobStatus.QUEUED,
            current_step="QUEUED",
            progress=0,
            created_at=now,
            steps=steps,
            sources=sources,
            metrics=PipelineMetrics(),
        )

        self.jobs[job_id] = job
        self.active_job_id = job_id
        self.latest_job_id = job_id

        # Launch background task
        asyncio.create_task(self._execute_pipeline(job_id, target_categories, target_per_category))
        return job

    async def _execute_pipeline(
        self,
        job_id: str,
        categories: List[str],
        target_per_category: int,
    ) -> None:
        """Execute the end-to-end pipeline through existing Steps 1–8 services."""
        job = self.jobs[job_id]
        start_time = time.monotonic()
        job.started_at = datetime.now(timezone.utc)
        job.status = PipelineJobStatus.RUNNING
        logger.info(f"Starting ESTD pipeline execution {job_id} across {len(categories)} categories...")

        try:
            # =========================================================================
            # STEP 1: Source Collection
            # =========================================================================
            job.current_step = "SOURCE_COLLECTION"
            job.progress = 10
            step1 = job.steps["step1"]
            step1.status = StepStatus.RUNNING
            step1.started_at = datetime.now(timezone.utc)

            source_service = SourceCollectionService()
            all_collected_items: List[NewsItem] = []

            # 1. GNews (Sampling up to first 2 categories to stay within API rate limit)
            try:
                gnews_cats = categories[:2] if len(categories) >= 2 else categories
                for cat in gnews_cats:
                    resp = await source_service.collect_from_gnews(category=cat, limit=2)
                    all_collected_items.extend(resp.items)
                job.sources["gnews"].status = "CONNECTED"
                job.sources["gnews"].count = len([i for i in all_collected_items if i.source_type == "gnews"])
            except Exception as exc:
                logger.warning(f"GNews collection notice: {exc}")
                job.sources["gnews"].status = "WARNING"
                job.sources["gnews"].error = str(exc)[:150]

            # 2. NewsData.io (Sampling up to 2 categories)
            try:
                newsdata_cats = categories[2:4] if len(categories) > 2 else categories
                for cat in newsdata_cats:
                    resp = await source_service.collect_from_newsdata(category=cat, limit=2)
                    all_collected_items.extend(resp.items)
                job.sources["newsdata"].status = "CONNECTED"
                job.sources["newsdata"].count = len([i for i in all_collected_items if i.source_type == "newsdata"])
            except Exception as exc:
                logger.warning(f"NewsData collection notice: {exc}")
                job.sources["newsdata"].status = "WARNING"
                job.sources["newsdata"].error = str(exc)[:150]

            # 3. RSS Feeds (All target canonical categories for reliable high-depth content)
            try:
                rss_count = 0
                for cat in categories:
                    resp = await source_service.collect_from_rss(category=cat, limit=2)
                    all_collected_items.extend(resp.items)
                    rss_count += len(resp.items)
                job.sources["rss"].status = "CONNECTED"
                job.sources["rss"].count = rss_count
            except Exception as exc:
                logger.warning(f"RSS collection notice: {exc}")
                job.sources["rss"].status = "WARNING"
                job.sources["rss"].error = str(exc)[:150]

            job.metrics.fetched = len(all_collected_items)
            step1.status = StepStatus.COMPLETED
            step1.completed_at = datetime.now(timezone.utc)
            step1.details = f"Collected {len(all_collected_items)} candidate articles across providers."
            logger.info(f"Step 1 Complete: {len(all_collected_items)} items fetched.")

            # Group candidates by category to ensure balanced progression
            candidates_by_cat: Dict[str, List[NewsItem]] = {c: [] for c in categories}
            for item in all_collected_items:
                if item.category in candidates_by_cat:
                    candidates_by_cat[item.category].append(item)

            # Select up to target_per_category * 2 for scraping
            scraping_candidates: List[NewsItem] = []
            for cat, items in candidates_by_cat.items():
                scraping_candidates.extend(items[: max(2, target_per_category * 2)])

            # =========================================================================
            # STEP 2: Article Extraction / Scraping
            # =========================================================================
            job.current_step = "SCRAPING"
            job.progress = 25
            step2 = job.steps["step2"]
            step2.status = StepStatus.RUNNING
            step2.started_at = datetime.now(timezone.utc)

            extraction_service = ExtractionService()
            scraped_articles = []

            for item in scraping_candidates:
                try:
                    # Force full article body extraction
                    extracted = await extraction_service.extract_article(item, force_fetch=True)
                    if (
                        extracted.extraction_status != "EXTRACTION_FAILED"
                        and extracted.content
                        and len(extracted.content.strip()) >= 200
                    ):
                        scraped_articles.append(extracted)
                        job.metrics.scraped += 1
                except Exception as exc:
                    logger.debug(f"Extraction skipped for {item.url}: {exc}")

            step2.status = StepStatus.COMPLETED
            step2.completed_at = datetime.now(timezone.utc)
            step2.details = f"Scraped and extracted body content for {len(scraped_articles)} articles."
            logger.info(f"Step 2 Complete: {len(scraped_articles)} articles scraped.")

            # =========================================================================
            # STEP 3: Content Cleaning & Normalization
            # =========================================================================
            job.current_step = "CONTENT_CLEANING"
            job.progress = 40
            step3 = job.steps["step3"]
            step3.status = StepStatus.RUNNING
            step3.started_at = datetime.now(timezone.utc)

            cleaning_service = ContentCleaningService()
            cleaned_articles = []

            for extracted in scraped_articles:
                try:
                    cleaned = cleaning_service.clean_article(extracted)
                    if (
                        cleaned.cleaning_status == CleaningStatus.SUCCESS
                        and cleaned.cleaned_content
                        and len(cleaned.cleaned_content.strip()) >= 200
                    ):
                        cleaned_articles.append(cleaned)
                        job.metrics.cleaned += 1
                except Exception as exc:
                    logger.debug(f"Cleaning error: {exc}")

            step3.status = StepStatus.COMPLETED
            step3.completed_at = datetime.now(timezone.utc)
            step3.details = f"Cleaned and normalized {len(cleaned_articles)} articles."
            logger.info(f"Step 3 Complete: {len(cleaned_articles)} articles cleaned.")

            # =========================================================================
            # STEP 4: Duplicate Detection (URL, SHA-256, TF-IDF Cosine Similarity)
            # =========================================================================
            job.current_step = "DUPLICATE_DETECTION"
            job.progress = 55
            step4 = job.steps["step4"]
            step4.status = StepStatus.RUNNING
            step4.started_at = datetime.now(timezone.utc)

            unique_check_results = []
            with get_db_session() as session:
                dedup_service = DuplicateDetectionService(
                    config=DuplicateDetectionConfig(
                        enable_historical_detection=True,
                        persist_unique_articles=True,
                    )
                )
                for cleaned in cleaned_articles:
                    try:
                        dedup_result = dedup_service.check_article(cleaned, session=session)
                        if dedup_result.status == "unique":
                            unique_check_results.append(dedup_result)
                        else:
                            job.metrics.duplicates_removed += 1
                    except Exception as exc:
                        logger.debug(f"Deduplication check error: {exc}")
                session.commit()

            step4.status = StepStatus.COMPLETED
            step4.completed_at = datetime.now(timezone.utc)
            step4.details = (
                f"Identified {len(unique_check_results)} unique articles; "
                f"{job.metrics.duplicates_removed} duplicates filtered."
            )
            logger.info(f"Step 4 Complete: {len(unique_check_results)} unique items identified.")

            # =========================================================================
            # STEP 5: PostgreSQL Knowledge Source Persistence
            # =========================================================================
            job.current_step = "POSTGRESQL_STORAGE"
            job.progress = 70
            step5 = job.steps["step5"]
            step5.status = StepStatus.RUNNING
            step5.started_at = datetime.now(timezone.utc)

            knowledge_service = KnowledgeSourceService()
            persisted_article_ids: List[int] = []

            for result in unique_check_results:
                try:
                    with get_db_session() as session:
                        persisted = knowledge_service.persist_from_step4(result, session=session)
                        persisted_article_ids.append(persisted.id)
                        job.metrics.stored_in_postgres += 1
                except ArticleDuplicateError:
                    job.metrics.duplicates_removed += 1
                except Exception as exc:
                    logger.warning(f"Persistence error for article: {exc}")

            step5.status = StepStatus.COMPLETED
            step5.completed_at = datetime.now(timezone.utc)
            step5.details = f"Persisted {len(persisted_article_ids)} new articles into PostgreSQL."
            logger.info(f"Step 5 Complete: {len(persisted_article_ids)} articles stored in PostgreSQL.")

            # =========================================================================
            # STEP 6: MCP Access Layer Verification
            # =========================================================================
            job.current_step = "MCP_ACCESS"
            job.progress = 78
            step6 = job.steps["step6"]
            step6.status = StepStatus.RUNNING
            step6.started_at = datetime.now(timezone.utc)

            mcp_service = MCPService()
            mcp_gen_service = MCPGenerationService(mcp_service=mcp_service)

            # Query knowledge source articles through MCP
            eligible_mcp_articles = mcp_gen_service.list_eligible_articles(limit=25)
            step6.status = StepStatus.COMPLETED
            step6.completed_at = datetime.now(timezone.utc)
            step6.details = f"MCP layer operational. Discovered {len(eligible_mcp_articles)} eligible articles via MCP."
            logger.info(f"Step 6 Complete: MCP queried {len(eligible_mcp_articles)} eligible articles.")

            # Determine articles to generate: prefer newly persisted, otherwise eligible knowledge source articles
            articles_to_generate_ids: List[int] = []
            if persisted_article_ids:
                articles_to_generate_ids.extend(persisted_article_ids)
            else:
                # If no new articles were persisted (e.g. repeated run), pick eligible articles without Docs
                with get_db_session() as session:
                    existing_docs = {
                        r.article_id
                        for r in session.query(GoogleDocumentRecord.article_id)
                        .filter(GoogleDocumentRecord.status == DocumentStatus.CREATED.value)
                        .all()
                    }
                    candidates = [a.id for a in eligible_mcp_articles if a.id not in existing_docs]
                    if not candidates:
                        candidates = [a.id for a in eligible_mcp_articles[: max(1, target_per_category * len(categories))]]
                    articles_to_generate_ids.extend(candidates[: max(1, target_per_category * len(categories))])

            # Limit generation count to target_per_category * categories
            max_to_process = max(1, target_per_category * len(categories))
            articles_to_generate_ids = articles_to_generate_ids[:max_to_process]

            # =========================================================================
            # STEP 7: Gemini AI Processing (via MCP)
            # =========================================================================
            job.current_step = "AI_GENERATION"
            job.progress = 86
            step7 = job.steps["step7"]
            step7.status = StepStatus.RUNNING
            step7.started_at = datetime.now(timezone.utc)

            generated_news_map = {}
            for art_id in articles_to_generate_ids:
                try:
                    req = ArticleGenerationRequest(article_id=art_id)
                    gen_response = mcp_gen_service.generate_from_mcp_article(req)
                    if gen_response.success and gen_response.data:
                        generated_news_map[art_id] = gen_response.data
                        self.generated_summaries[art_id] = gen_response.data.summary
                        job.metrics.ai_generated += 1
                except Exception as exc:
                    logger.warning(f"Step 7 Gemini generation warning for article {art_id}: {exc}")
                    job.metrics.failed += 1

            step7.status = StepStatus.COMPLETED
            step7.completed_at = datetime.now(timezone.utc)
            step7.details = f"Generated {len(generated_news_map)} fact-grounded ESTD articles via Gemini AI."
            logger.info(f"Step 7 Complete: {len(generated_news_map)} articles generated.")

            # =========================================================================
            # STEP 8: Google Docs Creation in Google Drive Category Folders
            # =========================================================================
            job.current_step = "GOOGLE_DOCS"
            job.progress = 94
            step8 = job.steps["step8"]
            step8.status = StepStatus.RUNNING
            step8.started_at = datetime.now(timezone.utc)

            step8_orchestrator = Step8Orchestrator()
            # Ensure folder hierarchy is verified
            step8_orchestrator.folder_resolver.initialize_hierarchy(force_refresh=False)

            docs_created_count = 0
            for art_id, generated_news in generated_news_map.items():
                try:
                    with get_db_session() as session:
                        doc_resp = step8_orchestrator.process_approved_content(
                            news=generated_news,
                            article_id=art_id,
                            session=session,
                        )
                        if doc_resp.success:
                            docs_created_count += 1
                            job.metrics.docs_created += 1
                except Exception as exc:
                    logger.warning(f"Step 8 Google Docs creation warning for article {art_id}: {exc}")
                    job.metrics.failed += 1

            step8.status = StepStatus.COMPLETED
            step8.completed_at = datetime.now(timezone.utc)
            step8.details = f"Created and routed {docs_created_count} documents in Google Drive category folders."
            logger.info(f"Step 8 Complete: {docs_created_count} Google Documents created.")

            # =========================================================================
            # FINALIZE JOB
            # =========================================================================
            job.current_step = "COMPLETED"
            job.progress = 100
            job.status = PipelineJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = round(time.monotonic() - start_time, 2)
            logger.info(f"ESTD pipeline job {job_id} COMPLETED successfully in {job.duration_seconds}s.")

        except Exception as exc:
            job.status = PipelineJobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            job.duration_seconds = round(time.monotonic() - start_time, 2)
            job.last_error = f"Pipeline execution failed: {str(exc)[:300]}"
            logger.exception(f"ESTD pipeline job {job_id} FAILED: {exc}")

        finally:
            self.active_job_id = None


# Singleton instance
pipeline_orchestrator = PipelineOrchestrator()
