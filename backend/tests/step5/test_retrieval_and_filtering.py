"""Tests verifying article querying, filtering by category/source/date, and pagination."""
import pytest

from backend.common.exceptions.custom_exceptions import InvalidCategoryError
from backend.step5_knowledge_source.schemas.article_schemas import ArticleCreateRequest
from backend.step5_knowledge_source.services.knowledge_service import KnowledgeSourceService


@pytest.fixture
def populated_knowledge_db(clean_knowledge_db):
    """Seed a known set of test articles across categories and sources."""
    service = KnowledgeSourceService()

    articles_data = [
        # Tech Articles
        {"title": "Test AI Model Alpha", "cat": "Tech", "source": "TechCrunch", "src_type": "gnews", "pub": "2026-10-01T08:00:00Z"},
        {"title": "Test AI Agent Beta", "cat": "Tech", "source": "VentureBeat", "src_type": "rss", "pub": "2026-10-02T09:00:00Z"},
        {"title": "Test Quantum Chip Roadmap", "cat": "Tech", "source": "Ars Technica", "src_type": "rss", "pub": "2026-10-03T10:00:00Z"},
        # Developments Articles
        {"title": "Test Exoplanet Atmosphere Study", "cat": "Developments", "source": "Nature Journal", "src_type": "rss", "pub": "2026-10-04T11:00:00Z"},
        {"title": "Test Gravitational Wave Signal", "cat": "Developments", "source": "Science Daily", "src_type": "newsdata", "pub": "2026-10-05T12:00:00Z"},
        # Business & Finance Articles
        {"title": "Test Tech Venture Funding Trends", "cat": "Business & Finance", "source": "Bloomberg", "src_type": "newsdata", "pub": "2026-10-06T13:00:00Z"},
        # Entertainment Articles
        {"title": "Test Film Festival Grand Prix", "cat": "Entertainment", "source": "EdTech Magazine", "src_type": "rss", "pub": "2026-10-07T14:00:00Z"},
    ]

    for idx, item in enumerate(articles_data):
        req = ArticleCreateRequest(
            title=item["title"],
            description=f"Description for {item['title']}",
            content=f"Full article text content for {item['title']} with adequate length and validation.",
            url=f"https://example.com/test-filter-{idx}",
            source_name=item["source"],
            source_type=item["src_type"],
            published_at=item["pub"],
            category=item["cat"],
        )
        service.create_article(req)

    return len(articles_data)


def test_filter_by_category_developments(populated_knowledge_db):
    """Verify category=Developments returns only Developments articles."""
    service = KnowledgeSourceService()
    items, pagination = service.list_articles(category="Developments")

    assert len(items) >= 2
    assert all(art.category == "Developments" for art in items)
    assert pagination.total_items >= 2


def test_filter_by_category_tech(populated_knowledge_db):
    """Verify category=Tech returns only Tech articles."""
    service = KnowledgeSourceService()
    items, pagination = service.list_articles(category="Tech")

    assert len(items) >= 3
    assert all(art.category == "Tech" for art in items)
    assert pagination.total_items >= 3


def test_invalid_category_filter_raises_error(populated_knowledge_db):
    """Verify filtering by an unsupported category like 'NonExistentCategory' raises InvalidCategoryError."""
    service = KnowledgeSourceService()
    with pytest.raises(InvalidCategoryError) as exc_info:
        service.list_articles(category="NonExistentCategory")

    assert exc_info.value.code == "INVALID_CATEGORY"


def test_filter_by_source_publisher(populated_knowledge_db):
    """Verify filtering by publisher name substring."""
    service = KnowledgeSourceService()
    items, pagination = service.list_articles(source="Nature")

    assert len(items) == 1
    assert "Nature Journal" in items[0].source_name


def test_filter_by_source_type(populated_knowledge_db):
    """Verify filtering by provider source_type."""
    service = KnowledgeSourceService()
    items, pagination = service.list_articles(source_type="newsdata")

    assert len(items) >= 2
    assert all(art.source_type == "newsdata" for art in items)


def test_filter_by_date_range(populated_knowledge_db):
    """Verify filtering by publication date range."""
    service = KnowledgeSourceService()
    items, pagination = service.list_articles(
        start_date="2026-10-04T00:00:00Z",
        end_date="2026-10-06T00:00:00Z",
    )

    # Should match Oct 4 and Oct 5 articles
    assert len(items) == 2
    titles = {art.title for art in items}
    assert "Test Exoplanet Atmosphere Study" in titles
    assert "Test Gravitational Wave Signal" in titles


def test_pagination_navigation(populated_knowledge_db):
    """Verify pagination correctly computes pages, offsets, and has_next/has_prev flags."""
    service = KnowledgeSourceService()

    # Total articles >= 7. Request page 1 with page_size 3
    p1_items, p1_meta = service.list_articles(page=1, page_size=3)
    assert len(p1_items) == 3
    assert p1_meta.page == 1
    assert p1_meta.page_size == 3
    assert p1_meta.total_items >= 7
    assert p1_meta.has_next is True
    assert p1_meta.has_prev is False

    # Request page 2 with page_size 3
    p2_items, p2_meta = service.list_articles(page=2, page_size=3)
    assert len(p2_items) == 3
    assert p2_meta.page == 2
    assert p2_meta.has_next is True
    assert p2_meta.has_prev is True

    # Request last page with page_size 3
    last_page = p1_meta.total_pages
    p_last_items, p_last_meta = service.list_articles(page=last_page, page_size=3)
    assert len(p_last_items) >= 1
    assert p_last_meta.page == last_page
    assert p_last_meta.has_next is False
    assert p_last_meta.has_prev is True
