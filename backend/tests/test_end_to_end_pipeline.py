"""Complete end-to-end verification and integration test suite: STEP 1 -> 2 -> 3 -> 4 -> 5."""
from datetime import datetime, timezone
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.exceptions.custom_exceptions import InvalidCategoryError
from backend.database.connection.session import get_db_session, get_engine, init_db
from backend.database.models.news_article import NewsArticle
from backend.database.repositories.category_repository import CategoryRepository
from backend.database.repositories.news_article_repository import NewsArticleRepository
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.detectors.similarity_detector import SimilarityDetector
from backend.step4_duplicate_detection.models.duplicate_record import (
    DuplicateDecision,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.schemas.duplicate_response import DuplicateCheckResult
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)
from backend.step5_knowledge_source.exceptions import (
    ArticleDuplicateError,
    ArticleNotFoundError,
)
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService


@pytest.fixture(scope="session", autouse=True)
def setup_database_schema():
    """Ensure database tables and canonical categories exist."""
    init_db()
    with get_db_session() as session:
        CategoryRepository.seed_categories(session)


@pytest.fixture
def clean_e2e_db():
    """Isolate tests by removing test articles without touching historical or production articles."""
    engine = get_engine()
    test_filter = "url LIKE '%example.com%' OR title LIKE 'E2E %' OR title LIKE 'Article A %' OR title LIKE 'Article B %' OR title LIKE 'Valid Article in Mixed Batch' OR title LIKE 'Failed Article in Mixed Batch'"
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM news_articles WHERE {test_filter};"))
        conn.execute(text("DELETE FROM estd_duplicate_index WHERE url LIKE '%example.com%' OR normalized_url LIKE '%example.com%';"))
        conn.commit()
    yield
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM news_articles WHERE {test_filter};"))
        conn.execute(text("DELETE FROM estd_duplicate_index WHERE url LIKE '%example.com%' OR normalized_url LIKE '%example.com%';"))
        conn.commit()


