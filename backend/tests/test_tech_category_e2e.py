"""Comprehensive Verification and Acceptance Tests for ESTD Tech Category (Category ID 1).

Covers:
1. Taxonomy Verification (Top-level Category ID 1, 7 Canonical Subcategories IDs 18-24)
2. Source Registry (Tech Feeds, Languages, Providers, Subcategory mappings)
3. Article Extraction & Sufficiency Verification
4. Content Cleaning & Unicode Normalization (English & Telugu preservation, code/version safety)
5. Step 4 Deduplication & Hash Protection
6. Step 5 PostgreSQL Knowledge Source Persistence & Integrity
7. Step 6 PostgreSQL MCP Read-Only Retrieval & SQL Safety
8. Step 7 Gemini AI News Synthesis Schema Validation & Fact Grounding
9. Step 8 Google Drive Folder Resolution & Document Staging Integrity
10. Protection of Frozen Entertainment & Sports Categories (Zero Regression Guarantee)
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


class TestTechTaxonomy:
    """Phase 1: Verification of Canonical Tech Taxonomy."""

    def test_canonical_tech_category_exists_in_db(self):
        with get_db_session() as session:
            tech = session.query(Category).filter(Category.id == 1).first()
            assert tech is not None, "Category ID 1 must exist in database"
            assert tech.name == "Tech", "Category ID 1 name must be 'Tech'"
            assert tech.code == "TECH", "Category ID 1 code must be 'TECH'"
            assert tech.is_active is True, "Category ID 1 must be active"

    def test_all_seven_canonical_tech_subcategories_exist(self):
        expected_subcategories = {
            18: ("Artificial Intelligence", "TECH_AI", "artificial-intelligence"),
            19: ("Software & Cloud", "TECH_SOFTWARE_CLOUD", "software-cloud"),
            20: ("Consumer Technology & Gadgets", "TECH_CONSUMER_GADGETS", "consumer-technology-gadgets"),
            21: ("Cybersecurity & Privacy", "TECH_CYBERSECURITY", "cybersecurity-privacy"),
            22: ("Developer Technologies & Open Source", "TECH_DEV_TOOLS", "developer-technologies"),
            23: ("Emerging Tech & Semiconductors", "TECH_EMERGING_HARDWARE", "emerging-tech-semiconductors"),
            24: ("Digital Platforms & Big Tech", "TECH_PLATFORMS", "digital-platforms"),
        }

        with get_db_session() as session:
            subcats = session.query(Subcategory).filter(Subcategory.category_id == 1).all()
            assert len(subcats) == 7, f"Expected exactly 7 tech subcategories, found {len(subcats)}"
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
            ESTDSubcategory.ARTIFICIAL_INTELLIGENCE,
            ESTDSubcategory.SOFTWARE_CLOUD,
            ESTDSubcategory.CONSUMER_TECH_GADGETS,
            ESTDSubcategory.CYBERSECURITY_PRIVACY,
            ESTDSubcategory.DEVELOPER_TECH,
            ESTDSubcategory.EMERGING_TECH_SEMICONDUCTORS,
            ESTDSubcategory.DIGITAL_PLATFORMS,
        ]:
            resolved = resolve_subcategory(sub_enum.value)
            assert resolved == sub_enum.value


class TestTechSourceRegistry:
    """Phase 3: Source Registry Coverage Verification."""

    def test_registered_tech_sources_coverage(self):
        registry = get_source_registry()
        tech_sources = registry.get_sources_by_category("Tech")
        assert len(tech_sources) >= 10, "At least 10 tech sources must be registered"

        source_ids = {s.source_id for s in tech_sources}
        assert "mit_tech_review_ai" in source_ids
        assert "venturebeat_ai" in source_ids
        assert "the_verge_tech" in source_ids
        assert "the_hacker_news" in source_ids
        assert "github_blog" in source_ids
        assert "toms_hardware" in source_ids
        assert "the_hindu_tech" in source_ids
        assert "oneindia_telugu_tech" in source_ids

    def test_multilingual_tech_sources(self):
        registry = get_source_registry()
        tech_sources = registry.get_sources_by_category("Tech")
        languages = {s.language for s in tech_sources}
        assert "en" in languages, "English sources must be present"
        assert "te" in languages, "Telugu sources must be present"


class TestTechExtractionAndCleaning:
    """Phases 5 & 6: Content Extraction, Cleaning and Unicode Normalization."""

    def test_cleaning_preserves_technical_terms_and_versions(self):
        cleaning_service = ContentCleaningService()
        raw_article = ExtractedArticle(
            title="Nvidia RTX 5060 Ti Launched Alongside DDR5-6000 Memory Architecture",
            content="Nvidia has introduced the RTX 5060 Ti with 16GB GDDR7 memory. In testing, the DDR5-6000 bandwidth showed a 28.5% improvement over PCIe 4.0 standards.",
            url="https://example.com/tech/nvidia-rtx-5060-ti",
            source_type="rss",
            category="Tech",
            subcategory="Emerging Tech & Semiconductors",
            language="en",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )
        cleaned = cleaning_service.clean_article(raw_article)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "RTX 5060 Ti" in cleaned.cleaned_content
        assert "DDR5-6000" in cleaned.cleaned_content
        assert "28.5%" in cleaned.cleaned_content

    def test_telugu_unicode_preservation(self):
        cleaning_service = ContentCleaningService()
        raw_article = ExtractedArticle(
            title="వన్ ప్లస్ 12: సరికొత్త ఫీచర్లు మరియు స్పెసిఫికేషన్లు విడుదల",
            content="భారతదేశంలో వన్ ప్లస్ 12 స్మార్ట్‌ఫోన్ అధికారికంగా విడుదలైంది. స్నాప్‌డ్రాగన్ 8 జెన్ 3 ప్రాసెసర్‌తో ఇది అద్భుతమైన పనితీరును కనబరుస్తుంది.",
            url="https://telugu.example.com/oneplus-12-launch",
            source_type="rss",
            category="Tech",
            subcategory="Consumer Technology & Gadgets",
            language="te",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )
        cleaned = cleaning_service.clean_article(raw_article)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "వన్ ప్లస్ 12" in cleaned.cleaned_content
        assert "స్మార్ట్‌ఫోన్" in cleaned.cleaned_content
        assert cleaned.language == "te"


class TestTechDeduplication:
    """Phase 7: Deduplication Verification."""

    def test_sha256_content_hash_integrity(self):
        import uuid
        cleaning_service = ContentCleaningService()
        unique_url = f"https://example.com/tech/cloudflare-deno-{uuid.uuid4().hex[:8]}"
        raw_article = ExtractedArticle(
            title="Cloudflare Acquires Deno to Boost Serverless Workers",
            content="Cloudflare has announced the acquisition of Deno, reinforcing its edge cloud runtime and developer platform capabilities.",
            url=unique_url,
            source_type="rss",
            category="Tech",
            subcategory="Software & Cloud",
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


class TestTechKnowledgeSourcePersistence:
    """Phase 8: PostgreSQL Persistence & Read-back Verification."""

    def test_tech_articles_persisted_in_database(self):
        with get_db_session() as session:
            articles = session.query(NewsArticle).filter(NewsArticle.category_id == 1).all()
            assert len(articles) >= 7, f"Expected at least 7 tech articles, found {len(articles)}"
            for art in articles:
                assert art.category == "Tech"
                assert art.category_id == 1
                assert art.subcategory_id in range(18, 25)
                assert art.content is not None and len(art.content) > 100
                assert art.normalized_url is not None
                assert art.content_hash is not None

    def test_all_seven_subcategories_have_persisted_articles(self):
        with get_db_session() as session:
            subcat_ids = {
                art.subcategory_id
                for art in session.query(NewsArticle).filter(NewsArticle.category_id == 1).all()
            }
            expected_ids = set(range(18, 25))
            assert expected_ids.issubset(subcat_ids), f"Missing subcategories: {expected_ids - subcat_ids}"


class TestTechMCPIntegration:
    """Phase 9: Read-Only MCP Retrieval Verification."""

    def test_mcp_retrieval_and_sql_injection_guard(self):
        mcp_service = MCPService()
        # Verify read-only query works
        res = mcp_service.query_knowledge_source("SELECT id, title, category FROM news_articles WHERE category_id = 1 LIMIT 3;")
        assert len(res) > 0
        for row in res:
            assert row.get("category") == "Tech"

        # Verify SQL mutation guards block destructive queries
        with pytest.raises(Exception):
            mcp_service.query_knowledge_source("DROP TABLE news_articles;")

        with pytest.raises(Exception):
            mcp_service.query_knowledge_source("DELETE FROM news_articles WHERE id = 1;")


class TestTechGeminiSynthesis:
    """Phase 10: Gemini Output & Grounding Validation."""

    def test_generated_news_validation_rules(self):
        valid_news = GeneratedNews(
            title="Cloudflare Completes Deno Acquisition for Edge Serverless Compute",
            category=ESTDCategory.TECH,
            subcategory="Software & Cloud",
            summary="Cloudflare has announced the completed acquisition of Deno to strengthen its serverless compute offerings and developer tools.",
            content="Cloudflare announced on Friday that it has officially acquired Deno. The acquisition is structured to unify Deno's modern JavaScript and TypeScript runtime with Cloudflare Workers' distributed network across global points of presence.",
            source_name="TechCrunch",
            source_url="https://techcrunch.com/2026/10/10/cloudflare-acquires-deno",
            generated_at=datetime.now(timezone.utc),
        )
        # Should pass validation without error
        GenerationValidator.validate_generated_news(valid_news, expected_category="Tech")

    def test_grounding_verification_rejects_hallucinations(self):
        hallucinated_news = GeneratedNews(
            title="Alien Spacecraft Discovered Orbiting Jupiter Moon Europa by Astronomers",
            category=ESTDCategory.TECH,
            subcategory="Emerging Tech & Semiconductors",
            summary="Astronomers have reported the anomalous observation of an unknown artifact near Europa with non-natural propulsion signatures.",
            content="A mysterious craft with exotic propulsion was reportedly observed today near Europa. The anomalous object exhibited non-keplerian trajectory characteristics that baffle conventional astrophysical observation models.",
            source_name="Science Daily",
            source_url="https://example.com/alien-europa",
            generated_at=datetime.now(timezone.utc),
        )
        # Source content completely unrelated to the alien spacecraft story
        source_content = "Lithium battery cathode manufacturing advances using cobalt-free synthetic phosphate chemistry solutions."
        with pytest.raises(GenerationValidationError):
            GenerationValidator.verify_grounding(hallucinated_news, source_content=source_content)


class TestTechGoogleDriveHierarchy:
    """Phase 11: Google Drive Subfolder Mapping Verification."""

    def test_canonical_subcategory_folders_registered(self):
        assert "Tech" in CANONICAL_SUBCATEGORY_FOLDERS
        tech_folders = CANONICAL_SUBCATEGORY_FOLDERS["Tech"]
        assert len(tech_folders) == 7
        assert "Artificial Intelligence" in tech_folders
        assert "Software & Cloud" in tech_folders
        assert "Consumer Technology & Gadgets" in tech_folders
        assert "Cybersecurity & Privacy" in tech_folders
        assert "Developer Technologies & Open Source" in tech_folders
        assert "Emerging Tech & Semiconductors" in tech_folders
        assert "Digital Platforms & Big Tech" in tech_folders

    def test_persisted_google_documents_in_database(self):
        with get_db_session() as session:
            docs = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.category == "Tech").all()
            assert len(docs) >= 7, f"Expected at least 7 tech Google Docs, found {len(docs)}"
            for doc in docs:
                assert doc.status == "CREATED"
                assert doc.google_document_id is not None
                assert doc.google_drive_subcategory_folder_id is not None


class TestProtectionOfFrozenCategories:
    """Phase 13 Non-Negotiable Safety: Zero Regression on Entertainment & Sports."""

    def test_entertainment_taxonomy_untouched(self):
        with get_db_session() as session:
            ent = session.query(Category).filter(Category.id == 2).first()
            assert ent is not None
            assert ent.name == "Entertainment"
            assert ent.code == "ENT"
            subcats = session.query(Subcategory).filter(Subcategory.category_id == 2).all()
            assert len(subcats) == 8, f"Expected 8 Entertainment subcategories, found {len(subcats)}"

    def test_sports_taxonomy_untouched(self):
        with get_db_session() as session:
            sports = session.query(Category).filter(Category.id == 5).first()
            assert sports is not None
            assert sports.name == "Sports"
            assert sports.code == "SPORTS"
            subcats = session.query(Subcategory).filter(Subcategory.category_id == 5).all()
            assert len(subcats) == 9, f"Expected 9 Sports subcategories, found {len(subcats)}"

    def test_historical_article_counts_preserved(self):
        with get_db_session() as session:
            ent_count = session.query(NewsArticle).filter(NewsArticle.category_id == 2).count()
            sports_count = session.query(NewsArticle).filter(NewsArticle.category_id == 5).count()
            assert ent_count == 16, f"Entertainment articles count modified! Expected 16, got {ent_count}"
            assert sports_count == 30, f"Sports articles count modified! Expected 30, got {sports_count}"

    def test_historical_document_counts_preserved(self):
        with get_db_session() as session:
            ent_docs = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.category == "Entertainment").count()
            sports_docs = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.category == "Sports").count()
            assert ent_docs == 16, f"Entertainment documents count modified! Expected 16, got {ent_docs}"
            assert sports_docs == 30, f"Sports documents count modified! Expected 30, got {sports_docs}"
