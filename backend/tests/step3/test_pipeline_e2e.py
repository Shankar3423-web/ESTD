"""End-to-end integration test running Step 1 -> Step 2 -> Step 3 pipeline."""
from unittest.mock import AsyncMock, patch
import pytest

from backend.step1_source_collection.models.news_item import NewsItem
from backend.step2_article_extraction.models import (
    ExtractedArticle,
    ExtractionMethod,
    ExtractionStatus,
)
from backend.step2_article_extraction.services.extraction_service import (
    ExtractionService,
)
from backend.step3_content_cleaning.models import CleanedArticle, CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)


@pytest.mark.asyncio
async def test_full_pipeline_step1_to_step2_to_step3():
    """Verify complete end-to-end pipeline: Step 1 (NewsItem) -> Step 2 (ExtractedArticle) -> Step 3 (CleanedArticle)."""
    # 1. STEP 1: NewsItem from source collection
    step1_news_item = NewsItem(
        title="Researchers Develop High-Efficiency Solar Cell",
        description="A snippet about photovoltaic energy advances.",
        url="https://science.example.com/energy/perovskite-solar",
        source_name="Science Today",
        source_type="rss",
        author="Dr. Elena Rostova",
        published_at="2026-09-30T08:00:00Z",
        category="Science",
        image_url="https://science.example.com/img/solar.jpg",
        collected_at="2026-09-30T08:15:00Z",
    )

    mock_html = """
    <html>
      <head><title>Researchers Develop High-Efficiency Solar Cell</title></head>
      <body>
        <nav><a href="/">Home</a> > <a href="/science">Science</a></nav>
        <div class="cookie-banner">This site uses cookies. Accept cookies.</div>
        <article>
          <h1>Researchers Develop High-Efficiency Solar Cell</h1>
          <div class="ad-slot">Advertisement</div>
          <p>Materials scientists at the National Renewable Energy Laboratory have fabricated a tandem perovskite
          solar cell achieving a certified conversion efficiency exceeding thirty-four percent.</p>
          <div class="share-box">Share this story on Twitter</div>
          <p>The tandem architecture utilizes complementary absorption bands across the solar spectrum,
          minimizing thermalization losses in the infrared regime.</p>
          <p>Sign up for our newsletter to get updates delivered to your inbox.</p>
          <p>Commercial prototype modules are scheduled for field endurance testing throughout the coming year.</p>
        </article>
        <footer>All rights reserved. Copyright 2026 Science Today.</footer>
      </body>
    </html>
    """

    # 2. STEP 2: Extraction Service
    with patch(
        "backend.step2_article_extraction.fetchers.article_fetcher.ArticleFetcher.fetch_html",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = mock_html

        extraction_service = ExtractionService()
        extracted_article: ExtractedArticle = await extraction_service.extract_article(step1_news_item)

        assert extracted_article.extraction_status == ExtractionStatus.EXTRACTED
        assert extracted_article.content is not None
        assert len(extracted_article.content) > 100

    # 3. STEP 3: Content Cleaning & Normalization Service
    cleaning_service = ContentCleaningService()
    cleaned_article: CleanedArticle = cleaning_service.clean_article(extracted_article)

    # 4. STEP 3 Outcome Verification
    assert cleaned_article.cleaning_status == CleaningStatus.SUCCESS

    # Verify HTML stripped
    assert "<p>" not in cleaned_article.cleaned_content
    assert "</article>" not in cleaned_article.cleaned_content

    # Verify Boilerplate stripped
    assert "This site uses cookies" not in cleaned_article.cleaned_content
    assert "Advertisement" not in cleaned_article.cleaned_content
    assert "Share this story on Twitter" not in cleaned_article.cleaned_content
    assert "Sign up for our newsletter" not in cleaned_article.cleaned_content
    assert "All rights reserved" not in cleaned_article.cleaned_content

    # Verify Valid Article Content Survived Intact
    assert "Materials scientists at the National Renewable Energy Laboratory" in cleaned_article.cleaned_content
    assert "tandem architecture utilizes complementary absorption bands" in cleaned_article.cleaned_content
    assert "Commercial prototype modules are scheduled" in cleaned_article.cleaned_content

    # Verify Preserved Provenance Across All 3 Steps
    assert cleaned_article.title == step1_news_item.title
    assert cleaned_article.url == step1_news_item.url
    assert cleaned_article.category == "Developments"
    assert cleaned_article.source_type == "rss"
    assert cleaned_article.source_name == "Science Today"
    assert cleaned_article.author == "Dr. Elena Rostova"
    assert cleaned_article.published_at == "2026-09-30T08:00:00Z"
    assert cleaned_article.collected_at == step1_news_item.collected_at
    assert cleaned_article.canonical_url == extracted_article.canonical_url
    assert cleaned_article.extracted_at == extracted_article.extracted_at
    assert cleaned_article.extraction_status == "EXTRACTED"
    assert cleaned_article.cleaned_at is not None

    # Verify Original vs Cleaned Content
    assert cleaned_article.original_content == extracted_article.content
    assert cleaned_article.original_content_length == len(extracted_article.content)
    assert cleaned_article.cleaned_content_length == len(cleaned_article.cleaned_content)
    assert cleaned_article.content == cleaned_article.cleaned_content
    assert cleaned_article.original_content_length > cleaned_article.cleaned_content_length
