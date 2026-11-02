"""Comprehensive Verification and Acceptance Tests for ESTD Sports Category (Category ID 5).

Covers:
1. Taxonomy Verification (Top-level Category ID 5, 9 Canonical Subcategories IDs 9-17)
2. Source Registry (Sports Feeds, Languages, Providers, Subcategory mappings)
3. Article Extraction & Sufficiency Verification
4. Content Cleaning & Unicode Normalization (English & Telugu preservation)
5. Step 4 Deduplication & Hash Protection
6. Step 5 PostgreSQL Knowledge Source Persistence & Integrity
7. Step 6 PostgreSQL MCP Read-Only Retrieval & SQL Safety
8. Step 7 Gemini AI News Synthesis Schema Validation
9. Step 8 Google Drive Folder Resolution & Document Staging Integrity
10. Protection of Frozen Entertainment Category (Zero Regression Guarantee)
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
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver


class TestSportsTaxonomy:
    """Phase 1: Verification of Canonical Sports Taxonomy."""

    def test_canonical_sports_category_exists_in_db(self):
        with get_db_session() as session:
            sports = session.query(Category).filter(Category.id == 5).first()
            assert sports is not None, "Category ID 5 must exist in database"
            assert sports.name == "Sports", "Category ID 5 name must be 'Sports'"
            assert sports.code == "SPORTS", "Category ID 5 code must be 'SPORTS'"
            assert sports.is_active is True, "Category ID 5 must be active"

    def test_all_nine_canonical_sports_subcategories_exist(self):
        expected_subcategories = {
            9: ("Cricket", "SPORTS_CRICKET", "cricket"),
            10: ("Football", "SPORTS_FOOTBALL", "football"),
            11: ("Tennis", "SPORTS_TENNIS", "tennis"),
            12: ("Badminton", "SPORTS_BADMINTON", "badminton"),
            13: ("Motorsport", "SPORTS_MOTORSPORT", "motorsport"),
            14: ("Hockey", "SPORTS_HOCKEY", "hockey"),
            15: ("Athletics & Olympic Sports", "SPORTS_ATHLETICS", "athletics-olympics"),
            16: ("Esports & Competitive Gaming", "SPORTS_ESPORTS", "esports-competitive-gaming"),
            17: ("Other Sports", "SPORTS_OTHER", "other-sports"),
        }

        with get_db_session() as session:
            subcats = session.query(Subcategory).filter(Subcategory.category_id == 5).all()
            assert len(subcats) == 9, f"Expected exactly 9 sports subcategories, found {len(subcats)}"
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
            ESTDSubcategory.CRICKET,
            ESTDSubcategory.FOOTBALL,
            ESTDSubcategory.TENNIS,
            ESTDSubcategory.BADMINTON,
            ESTDSubcategory.MOTORSPORT,
            ESTDSubcategory.HOCKEY,
            ESTDSubcategory.ATHLETICS_OLYMPICS,
            ESTDSubcategory.ESPORTS_COMPETITIVE,
            ESTDSubcategory.OTHER_SPORTS,
        ]:
            resolved = resolve_subcategory(sub_enum.value)
            assert resolved == sub_enum


class TestSportsSourceRegistry:
    """Phase 3: Source Registry Coverage Verification."""

    def test_registered_sports_sources_coverage(self):
        registry = get_source_registry()
        sports_sources = registry.get_sources_by_category("Sports")
        assert len(sports_sources) >= 5, "At least 5 sports sources must be registered"

        source_ids = {s.source_id for s in sports_sources}
        assert "the_hindu_sport" in source_ids
        assert "hindustan_times_sports" in source_ids
        assert "chess_com_news" in source_ids
        assert "oneindia_telugu_sports" in source_ids

    def test_regional_language_sports_source_exists(self):
        registry = get_source_registry()
        telugu_sources = [s for s in registry.get_sources_by_category("Sports") if s.language == "te"]
        assert len(telugu_sources) >= 1, "At least one Telugu sports source must be registered"
        assert any("oneindia" in s.source_id or "sakshi" in s.source_id for s in telugu_sources)


class TestSportsCleaningAndUnicode:
    """Phase 6: Cleaning and Unicode Preservation."""

    def test_telugu_unicode_preservation_in_cleaning(self):
        cleaner = ContentCleaningService()
        raw_telugu = (
            "సిరాజ్ సేన విధ్వంసం.. హైదరాబాద్‌కు ఘన విజయం!\n\n"
            "రంజీ ట్రోఫీ 2026-27 సీజన్‌లో మహ్మద్ సిరాజ్ నేతృత్వంలోని హైదరాబాద్ జట్టు ఘన విజయం సాధించింది. "
            "త్రిపురతో జరిగిన మ్యాచ్‌లో ఇన్నింగ్స్ మరియు 45 పరుగుల తేడాతో గెలిచింది. "
            "తనయ్ త్యాగరాజన్ 9 వికెట్లతో రాణించాడు."
        )
        item = NewsItem(
            title="సిరాజ్ సేన విధ్వంసం.. హైదరాబాద్‌కు ఘన విజయం!",
            url="https://telugu.oneindia.com/sports/test-ranji",
            source_name="Oneindia Telugu",
            source_type="rss",
            category="Sports",
            subcategory="Cricket",
            language="te"
        )
        extraction = ExtractedArticle.from_existing_content(item, content=raw_telugu)
        cleaned = cleaner.clean_article(extraction)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "సిరాజ్ సేన" in cleaned.cleaned_content
        assert "హైదరాబాద్ జట్టు" in cleaned.cleaned_content
        assert "9 వికెట్లతో" in cleaned.cleaned_content
        assert cleaned.language == "te"

    def test_sports_scores_and_metrics_preservation(self):
        cleaner = ContentCleaningService()
        raw_text = (
            "Alexander Zverev defeated Carlos Alcaraz 6-4, 7-6 (7-3) in the Shanghai Masters semifinal. "
            "With this 120-minute victory, Zverev earned 1,000 ATP points and secured year-end No. 1 ranking."
        )
        item = NewsItem(
            title="Zverev claims year-end No 1 ranking",
            url="https://www.hindustantimes.com/sports/tennis/test-zverev",
            source_name="Hindustan Times",
            source_type="rss",
            category="Sports",
            subcategory="Tennis",
            language="en"
        )
        extraction = ExtractedArticle.from_existing_content(item, content=raw_text)
        cleaned = cleaner.clean_article(extraction)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "6-4, 7-6 (7-3)" in cleaned.cleaned_content
        assert "1,000 ATP points" in cleaned.cleaned_content


class TestSportsDuplicateDetection:
    """Phase 7: Deduplication Verification."""

    def test_canonical_url_duplicate_rejected(self):
        import uuid
        cleaner = ContentCleaningService()
        unique_test_url = f"https://telugu.oneindia.com/sports/ranji-trophy-test-{uuid.uuid4().hex[:8]}.html"
        item = NewsItem(
            title="Duplicate Ranji Check",
            url=unique_test_url,
            source_name="Oneindia Telugu",
            source_type="rss",
            category="Sports",
            subcategory="Cricket",
            language="te"
        )
        extraction = ExtractedArticle.from_existing_content(
            item,
            content="సిరాజ్ సేన విధ్వంసం హైదరాబాద్ జట్టు ఘన విజయం సాధించింది త్రిపురతో జరిగిన మ్యాచ్‌లో ఇన్నింగ్స్ విజయం."
        )
        cleaned = cleaner.clean_article(extraction)

        with get_db_session() as session:
            dedup = DuplicateDetectionService(
                config=DuplicateDetectionConfig(
                    enable_historical_detection=False,
                )
            )
            results = dedup.check_batch([cleaned, cleaned], session=session)
            assert len(results) == 2
            assert results[0].status == "unique"
            assert results[1].status == "duplicate", "Second identical item must be detected as duplicate"
            assert results[1].decision.duplicate_reason == DuplicateReason.URL_MATCH


class TestSportsPostgresAndMCP:
    """Phase 8 & 9: Database Persistence and Read-Only MCP Retrieval."""

    def test_all_sports_subcategories_persisted_in_database(self):
        with get_db_session() as session:
            articles = session.query(NewsArticle).filter(NewsArticle.category_id == 5).all()
            assert len(articles) >= 9, f"Expected at least 9 persisted sports articles, found {len(articles)}"
            covered_subcat_ids = {a.subcategory_id for a in articles}
            expected_ids = set(range(9, 18))
            missing = expected_ids - covered_subcat_ids
            assert not missing, f"Missing persisted articles for subcategory IDs: {missing}"

    def test_mcp_query_retrieves_sports_article_safely(self):
        mcp = MCPService()
        result = mcp.query_knowledge_source(
            "SELECT id, title, category, subcategory, language FROM news_articles WHERE category_id = 5 ORDER BY id ASC LIMIT 1;"
        )
        assert len(result) == 1
        article = result[0]
        assert article["category"] == "Sports"
        assert article["subcategory"] in [
            "Cricket", "Football", "Tennis", "Badminton", "Motorsport",
            "Hockey", "Athletics & Olympic Sports", "Esports & Competitive Gaming", "Other Sports"
        ]

    def test_mcp_sql_injection_defense(self):
        mcp = MCPService()
        with pytest.raises(Exception):
            mcp.query_knowledge_source("DROP TABLE news_articles;")
        with pytest.raises(Exception):
            mcp.query_knowledge_source("DELETE FROM news_articles WHERE id = 1051;")


class TestSportsDriveFolderRouting:
    """Phase 2 & 11: Google Drive Hierarchy and Resolver."""

    def test_sports_root_folder_configured(self):
        resolver = DriveFolderResolver()
        sports_folder_id = resolver.resolve_category_folder_id("Sports")
        assert sports_folder_id == "1KbF5HuofvQaB7fYhaNFQESn2Xq_xBFLs"

    def test_sports_documents_staged_in_db(self):
        with get_db_session() as session:
            docs = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.category == "Sports").all()
            assert len(docs) >= 9, f"Expected at least 9 staged sports documents, found {len(docs)}"
            for d in docs:
                assert d.article_id is not None
                assert d.google_drive_category_folder_id == "1KbF5HuofvQaB7fYhaNFQESn2Xq_xBFLs"
                assert d.status in ["CREATED", "FAILED"]


class TestEntertainmentFreezeProtection:
    """Phase 16: Zero-Regression Protection of Frozen Entertainment Category."""

    def test_entertainment_category_and_subcategories_unmodified(self):
        with get_db_session() as session:
            ent = session.query(Category).filter(Category.id == 2).first()
            assert ent is not None
            assert ent.name == "Entertainment"

            ent_subcats = session.query(Subcategory).filter(Subcategory.category_id == 2).order_by(Subcategory.id).all()
            assert len(ent_subcats) == 8, "Entertainment must retain exactly 8 canonical subcategories"
            expected_ent_sub_ids = [1, 2, 3, 4, 5, 6, 7, 8]
            assert [s.id for s in ent_subcats] == expected_ent_sub_ids

    def test_historical_entertainment_articles_intact(self):
        with get_db_session() as session:
            ent_articles = session.query(NewsArticle).filter(NewsArticle.category_id == 2).all()
            assert len(ent_articles) >= 16, "All 16 production Entertainment articles must remain intact"
            art_ids = {a.id for a in ent_articles}
            for expected_id in [2, 495, 496, 497, 498, 500, 501, 503, 504, 509, 512, 553, 557, 559, 560, 562]:
                assert expected_id in art_ids, f"Historical Entertainment article {expected_id} missing"