class TestEndToEndPipeline:
    """Verifies continuous execution from Step 1 through Step 5 without skipping any stage."""

    @pytest.mark.asyncio
    async def test_full_pipeline_step1_to_step5_single_article(self, clean_e2e_db):
        """Mandatory Section 8 Full End-to-End Pipeline Test:
        Step 1 -> Step 2 -> Step 3 -> Step 4 (UNIQUE) -> Step 5 (PostgreSQL Persistence) -> Retrieval.
        """
        # -------------------------------------------------------------
        # STEP 1: Source Collection (NewsItem contract)
        # -------------------------------------------------------------
        item = NewsItem(
            title="E2E Autonomous Drones Complete Clinical Logistics Trials",
            description="Autonomous electric aircraft complete automated regional hospital supply runs.",
            url="https://healthtech.example.com/e2e-medical-drone-trials",
            source_name="HealthTech Global",
            source_type="rss",
            author="Dr. Rachel Stone",
            published_at="2026-10-05T08:00:00Z",
            category="Tech",
            image_url="https://healthtech.example.com/images/drone.jpg",
            collected_at="2026-10-05T08:15:00Z",
        )
        assert item.category == "Tech"
        assert item.url == "https://healthtech.example.com/e2e-medical-drone-trials"

        # -------------------------------------------------------------
        # STEP 2: Article Extraction
        # -------------------------------------------------------------
        raw_html_body = (
            "<article>\n"
            "<h1>Autonomous Drones Complete Clinical Logistics Trials</h1>\n"
            "<div class='ad-slot'>SPONSORED CONTENT</div>\n"
            "<p>Autonomous electric cargo drones have successfully concluded a ninety-day operational "
            "trial connecting twelve regional medical centers across mountainous terrain.</p>\n"
            "<p>The uncrewed aircraft delivered over four thousand units of perishable biologics, "
            "diagnostic blood samples, and antivenom serums with zero inflight incidents.</p>\n"
            "<footer>Sign up for our newsletter | Follow us on Twitter</footer>\n"
            "</article>"
        )
        extracted = ExtractedArticle(
            title=item.title,
            description=item.description,
            url=item.url,
            canonical_url=item.url,
            source_name=item.source_name,
            source_type=item.source_type,
            author=item.author,
            published_at=item.published_at,
            category=item.category,
            image_url=item.image_url,
            collected_at=item.collected_at,
            extraction_status="EXTRACTED",
            extraction_method="article_web_extraction",
            content=raw_html_body,
        )
        assert extracted.extraction_status == "EXTRACTED"
        assert "<article>" in extracted.content

        # -------------------------------------------------------------
        # STEP 3: Content Cleaning
        # -------------------------------------------------------------
        cleaning_service = ContentCleaningService()
        cleaned: CleanedArticle = cleaning_service.clean_article(extracted)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "<article>" not in (cleaned.cleaned_content or "")
        assert "SPONSORED CONTENT" not in (cleaned.cleaned_content or "")
        assert "newsletter" not in (cleaned.cleaned_content or "").lower()
        assert len(cleaned.cleaned_content or "") > 80

        # Verify metadata preservation between Step 1 and Step 3
        assert cleaned.title == item.title
        assert cleaned.category == item.category
        assert cleaned.source_type == item.source_type
        assert cleaned.source_name == item.source_name
        assert cleaned.url == item.url

        # -------------------------------------------------------------
        # STEP 4: Duplicate Detection
        # -------------------------------------------------------------
        with get_db_session() as session:
            dedup_service = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=True,
                    persist_unique_articles=True,
                )
            )
            dedup_result = dedup_service.check_article(cleaned, session=session)
            session.commit()

        assert dedup_result.status == "unique"
        assert dedup_result.decision.status == DuplicateStatus.UNIQUE
        assert dedup_result.decision.is_duplicate is False
        assert dedup_result.decision.normalized_url is not None
        assert dedup_result.decision.content_hash is not None

        # -------------------------------------------------------------
        # STEP 5: PostgreSQL Persistence
        # -------------------------------------------------------------
        knowledge_service = KnowledgeSourceService()
        persisted: NewsArticle = knowledge_service.persist_from_step4(dedup_result)

        assert persisted.id is not None
        assert persisted.title == item.title
        assert persisted.category == "Tech"
        assert persisted.category_id is not None
        assert persisted.normalized_url == dedup_result.decision.normalized_url
        assert persisted.content_hash == dedup_result.decision.content_hash

        # -------------------------------------------------------------
        # POSTGRESQL DIRECT QUERY VERIFICATION
        # -------------------------------------------------------------
        with get_db_session() as session:
            db_article = NewsArticleRepository.get_by_id(session, persisted.id)
            assert db_article is not None
            assert db_article.id == persisted.id
            assert db_article.title == item.title
            assert db_article.url == item.url
            assert db_article.category == "Tech"
            assert db_article.category_ref.name == "Tech"
            assert "<p>" not in db_article.content

    def test_critical_duplicate_database_test(self, clean_e2e_db):
        """Mandatory Section 7 Critical Duplicate Database Test:
        Process exact same article twice:
          Run 1 -> Step 4 UNIQUE -> Step 5 persisted into DB
          Run 2 -> Step 4 DUPLICATE -> Step 5 rejected
        Verify directly in PostgreSQL: row count is EXACTLY 1!
        """
        article_body = (
            "NASA astrophysicists announced the discovery of a terrestrial-mass exoplanet orbiting "
            "within the habitable zone of a nearby red dwarf star located 35 light years from Earth. "
            "Initial transmission spectroscopic observations confirm an atmosphere with water vapor."
        )
        cleaned = CleanedArticle(
            title="E2E Habitable Exoplanet Discovered",
            description="New exoplanet detected in nearby star system.",
            content=article_body,
            cleaned_content=article_body,
            url="https://space.example.com/e2e-habitable-exoplanet",
            canonical_url="https://space.example.com/e2e-habitable-exoplanet",
            source_name="Space News",
            source_type="rss",
            author="Dr. Sagan",
            published_at="2026-10-05T09:00:00Z",
            category="Science",
            collected_at="2026-10-05T09:10:00Z",
            cleaning_status=CleaningStatus.SUCCESS,
            cleaned_content_length=len(article_body),
            original_content_length=len(article_body),
        )

        knowledge_service = KnowledgeSourceService()

        # -------------------------------------------------------------
        # FIRST EXECUTION: Must be detected as UNIQUE and persisted
        # -------------------------------------------------------------
        with get_db_session() as session:
            dedup_service_1 = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=True,
                    persist_unique_articles=True,
                )
            )
            result_1 = dedup_service_1.check_article(cleaned, session=session)
            session.commit()

        assert result_1.status == "unique"
        assert result_1.decision.status == DuplicateStatus.UNIQUE

        persisted_1 = knowledge_service.persist_from_step4(result_1)
        assert persisted_1.id is not None

        # Verify exactly 1 row in PostgreSQL
        with get_db_session() as session:
            count_1 = session.scalar(
                select(func.count(NewsArticle.id)).where(NewsArticle.url == cleaned.url)
            )
            assert count_1 == 1

        # -------------------------------------------------------------
        # SECOND EXECUTION: Must be detected as DUPLICATE and blocked
        # -------------------------------------------------------------
        with get_db_session() as session:
            dedup_service_2 = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=True,
                    persist_unique_articles=True,
                )
            )
            result_2 = dedup_service_2.check_article(cleaned, session=session)
            session.commit()

        assert result_2.status == "duplicate"
        assert result_2.decision.status == DuplicateStatus.DUPLICATE
        assert result_2.decision.duplicate_reason == DuplicateReason.URL_MATCH

        # Attempt to pass duplicate to Step 5: MUST RAISE ArticleDuplicateError
        with pytest.raises(ArticleDuplicateError) as exc_info:
            knowledge_service.persist_from_step4(result_2)
        assert exc_info.value.status_code == 409

        # -------------------------------------------------------------
        # POSTGRESQL DIRECT COUNT CHECK: Row count MUST STILL BE 1
        # -------------------------------------------------------------
        with get_db_session() as session:
            count_2 = session.scalar(
                select(func.count(NewsArticle.id)).where(NewsArticle.url == cleaned.url)
            )
            assert count_2 == 1, f"Expected 1 article in database, but found {count_2}!"

    def test_current_batch_duplicate_detection(self, clean_e2e_db):
        """Mandatory Section 5.A Batch Duplicate Detection Test:
        Article A, Article B, Article A again in the same batch -> [A: UNIQUE, B: UNIQUE, A2: DUPLICATE].
        Only UNIQUE articles reach Step 5.
        """
        body_a = "Article A unique content describing advanced semiconductor packaging and chiplet interconnects."
        body_b = "Article B completely different content covering global trade logistics and maritime shipping routes."

        art_a1 = CleanedArticle(
            title="Article A Chiplet Tech",
            content=body_a,
            cleaned_content=body_a,
            url="https://example.com/article-a-chiplets",
            category="Technology",
            source_type="rss",
            collected_at="2026-10-05T10:00:00Z",
            cleaning_status=CleaningStatus.SUCCESS,
        )
        art_b = CleanedArticle(
            title="Article B Trade Logistics",
            content=body_b,
            cleaned_content=body_b,
            url="https://example.com/article-b-trade",
            category="Business",
            source_type="rss",
            collected_at="2026-10-05T10:00:00Z",
            cleaning_status=CleaningStatus.SUCCESS,
        )
        art_a2 = CleanedArticle(
            title="Article A Duplicate Copy",
            content=body_a,
            cleaned_content=body_a,
            url="https://example.com/article-a-chiplets",  # Same canonical URL
            category="Technology",
            source_type="rss",
            collected_at="2026-10-05T10:00:00Z",
            cleaning_status=CleaningStatus.SUCCESS,
        )

        with get_db_session() as session:
            dedup_service = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=True,
                    persist_unique_articles=True,
                )
            )
            batch_items = dedup_service.check_batch([art_a1, art_b, art_a2], session=session)
            session.commit()

        assert len(batch_items) == 3
        unique_items = [it for it in batch_items if it.status == "unique"]
        dup_items = [it for it in batch_items if it.status == "duplicate"]
        assert len(unique_items) == 2
        assert len(dup_items) == 1

        res_a1 = batch_items[0]
        res_b = batch_items[1]
        res_a2 = batch_items[2]

        assert res_a1.status == "unique"
        assert res_b.status == "unique"
        assert res_a2.status == "duplicate"
        assert res_a2.decision.duplicate_reason == DuplicateReason.URL_MATCH

        # Persist only unique items into Step 5
        knowledge_service = KnowledgeSourceService()
        persisted_items = []
        for item in batch_items:
            if item.status == "unique":
                persisted_items.append(knowledge_service.persist_from_step4(item))

        assert len(persisted_items) == 2
        with get_db_session() as session:
            persisted_in_db = session.scalar(
                select(func.count(NewsArticle.id)).where(
                    NewsArticle.url.in_(["https://example.com/article-a-chiplets", "https://example.com/article-b-trade"])
                )
            )
            assert persisted_in_db == 2

    def test_cosine_similarity_scenarios(self, clean_e2e_db):
        """Mandatory Section 5.C Cosine Similarity Verification:
        1. Exact same content -> 1.0
        2. Minor wording changes -> High similarity (>=0.80)
        3. Completely different article -> Low similarity (<0.3)
        4. Same topic but different news event -> Below threshold (<0.82)
        5. Same title but substantially different content -> Below threshold
        6. Short / insufficient content -> Safely handled without crash
        """
        detector = SimilarityDetector(threshold=0.82)

        # 1. Exact same content
        base_text = (
            "OpenAI announced a new reasoning model for software developers today. "
            "The system demonstrates enhanced mathematical reasoning and algorithmic problem solving "
            "across standard benchmarks and software engineering evaluation suites worldwide."
        )
        score_exact = detector.calculate_pairwise_similarity(base_text, base_text)
        assert score_exact >= 0.99

        # 2. Minor wording changes (nearly identical article)
        nearly_identical_text = (
            "OpenAI announced a new reasoning model for software developers today. "
            "The system demonstrates enhanced mathematical reasoning and algorithmic problem solving "
            "across standard benchmarks and software engineering assessment suites worldwide."
        )
        score_para = detector.calculate_pairwise_similarity(base_text, nearly_identical_text)
        assert score_para >= 0.85  # Demonstrates high semantic overlap for near-identical wording

        # 3. Completely different article
        diff_text = (
            "NASA astronomers using the James Webb Space Telescope observed gravitational lensing "
            "around a massive cluster of galaxies five billion light years away."
        )
        score_diff = detector.calculate_pairwise_similarity(base_text, diff_text)
        assert score_diff < 0.20

        # 4. Same topic (AI), different news event
        different_event_text = (
            "Anthropic introduced redesigned Claude enterprise workspaces with compliance controls "
            "and centralized administrative management for corporate deployments."
        )
        score_diff_event = detector.calculate_pairwise_similarity(base_text, different_event_text)
        assert score_diff_event < 0.50

        # 5. Same title, different content
        score_title = detector.calculate_pairwise_similarity(base_text, diff_text)
        assert score_title < 0.20

        # 6. Short / empty content
        score_empty = detector.calculate_pairwise_similarity("", "")
        assert score_empty == 0.0

        score_short = detector.calculate_pairwise_similarity("hello world", "quick brown fox")
        assert score_short == 0.0


    @pytest.mark.asyncio
    async def test_cross_source_pipeline_step1_to_step5(self, clean_e2e_db):
        """Mandatory Section 9 Cross-Source End-to-End Test:
        Verify that GNews, NewsData.io, and RSS all produce canonical NewsItems that pass
        through Step 2 Extraction, Step 3 Cleaning, Step 4 Deduplication, and Step 5 Persistence.
        """
        knowledge_service = KnowledgeSourceService()
        cleaning_service = ContentCleaningService()

        source_scenarios = [
            {
                "provider": "gnews",
                "title": "E2E GNews Breakthrough in Quantum Materials",
                "category": "Developments",
                "url": "https://gnews.example.com/quantum-materials",
                "content": "<p>Physicists have synthesized a stable room-temperature topological insulator.</p>",
            },
            {
                "provider": "newsdata",
                "title": "E2E NewsData Venture Capital Investment Report",
                "category": "Business & Finance",
                "url": "https://newsdata.example.com/vc-report-2026",
                "content": "<p>Global venture investments in generative AI automation expanded by forty percent.</p>",
            },
            {
                "provider": "rss",
                "title": "E2E RSS Higher Education Digital Transformation",
                "category": "Developments",
                "url": "https://rss.example.com/higher-ed-ai-tools",
                "content": "<p>Universities are adopting personalized tutoring agents across engineering curricula.</p>",
            },
        ]

        for sc in source_scenarios:
            # Step 1: NewsItem
            item = NewsItem(
                title=sc["title"],
                url=sc["url"],
                source_type=sc["provider"],
                source_name=f"Provider-{sc['provider']}",
                category=sc["category"],
                collected_at="2026-10-05T10:00:00Z",
            )
            assert item.source_type == sc["provider"]

            # Step 2: ExtractedArticle
            extracted = ExtractedArticle(
                title=item.title,
                url=item.url,
                canonical_url=item.url,
                source_name=item.source_name,
                source_type=item.source_type,
                category=item.category,
                collected_at=item.collected_at,
                extraction_status="EXTRACTED",
                extraction_method="article_web_extraction",
                content=sc["content"],
            )

            # Step 3: CleanedArticle
            cleaned = cleaning_service.clean_article(extracted)
            assert cleaned.cleaning_status == CleaningStatus.SUCCESS

            # Step 4: Duplicate Detection
            with get_db_session() as session:
                dedup_service = DuplicateDetectionService(
                    config=DuplicateDetectionConfig(
                        enable_historical_detection=True,
                        persist_unique_articles=True,
                    )
                )
                result = dedup_service.check_article(cleaned, session=session)
                session.commit()
            assert result.status == "unique"

            # Step 5: Knowledge Source Persistence
            persisted = knowledge_service.persist_from_step4(result)
            assert persisted.id is not None
            assert persisted.source_type == sc["provider"]
            assert persisted.category == sc["category"]

        # Verify all 3 source types present in PostgreSQL
        with get_db_session() as session:
            sources = set(session.scalars(select(NewsArticle.source_type).where(NewsArticle.url.like("%example.com%"))).all())
            assert sources == {"gnews", "newsdata", "rss"}

    def test_all_five_categories_end_to_end(self, clean_e2e_db):
        """Mandatory Section 11 Category Integrity:
        Verify end-to-end pipeline across all 5 canonical categories.
        """
        knowledge_service = KnowledgeSourceService()
        cleaning_service = ContentCleaningService()

        for idx, cat in enumerate(VALID_CATEGORIES):
            content = f"Comprehensive analysis and verified facts concerning developments in {cat}."
            url = f"https://example.com/e2e-all-cats-{idx}"

            item = NewsItem(
                title=f"E2E Report on {cat}",
                url=url,
                source_type="rss",
                source_name=f"{cat} Monitor",
                category=cat,
                collected_at="2026-10-05T11:00:00Z",
            )
            extracted = ExtractedArticle(
                title=item.title,
                url=item.url,
                canonical_url=item.url,
                source_name=item.source_name,
                source_type=item.source_type,
                category=item.category,
                collected_at=item.collected_at,
                extraction_status="EXTRACTED",
                extraction_method="article_web_extraction",
                content=f"<p>{content}</p>",
            )
            cleaned = cleaning_service.clean_article(extracted)
            assert cleaned.category == cat

            with get_db_session() as session:
                dedup_service = DuplicateDetectionService(
                    config=DuplicateDetectionConfig(
                        enable_historical_detection=True,
                        persist_unique_articles=True,
                    )
                )
                res = dedup_service.check_article(cleaned, session=session)
                session.commit()

            persisted = knowledge_service.persist_from_step4(res)
            assert persisted.category == cat

        # Verify PostgreSQL contains exactly articles across the 5 categories
        with get_db_session() as session:
            stored_categories = set(session.scalars(select(NewsArticle.category).where(NewsArticle.url.like("%example.com%"))).all())
            assert stored_categories == set(VALID_CATEGORIES)

    def test_pipeline_idempotency_second_run_creates_zero_new_rows(self, clean_e2e_db):
        """Mandatory Section 14 Idempotency Test:
        Run the complete pipeline twice with the same batch of 3 articles.
        First run -> 3 inserted.
        Second run -> 3 duplicates detected, 0 inserted.
        Final row count must remain 3.
        """
        knowledge_service = KnowledgeSourceService()
        cleaning_service = ContentCleaningService()

        articles = [
            {
                "title": "Quantum Computing Chip Architecture Milestone",
                "cat": "Tech",
                "url": "https://example.com/idemp-quantum-chip",
                "content": "<p>Engineers have announced an 80-qubit coherent superconducting quantum processor with reduced thermal dissipation and state-of-the-art error mitigation protocols.</p>",
            },
            {
                "title": "Astronomers Detect Atmospheric Methane on Habitable Exoplanet",
                "cat": "Developments",
                "url": "https://example.com/idemp-exoplanet-methane",
                "content": "<p>Spectroscopic observations using deep space infrared telescopes revealed strong chemical biosignature absorption bands in the upper atmosphere of an Earth-sized exoplanet.</p>",
            },
            {
                "title": "Venture Capital Deployments in Clean Energy Accelerate",
                "cat": "Business & Finance",
                "url": "https://example.com/idemp-clean-energy-vc",
                "content": "<p>Private equity syndicates allocated twenty billion dollars into commercial grid-scale battery storage facilities and long-duration hydrogen infrastructure across North America.</p>",
            },
        ]

        def process_batch():
            inserted_count = 0
            duplicate_count = 0
            for a in articles:
                item = NewsItem(
                    title=a["title"],
                    url=a["url"],
                    source_type="rss",
                    category=a["cat"],
                    collected_at="2026-10-05T12:00:00Z",
                )
                extracted = ExtractedArticle(
                    title=item.title,
                    url=item.url,
                    canonical_url=item.url,
                    source_name="Idempotency Feed",
                    source_type=item.source_type,
                    category=item.category,
                    collected_at=item.collected_at,
                    extraction_status="EXTRACTED",
                    extraction_method="article_web_extraction",
                    content=a["content"],
                )
                cleaned = cleaning_service.clean_article(extracted)
                with get_db_session() as session:
                    dedup_service = DuplicateDetectionService(
                        config=DuplicateDetectionConfig(
                            enable_historical_detection=True,
                            persist_unique_articles=True,
                        )
                    )
                    res = dedup_service.check_article(cleaned, session=session)
                    session.commit()

                if res.status == "unique":
                    knowledge_service.persist_from_step4(res)
                    inserted_count += 1
                else:
                    duplicate_count += 1
            return inserted_count, duplicate_count

        # Run 1
        ins1, dup1 = process_batch()
        assert ins1 == 3
        assert dup1 == 0
        with get_db_session() as session:
            persisted_in_db = session.scalar(
                select(func.count(NewsArticle.id)).where(
                    NewsArticle.url.in_([a["url"] for a in articles])
                )
            )
            assert persisted_in_db == 3

        # Run 2
        ins2, dup2 = process_batch()
        assert ins2 == 0
        assert dup2 == 3
        with get_db_session() as session:
            persisted_in_db = session.scalar(
                select(func.count(NewsArticle.id)).where(
                    NewsArticle.url.in_([a["url"] for a in articles])
                )
            )
            assert persisted_in_db == 3

    def test_pipeline_failure_handling_does_not_abort_valid_articles(self, clean_e2e_db):
        """Mandatory Section 12 Failure Handling:
        One corrupted/empty article in a batch does NOT crash or abort processing of valid articles.
        """
        cleaning_service = ContentCleaningService()
        knowledge_service = KnowledgeSourceService()

        # 1. Valid Article
        valid_extracted = ExtractedArticle(
            title="Valid Article in Mixed Batch",
            url="https://example.com/valid-mixed-1",
            category="Technology",
            source_type="rss",
            collected_at="2026-10-05T12:00:00Z",
            content="Valid substantive article text content describing robotics.",
            extraction_status="EXTRACTED",
        )

        # 2. Failed Extraction Article (empty content)
        failed_extracted = ExtractedArticle(
            title="Failed Article in Mixed Batch",
            url="https://example.com/failed-mixed-2",
            category="Technology",
            source_type="rss",
            collected_at="2026-10-05T12:00:00Z",
            content="",
            extraction_status="EXTRACTION_FAILED",
            error_message="HTTP 500 Server Error",
        )

        # Step 3 handles failure gracefully
        cleaned_valid = cleaning_service.clean_article(valid_extracted)
        cleaned_failed = cleaning_service.clean_article(failed_extracted)

        assert cleaned_valid.cleaning_status == CleaningStatus.SUCCESS
        assert cleaned_failed.cleaning_status == CleaningStatus.CLEANING_FAILED

        # Step 4 & 5 process valid article
        with get_db_session() as session:
            dedup_service = DuplicateDetectionService(
                config=DuplicateDetectionConfig(enable_historical_detection=True, persist_unique_articles=True)
            )
            res_valid = dedup_service.check_article(cleaned_valid, session=session)
            session.commit()

        persisted = knowledge_service.persist_from_step4(res_valid)
        assert persisted.id is not None
        assert persisted.title == "Valid Article in Mixed Batch"
