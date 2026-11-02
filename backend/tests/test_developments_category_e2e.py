"""Comprehensive Verification and Acceptance Tests for ESTD Developments Category (Category ID 4).

Covers:
1. Taxonomy Verification (Top-level Category ID 4, 7 Canonical Subcategories IDs 25-31)
2. Source Registry (Developments Feeds, Languages, Providers, Subcategory mappings)
3. Article Extraction & Sufficiency Verification
4. Content Cleaning & Unicode Normalization (English & Telugu preservation, policy facts, dates)
5. Step 4 Deduplication & Hash Protection
6. Step 5 PostgreSQL Knowledge Source Persistence & Integrity
7. Step 6 PostgreSQL MCP Read-Only Retrieval & SQL Safety
8. Step 7 Gemini AI News Synthesis Schema Validation & Fact Grounding
9. Step 8 Google Drive Folder Resolution & Document Staging Integrity
10. Protection of Frozen Entertainment, Sports, and Tech Categories (Zero Regression Guarantee)
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from backend.common.constants.categories import ESTDCategory, ESTDSubcategory, resolve_subcategory
from backend.database.connection.session import get_db_session
from backend.database.models import Category, Subcategory, NewsArticle, GoogleDocumentRecord
from backend.step1_source_collection.models.news_item import NewsItem
from backend.step1_source_collection.rss.sources.registry import get_source_registry
from backend.step2_article_extraction.models.extracted_article import ExtractedArticle
from backend.step2_article_extraction.models.extraction_enums import ExtractionStatus, ExtractionMethod
from backend.step3_content_cleaning.models.cleaning_enums import CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import ContentCleaningService
from backend.step4_duplicate_detection.config import DuplicateDetectionConfig
from backend.step4_duplicate_detection.models.duplicate_record import DuplicateReason
from backend.step4_duplicate_detection.services.duplicate_detection_service import DuplicateDetectionService
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.validators.generation_validator import (
    GenerationValidator,
    GenerationValidationError,
)
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver, CANONICAL_SUBCATEGORY_FOLDERS


class TestDevelopmentsTaxonomy:
    """Phase 1 & 2: Verification of Canonical Developments Taxonomy."""

    def test_canonical_developments_category_exists_in_db(self):
        with get_db_session() as session:
            dev = session.query(Category).filter(Category.id == 4).first()
            assert dev is not None, "Category ID 4 must exist in database"
            assert dev.name == "Developments", "Category ID 4 name must be 'Developments'"
            assert dev.code == "DEV", "Category ID 4 code must be 'DEV'"
            assert dev.is_active is True, "Category ID 4 must be active"

    def test_all_seven_canonical_developments_subcategories_exist(self):
        expected_subcategories = {
            25: ("Government & Public Policy", "DEV_GOV_POLICY", "government-public-policy"),
            26: ("Infrastructure & Urban Planning", "DEV_INFRA", "infrastructure-planning"),
            27: ("Energy, Climate & Environment", "DEV_ENERGY_CLIMATE", "energy-environment"),
            28: ("Health & Medical Sciences", "DEV_HEALTH_MED", "health-medical-sciences"),
            29: ("Education & Learning Policy", "DEV_EDUCATION", "education-learning-policy"),
            30: ("Science & Research Discoveries", "DEV_SCIENCE_RESEARCH", "science-research"),
            31: ("Global Affairs & Geopolitics", "DEV_GLOBAL_AFFAIRS", "global-affairs"),
        }

        with get_db_session() as session:
            subcats = session.query(Subcategory).filter(Subcategory.category_id == 4).all()
            assert len(subcats) == 7, f"Expected exactly 7 developments subcategories, found {len(subcats)}"
            found_ids = {s.id for s in subcats}
            assert found_ids == set(expected_subcategories.keys()), "Mismatch in subcategory primary keys"

            for s in subcats:
                exp_name, exp_code, exp_slug = expected_subcategories[s.id]
                assert s.name == exp_name
                assert s.code == exp_code
                assert s.slug == exp_slug
                assert s.is_active is True

    def test_enum_to_database_taxonomy_consistency(self):
        for sub_enum in [
            ESTDSubcategory.GOVERNMENT_PUBLIC_POLICY,
            ESTDSubcategory.INFRASTRUCTURE_PLANNING,
            ESTDSubcategory.ENERGY_ENVIRONMENT,
            ESTDSubcategory.HEALTH_MEDICAL_SCIENCES,
            ESTDSubcategory.EDUCATION_LEARNING_POLICY,
            ESTDSubcategory.SCIENCE_RESEARCH,
            ESTDSubcategory.GLOBAL_AFFAIRS,
        ]:
            resolved = resolve_subcategory(sub_enum.value)
            assert resolved == sub_enum.value


class TestDevelopmentsSourceRegistry:
    """Phase 4: Source Registry Coverage Verification."""

    def test_registered_developments_sources_coverage(self):
        registry = get_source_registry()
        dev_sources = registry.get_sources_by_category("Developments")
        assert len(dev_sources) >= 10, "At least 10 developments sources must be registered"

        source_ids = {s.source_id for s in dev_sources}
        assert "un_news_global" in source_ids
        assert "who_news" in source_ids
        assert "nature_journal" in source_ids
        assert "phys_org" in source_ids
        assert "the_hindu_national" in source_ids
        assert "the_hindu_environment" in source_ids
        assert "the_hindu_health" in source_ids
        assert "the_hindu_education" in source_ids
        assert "indian_express_national" in source_ids
        assert "indian_express_education" in source_ids
        assert "the_hindu_hyderabad" in source_ids
        assert "telangana_today_hyd" in source_ids
        assert "oneindia_telugu_dev" in source_ids
        assert "sakshi_telangana_dev" in source_ids

    def test_developments_language_diversity(self):
        registry = get_source_registry()
        dev_sources = registry.get_sources_by_category("Developments")
        languages = {s.language for s in dev_sources}
        assert "en" in languages, "English developments feeds must be present"
        assert "te" in languages, "Telugu regional developments feeds must be present"

    def test_developments_geographic_diversity(self):
        registry = get_source_registry()
        dev_sources = registry.get_sources_by_category("Developments")
        regions = {s.region for s in dev_sources}
        assert "IN" in regions, "India national/regional feeds must be present"
        assert "US" in regions or "CH" in regions, "International feeds must be present"


class TestDevelopmentsPipelineProcessing:
    """Phases 6-8: Extraction, Cleaning, Normalization and Deduplication."""

    def test_cleaning_service_preserves_telugu_unicode(self):
        cleaning_service = ContentCleaningService()
        raw_telugu = (
            "<p>స్థానిక సంస్థల ఎన్నికల ప్రక్రియను రాష్ట్ర ఎన్నికల సంఘం వేగవంతం చేసింది.</p>"
            "<div>ఓటర్ల జాబితా నమోదు, అభ్యంతరాల స్వీకరణ పూర్తి చేసినట్లు అధికారులు ప్రకటించారు.</div>"
        )
        extracted = ExtractedArticle(
            url="https://telugu.oneindia.com/news/telangana-test-policy.html",
            title="స్థానిక సంస్థల ఎన్నికల ప్రక్రియ",
            content=raw_telugu,
            source_name="Oneindia Telugu",
            source_type="rss",
            category="Developments",
            subcategory="Government & Public Policy",
            language="te",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )

        cleaned = cleaning_service.clean_article(extracted)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "స్థానిక సంస్థల ఎన్నికల ప్రక్రియను" in cleaned.cleaned_content
        assert "రాష్ట్ర ఎన్నికల సంఘం" in cleaned.cleaned_content
        assert cleaned.language == "te"

    def test_duplicate_detection_prevents_exact_url_collision(self):
        import uuid
        cleaning_service = ContentCleaningService()
        unique_url = f"https://example.com/dev/policy-report-{uuid.uuid4().hex[:8]}"
        raw_article = ExtractedArticle(
            title="Public Infrastructure Investment Framework Announced",
            content="A comprehensive urban infrastructure investment plan was released detailing capital outlays for metro transport expansion.",
            url=unique_url,
            source_type="rss",
            category="Developments",
            subcategory="Infrastructure & Urban Planning",
            language="en",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )
        cleaned = cleaning_service.clean_article(raw_article)

        with get_db_session() as session:
            dedup_service = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=False,
                )
            )
            results = dedup_service.check_batch([cleaned, cleaned], session=session)
            assert len(results) == 2
            assert results[0].status == "unique"
            assert results[1].status == "duplicate", "Second identical item must be detected as duplicate"
            assert results[1].decision.duplicate_reason == DuplicateReason.URL_MATCH


class TestDevelopmentsPostgresPersistence:
    """Phase 9: PostgreSQL Knowledge Source Persistence Verification."""

    def test_developments_articles_persisted_with_valid_fks(self):
        with get_db_session() as session:
            articles = session.query(NewsArticle).filter(NewsArticle.category_id == 4).all()
            assert len(articles) >= 7, "All 7 canonical subcategories must have persisted articles"

            for art in articles:
                assert art.category == "Developments"
                assert art.category_id == 4
                assert art.subcategory_id in {25, 26, 27, 28, 29, 30, 31}
                assert art.content is not None and len(art.content.strip()) > 100
                assert art.content_hash is not None and len(art.content_hash) == 64

    def test_all_seven_subcategories_represented_in_articles(self):
        with get_db_session() as session:
            articles = session.query(NewsArticle).filter(NewsArticle.category_id == 4).all()
            sub_ids = {art.subcategory_id for art in articles}
            assert {25, 26, 27, 28, 29, 30, 31}.issubset(sub_ids), (
                f"Missing subcategories in news_articles. Present: {sub_ids}"
            )


class TestDevelopmentsMCPAccess:
    """Phase 10: Read-Only MCP Retrieval and Safety Verification."""

    def test_mcp_service_retrieves_developments_article(self):
        mcp_service = MCPService()
        sql = "SELECT id, title, category, subcategory FROM news_articles WHERE category_id = 4 ORDER BY id LIMIT 1;"
        rows = mcp_service.query_knowledge_source(sql)
        assert len(rows) == 1
        assert rows[0]["category"] == "Developments"

    def test_mcp_service_rejects_sql_mutations(self):
        mcp_service = MCPService()
        for forbidden_sql in [
            "INSERT INTO categories (name, code, slug) VALUES ('Hack', 'HACK', 'hack');",
            "UPDATE news_articles SET title = 'Altered' WHERE id = 1;",
            "DELETE FROM news_articles WHERE id = 1;",
            "DROP TABLE news_articles;",
            "TRUNCATE TABLE news_articles;",
        ]:
            with pytest.raises(Exception):
                mcp_service.query_knowledge_source(forbidden_sql)


class TestDevelopmentsGeminiAIValidation:
    """Phase 11: Gemini Structured Output Schema Validation."""

    def test_valid_generated_news_passes_validation(self):
        valid_news = GeneratedNews(
            title="Adani-Linked Mining Project Threatens Rare Jeypore Ground Gecko in Eastern Ghats",
            category=ESTDCategory.DEVELOPMENTS,
            subcategory="Energy, Climate & Environment",
            summary="A proposed bauxite mining project in Odisha threatens the micro-endemic Jeypore ground gecko population.",
            content="The Jeypore ground gecko (Cyrtodactylus jeyporensis), rediscovered after 135 years, faces habitat loss from bauxite mining lease proposals in Koraput district. Conservation biologists have urged environmental ministries to review biodiversity clearances.",
            source_name="The Hindu",
            source_url="https://www.thehindu.com/sci-tech/energy-and-environment/mining-project-threatens-gecko.html",
            generated_at=datetime.now(timezone.utc),
        )
        GenerationValidator.validate_generated_news(valid_news, expected_category="Developments")

    def test_grounding_verification_rejects_hallucinations(self):
        hallucinated_news = GeneratedNews(
            title="Ancient Deep-Sea Pyramid Complex Discovered Beneath Indian Ocean",
            category=ESTDCategory.DEVELOPMENTS,
            subcategory="Science & Research Discoveries",
            summary="Oceanographers have reportedly uncovered massive stone pyramids resting on the seabed.",
            content="A mysterious submerged stone pyramid was reportedly observed today during seabed mapping. The architectural characteristics baffle conventional geology.",
            source_name="Science Daily",
            source_url="https://example.com/pyramid-ocean",
            generated_at=datetime.now(timezone.utc),
        )
        source_content = "Solar photovoltaic panel recycling regulations announced by municipal authorities to reduce electronic waste."
        with pytest.raises(GenerationValidationError):
            GenerationValidator.verify_grounding(hallucinated_news, source_content=source_content)


class TestDevelopmentsGoogleDriveHierarchy:
    """Phase 3 & 12: Google Drive Hierarchy and Document Reconciliation."""

    def test_canonical_subcategory_folders_registered(self):
        assert "Developments" in CANONICAL_SUBCATEGORY_FOLDERS
        dev_folders = CANONICAL_SUBCATEGORY_FOLDERS["Developments"]
        assert len(dev_folders) == 7

        expected_names = [
            "Government & Public Policy",
            "Infrastructure & Urban Planning",
            "Energy, Climate & Environment",
            "Health & Medical Sciences",
            "Education & Learning Policy",
            "Science & Research Discoveries",
            "Global Affairs & Geopolitics",
        ]
        for name in expected_names:
            assert name in dev_folders
            assert dev_folders[name] is not None and len(dev_folders[name]) > 10

    def test_google_document_records_created_and_reconciled(self):
        with get_db_session() as session:
            docs = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.category == "Developments").all()
            assert len(docs) >= 10, "At least 10 developments documents must exist in google_document_records"

            for doc in docs:
                assert doc.status == "CREATED"
                assert doc.google_document_id is not None
                assert doc.google_document_url is not None
                assert doc.google_drive_category_folder_id == "14ENJOk8LkChMt792K5s3_jD6FzVc_g1D"
                assert doc.google_drive_subcategory_folder_id is not None
                assert doc.google_drive_root_folder_id == "1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8"


class TestRegressionIsolation:
    """Phase 14: Absolute Protection of Frozen Categories."""

    def test_frozen_categories_isolation(self):
        with get_db_session() as session:
            # Check Tech (ID 1)
            tech = session.query(Category).filter(Category.id == 1).first()
            assert tech.name == "Tech"
            assert tech.code == "TECH"

            # Check Entertainment (ID 2)
            ent = session.query(Category).filter(Category.id == 2).first()
            assert ent.name == "Entertainment"
            assert ent.code == "ENT"

            # Check Sports (ID 5)
            sports = session.query(Category).filter(Category.id == 5).first()
            assert sports.name == "Sports"
            assert sports.code == "SPORTS"

    def test_frozen_subcategories_counts(self):
        with get_db_session() as session:
            tech_subs = session.query(Subcategory).filter(Subcategory.category_id == 1).count()
            assert tech_subs == 7, "Tech must have exactly 7 canonical subcategories"

            ent_subs = session.query(Subcategory).filter(Subcategory.category_id == 2).count()
            assert ent_subs == 8, "Entertainment must have exactly 8 canonical subcategories"

            sports_subs = session.query(Subcategory).filter(Subcategory.category_id == 5).count()
            assert sports_subs == 9, "Sports must have exactly 9 canonical subcategories"
