"""Comprehensive Verification and Acceptance Tests for ESTD Business & Finance Category (Category ID 3).

Covers:
1. Taxonomy Verification (Top-level Category ID 3, 6 Canonical Subcategories IDs 32-37)
2. Source Registry (Business & Finance Feeds, Languages, Providers, Subcategory mappings)
3. Content Cleaning & Financial Number / Unicode Preservation (₹, $, %, crore, balance sheet, Telugu)
4. Step 4 Deduplication & Hash Protection
5. Step 5 PostgreSQL Knowledge Source Persistence & Integrity
6. Step 6 PostgreSQL MCP Read-Only Retrieval & SQL Safety
7. Step 7 Gemini AI News Synthesis Schema Validation & Fact Grounding
8. Step 8 Google Drive Folder Resolution & Document Staging Integrity
9. Protection of Frozen Entertainment, Sports, Tech, and Developments Categories (Zero Regression Guarantee)
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


class TestBusinessFinanceTaxonomy:
    """Phase 1 & 2: Verification of Canonical Business & Finance Taxonomy."""

    def test_canonical_business_finance_category_exists_in_db(self):
        with get_db_session() as session:
            cat = session.query(Category).filter(Category.id == 3).first()
            assert cat is not None, "Category ID 3 must exist in database"
            assert cat.name == "Business & Finance", "Category ID 3 name must be 'Business & Finance'"
            assert cat.code == "BIZ_FIN", "Category ID 3 code must be 'BIZ_FIN'"
            assert cat.slug == "business-finance", "Category ID 3 slug must be 'business-finance'"
            assert cat.is_active is True, "Category ID 3 must be active"

    def test_all_six_canonical_business_finance_subcategories_exist(self):
        expected_subcategories = {
            32: ("Financial Markets & Banking", "BIZ_MARKETS", "financial-markets-banking"),
            33: ("Startups & Venture Capital", "BIZ_STARTUPS", "startups-venture-capital"),
            34: ("Corporate Strategy & Earnings", "BIZ_CORP_STRATEGY", "corporate-strategy-earnings"),
            35: ("Personal Finance & Wealth Management", "BIZ_PERSONAL_FINANCE", "personal-finance-wealth"),
            36: ("Economy & Macroeconomics", "BIZ_MACROECONOMY", "economy-macroeconomics"),
            37: ("Trade, Supply Chain & Industry", "BIZ_TRADE_INDUSTRY", "trade-industry"),
        }

        with get_db_session() as session:
            subcats = session.query(Subcategory).filter(Subcategory.category_id == 3).all()
            assert len(subcats) == 6, f"Expected exactly 6 business & finance subcategories, found {len(subcats)}"
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
            ESTDSubcategory.FINANCIAL_MARKETS,
            ESTDSubcategory.STARTUPS_VENTURE_CAPITAL,
            ESTDSubcategory.CORPORATE_STRATEGY,
            ESTDSubcategory.PERSONAL_FINANCE_WEALTH,
            ESTDSubcategory.ECONOMY_MACROECONOMICS,
            ESTDSubcategory.TRADE_SUPPLY_CHAIN,
        ]:
            resolved = resolve_subcategory(sub_enum.value, parent_category=ESTDCategory.BUSINESS_FINANCE.value)
            assert resolved == sub_enum.value, f"Failed resolving {sub_enum.value}"


class TestBusinessFinanceSourceRegistry:
    """Phase 5: Source Registry Coverage Verification."""

    def test_registered_business_finance_sources_coverage(self):
        registry = get_source_registry()
        bf_sources = registry.get_sources_by_category("Business & Finance")
        assert len(bf_sources) >= 15, f"Expected at least 15 sources, found {len(bf_sources)}"

        source_ids = {s.source_id for s in bf_sources}
        assert "et_markets" in source_ids
        assert "bs_markets" in source_ids
        assert "livemint_markets" in source_ids
        assert "et_startups" in source_ids
        assert "inc42_startups" in source_ids
        assert "et_companies" in source_ids
        assert "bs_companies" in source_ids
        assert "et_wealth" in source_ids
        assert "bs_personal_finance" in source_ids
        assert "livemint_money" in source_ids
        assert "bs_economy" in source_ids
        assert "bbc_business" in source_ids
        assert "et_industry" in source_ids
        assert "bs_industry" in source_ids
        assert "the_hindu_business" in source_ids
        assert "indian_express_business" in source_ids
        assert "guardian_business" in source_ids
        assert "sakshi_business" in source_ids

    def test_business_finance_language_diversity(self):
        registry = get_source_registry()
        bf_sources = registry.get_sources_by_category("Business & Finance")
        languages = {s.language for s in bf_sources}
        assert "en" in languages, "English feeds must be present"
        assert "te" in languages, "Telugu regional feeds must be present"

    def test_business_finance_geographic_diversity(self):
        registry = get_source_registry()
        bf_sources = registry.get_sources_by_category("Business & Finance")
        regions = {s.region for s in bf_sources}
        assert "IN" in regions, "India national feeds must be present"
        assert "GB" in regions or "US" in regions, "International feeds must be present"

    def test_all_six_subcategories_covered_in_registry(self):
        registry = get_source_registry()
        bf_sources = registry.get_sources_by_category("Business & Finance")
        covered_subcats = {s.subcategory for s in bf_sources if s.subcategory}
        required_subcats = {
            "Financial Markets & Banking",
            "Startups & Venture Capital",
            "Corporate Strategy & Earnings",
            "Personal Finance & Wealth Management",
            "Economy & Macroeconomics",
            "Trade, Supply Chain & Industry",
        }
        missing = required_subcats - covered_subcats
        assert not missing, f"Missing subcategories in source registry: {missing}"


class TestBusinessFinanceCleaningAndIntegrity:
    """Phase 8: Content Cleaning & Financial Number Preservation."""

    def test_cleaning_preserves_financial_figures_and_symbols(self):
        cleaner = ContentCleaningService()
        raw_text = (
            "The Reserve Bank of India raised repo rates by 25 bps to 6.50% today. "
            "Company revenue grew 18.5% YoY to ₹1,450.50 crore ($175 million), with EBITDA margins expanding "
            "by 120 basis points. FY26 guidance projects net profit of ₹320.75 cr."
        )
        extracted = ExtractedArticle(
            id="test_fin_art",
            url="https://example.com/finance/earnings",
            title="Q2 Earnings Report",
            content=raw_text,
            category="Business & Finance",
            subcategory="Corporate Strategy & Earnings",
            source_name="Financial Express",
            source_type="rss",
            language="en",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )
        cleaned = cleaner.clean_article(extracted)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        # Verify preservation of symbols, units, percentages, decimals
        assert "₹1,450.50 crore" in cleaned.content
        assert "$175 million" in cleaned.content
        assert "18.5%" in cleaned.content
        assert "6.50%" in cleaned.content
        assert "EBITDA" in cleaned.content
        assert "FY26" in cleaned.content

    def test_cleaning_preserves_telugu_unicode_in_business(self):
        cleaner = ContentCleaningService()
        raw_text = "రూ.6.99 లక్షలకే కొత్త కారును విడుదల చేసిన ప్రముఖ ఆటోమొబైల్ సంస్థ. దేశీయ మార్కెట్లో అమ్మకాలు జోరుగా సాగుతున్నాయి."
        extracted = ExtractedArticle(
            id="test_te_biz",
            url="https://example.com/telugu/business",
            title="కొత్త కారు విడుదల",
            content=raw_text,
            category="Business & Finance",
            subcategory="Trade, Supply Chain & Industry",
            source_name="Sakshi",
            source_type="rss",
            language="te",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )
        cleaned = cleaner.clean_article(extracted)
        assert cleaned.cleaning_status == CleaningStatus.SUCCESS
        assert "రూ.6.99 లక్షలకే" in cleaned.content
        assert "మార్కెట్లో" in cleaned.content


class TestBusinessFinanceDeduplication:
    """Phase 9: Deduplication and Canonical Identification."""

    def test_exact_url_and_hash_deduplication(self):
        cleaner = ContentCleaningService()
        extracted = ExtractedArticle(
            id="test_dedup_1",
            url="https://example.com/finance/markets-surge?utm_source=twitter&ref=feed",
            title="Sensex Rallies 500 Points",
            content="Sensex rallied 500 points led by heavy buying in banking and IT shares on Wednesday.",
            category="Business & Finance",
            subcategory="Financial Markets & Banking",
            source_name="MarketSource",
            source_type="rss",
            language="en",
            collected_at=datetime.now(timezone.utc).isoformat(),
            extraction_status=ExtractionStatus.EXTRACTED,
            extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        )
        cleaned = cleaner.clean_article(extracted)

        config = DuplicateDetectionConfig(enable_historical_detection=False, persist_unique_articles=False)
        service = DuplicateDetectionService(config=config)

        # Batch check identical items: first is unique, second is duplicate
        results = service.check_batch([cleaned, cleaned])
        assert len(results) == 2
        assert results[0].status == "unique"
        assert results[1].status == "duplicate", "Second identical item must be detected as duplicate"
        assert results[1].decision.duplicate_reason == DuplicateReason.URL_MATCH


class TestBusinessFinanceKnowledgeSource:
    """Phase 10: PostgreSQL Knowledge Source Integrity."""

    def test_persisted_articles_reference_canonical_taxonomy(self):
        with get_db_session() as session:
            articles = session.query(NewsArticle).filter(NewsArticle.category_id == 3).all()
            assert len(articles) >= 2, "Must have at least historical articles in category ID 3"
            for a in articles:
                assert a.category_id == 3
                assert a.category == "Business & Finance"
                assert a.subcategory_id in (32, 33, 34, 35, 36, 37), f"Invalid subcategory_id {a.subcategory_id} for article {a.id}"
                assert a.content_hash is not None
                assert len(a.content_hash) == 64

    def test_historical_business_finance_articles_preserved(self):
        with get_db_session() as session:
            art3 = session.query(NewsArticle).filter(NewsArticle.id == 3).first()
            assert art3 is not None
            assert art3.category_id == 3
            assert art3.subcategory_id == 35

            art561 = session.query(NewsArticle).filter(NewsArticle.id == 561).first()
            assert art561 is not None
            assert art561.category_id == 3
            assert art561.subcategory_id == 37


class TestBusinessFinanceMCP:
    """Phase 11: MCP Read-Only Security & Scoped Retrieval."""

    def test_mcp_read_only_protection_against_mutations(self):
        mcp = MCPService()
        mutation_queries = [
            "INSERT INTO news_articles (title) VALUES ('Hacked')",
            "UPDATE news_articles SET title = 'Hacked'",
            "DELETE FROM news_articles WHERE id = 3",
            "DROP TABLE news_articles",
            "ALTER TABLE news_articles ADD COLUMN hacker TEXT",
            "TRUNCATE TABLE news_articles",
        ]
        for q in mutation_queries:
            with pytest.raises(Exception):
                mcp.query_knowledge_source(q)

    def test_mcp_scoped_retrieval_for_business_finance(self):
        mcp = MCPService()
        result = mcp.query_knowledge_source("SELECT id, title, category, subcategory FROM news_articles WHERE category_id = 3 LIMIT 5")
        assert isinstance(result, list)
        for row in result:
            assert row.get("category") == "Business & Finance"


class TestBusinessFinanceGeminiGeneration:
    """Phase 12: Gemini Content Generation Validation."""

    def test_generation_validator_accepts_valid_business_finance_news(self):
        valid_news = GeneratedNews(
            title="RBI Holds Repo Rate Steady at 6.5% Amid Stable Inflation Outlook",
            summary="The Reserve Bank of India decided to maintain the benchmark lending rate at 6.5%, citing steady macroeconomic indicators and stable food inflation.",
            content="The Monetary Policy Committee (MPC) of the Reserve Bank of India concluded its bi-monthly policy review today, voting unanimously to keep the repo rate unchanged at 6.50%.\n\nGovernor Shaktikanta Das stated that economic growth remains robust while inflation has shown signs of moderation across core sectors. Financial markets responded positively to the announcement, with banking stocks rallying on expectations of sustained liquidity in the credit system.",
            category=ESTDCategory.BUSINESS_FINANCE,
            subcategory="Economy & Macroeconomics",
            source_name="The Hindu - Business",
            source_url="https://www.thehindu.com/business/rbi-policy-rates",
        )
        # Should validate without error
        GenerationValidator.validate_generated_news(
            valid_news,
            expected_category="Business & Finance",
            expected_url="https://www.thehindu.com/business/rbi-policy-rates",
        )

    def test_generation_validator_rejects_category_mismatch(self):
        mismatched_news = GeneratedNews(
            title="RBI Holds Repo Rate Steady at 6.5% Amid Stable Inflation Outlook",
            summary="The Reserve Bank of India decided to maintain the benchmark lending rate at 6.5%.",
            content="The Monetary Policy Committee of the Reserve Bank of India concluded its review today.\n\nMarkets reacted with stability.",
            category=ESTDCategory.TECH,
            subcategory="Software & Cloud",
            source_name="The Hindu",
            source_url="https://example.com/rbi",
        )
        with pytest.raises(GenerationValidationError, match="Category mismatch"):
            GenerationValidator.validate_generated_news(
                mismatched_news,
                expected_category="Business & Finance",
            )


class TestBusinessFinanceGoogleDriveResolution:
    """Phase 13: Google Drive Folder Resolution & Document Staging."""

    def test_canonical_subcategory_folders_registered(self):
        assert "Business & Finance" in CANONICAL_SUBCATEGORY_FOLDERS
        bf_folders = CANONICAL_SUBCATEGORY_FOLDERS["Business & Finance"]
        assert len(bf_folders) == 6
        expected_subs = [
            "Financial Markets & Banking",
            "Startups & Venture Capital",
            "Corporate Strategy & Earnings",
            "Personal Finance & Wealth Management",
            "Economy & Macroeconomics",
            "Trade, Supply Chain & Industry",
        ]
        for sub in expected_subs:
            assert sub in bf_folders
            assert len(bf_folders[sub]) > 10, f"Invalid folder ID for {sub}"

    def test_folder_resolver_routes_subcategories_to_distinct_folders(self):
        resolver = DriveFolderResolver()
        folder_ids = set()
        for sub in [
            "Financial Markets & Banking",
            "Startups & Venture Capital",
            "Corporate Strategy & Earnings",
            "Personal Finance & Wealth Management",
            "Economy & Macroeconomics",
            "Trade, Supply Chain & Industry",
        ]:
            fid = resolver.resolve_subcategory_folder_id("Business & Finance", sub)
            assert fid is not None
            assert fid not in folder_ids, f"Duplicate folder ID {fid} for subcategory {sub}"
            folder_ids.add(fid)
        assert len(folder_ids) == 6


class TestRegressionIsolation:
    """Phase 15: Verification that Frozen Categories Remain 100% Intact."""

    def test_entertainment_sports_tech_developments_remain_untouched(self):
        with get_db_session() as session:
            # 1. Tech (ID 1)
            tech_count = session.query(NewsArticle).filter(NewsArticle.category_id == 1).count()
            assert tech_count == 10, f"Tech article count modified: expected 10, got {tech_count}"
            tech_subs = session.query(Subcategory).filter(Subcategory.category_id == 1).count()
            assert tech_subs == 7, f"Tech subcategories modified: expected 7, got {tech_subs}"

            # 2. Entertainment (ID 2)
            ent_count = session.query(NewsArticle).filter(NewsArticle.category_id == 2).count()
            assert ent_count == 16, f"Entertainment article count modified: expected 16, got {ent_count}"
            ent_subs = session.query(Subcategory).filter(Subcategory.category_id == 2).count()
            assert ent_subs == 8, f"Entertainment subcategories modified: expected 8, got {ent_subs}"

            # 3. Developments (ID 4)
            dev_count = session.query(NewsArticle).filter(NewsArticle.category_id == 4).count()
            assert dev_count == 14, f"Developments article count modified: expected 14, got {dev_count}"
            dev_subs = session.query(Subcategory).filter(Subcategory.category_id == 4).count()
            assert dev_subs == 7, f"Developments subcategories modified: expected 7, got {dev_subs}"

            # 4. Sports (ID 5)
            sports_count = session.query(NewsArticle).filter(NewsArticle.category_id == 5).count()
            assert sports_count == 30, f"Sports article count modified: expected 30, got {sports_count}"
            sports_subs = session.query(Subcategory).filter(Subcategory.category_id == 5).count()
            assert sports_subs == 9, f"Sports subcategories modified: expected 9, got {sports_subs}"
