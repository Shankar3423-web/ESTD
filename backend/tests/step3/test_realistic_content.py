"""Realistic news content tests for Step 3 Content Cleaning & Normalization."""
import pytest

from backend.step2_article_extraction.models import (
    ExtractedArticle,
    ExtractionMethod,
    ExtractionStatus,
)
from backend.step3_content_cleaning.models import CleanedArticle, CleaningStatus
from backend.step3_content_cleaning.services.content_cleaning_service import (
    ContentCleaningService,
)


def test_realistic_multimedia_news_article_cleaning():
    """Test realistic article with headline, mixed HTML, banner ads, social sharing, newsletters, whitespace, and duplicated paragraph."""
    raw_realistic_content = """
    <div class="header-nav">Home > Technology > AI & Cloud</div>
    
    <h1>Next-Gen Semiconductor Fabrication Facility Breaks Ground in Dresden</h1>
    
    <div class="cookie-notice">We use cookies to improve your experience. Accept all cookies.</div>
    
    <div class="ad-slot">ADVERTISEMENT</div>
    
    <p>European technology consortium GlobalFoundries, in collaboration with leading regional research
    institutes, officially broke ground on a multi-billion euro wafer fabrication facility in Dresden today.</p>
    
    <p>The facility—designed to manufacture energy-efficient microcontrollers and automotive sensor
    logic—is slated to enter volume production by late 2028.</p>
    
    <div class="social-share">Share this article on Twitter | Share on LinkedIn</div>
    
    <p>The facility—designed to manufacture energy-efficient microcontrollers and automotive sensor
    logic—is slated to enter volume production by late 2028.</p>
    
    <p>“This investment marks a decisive milestone for European semiconductor sovereignty,” said
    Dr. Thomas Weber, chief executive of the industrial development board. “We are expanding capacity
    where demand from automotive and renewable sectors is expanding most aggressively.”</p>
    
    <div class="newsletter-box">
    Sign up for our free newsletter to get daily tech updates delivered to your inbox.
    </div>
    
    <p>Industry analysts at Gartner noted that the geographic diversification of foundry capacity
    helps mitigate acute vulnerability to maritime supply chain bottlenecks.</p>
    
    <div class="related-widget">Related stories: German auto sector welcomes silicon fab expansion</div>
    
    <footer>All rights reserved. Copyright 2026 TechGlobal Media Group.</footer>
    """

    article = ExtractedArticle(
        title="Next-Gen Semiconductor Fabrication Facility Breaks Ground in Dresden",
        description="GlobalFoundries and partners break ground on multi-billion wafer facility.",
        url="https://techglobal.example.com/semiconductors/dresden-fab",
        source_name="TechGlobal",
        source_type="gnews",
        author="Klaus Meyer",
        published_at="2026-09-30T11:00:00Z",
        category="Technology",
        image_url="https://techglobal.example.com/img/dresden.jpg",
        collected_at="2026-09-30T11:15:00Z",
        canonical_url="https://techglobal.example.com/semiconductors/dresden-fab",
        extraction_status=ExtractionStatus.EXTRACTED,
        extraction_method=ExtractionMethod.ARTICLE_WEB_EXTRACTION,
        extracted_at="2026-09-30T11:15:05Z",
        content=raw_realistic_content,
    )

    service = ContentCleaningService()
    cleaned: CleanedArticle = service.clean_article(article)

    # 1. Pipeline status
    assert cleaned.cleaning_status == CleaningStatus.SUCCESS

    # 2. Check noise removal
    assert "<div" not in cleaned.cleaned_content
    assert "</p>" not in cleaned.cleaned_content
    assert "Home > Technology > AI & Cloud" not in cleaned.cleaned_content
    assert "We use cookies" not in cleaned.cleaned_content
    assert "ADVERTISEMENT" not in cleaned.cleaned_content
    assert "Share this article on Twitter" not in cleaned.cleaned_content
    assert "Sign up for our free newsletter" not in cleaned.cleaned_content
    assert "Related stories:" not in cleaned.cleaned_content
    assert "All rights reserved" not in cleaned.cleaned_content

    # 3. Check article content survival and meaning
    assert "GlobalFoundries, in collaboration with leading regional research" in cleaned.cleaned_content
    assert "The facility-designed to manufacture energy-efficient microcontrollers" in cleaned.cleaned_content
    assert "This investment marks a decisive milestone for European semiconductor sovereignty" in cleaned.cleaned_content
    assert "Industry analysts at Gartner noted that the geographic diversification" in cleaned.cleaned_content

    # 4. Check repeated paragraph removal (should occur exactly once)
    repeated_phrase = "The facility-designed to manufacture energy-efficient microcontrollers"
    assert cleaned.cleaned_content.count(repeated_phrase) == 1

    # 5. Check metadata preserved
    assert cleaned.title == article.title
    assert cleaned.url == article.url
    assert cleaned.category == "Tech"
    assert cleaned.author == "Klaus Meyer"
    assert cleaned.published_at == "2026-09-30T11:00:00Z"
    assert cleaned.original_content_length > cleaned.cleaned_content_length
