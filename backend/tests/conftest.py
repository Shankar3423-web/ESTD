"""Pytest fixtures and mock data for ESTD tests."""
import pytest
from pydantic import SecretStr

from backend.common.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Return Settings configured with dummy test API keys."""
    return Settings(
        GNEWS_API_KEY="test_gnews_key_12345",
        NEWSDATA_API_KEY="test_newsdata_key_67890",
        HTTP_TIMEOUT_SECONDS=5.0,
        HTTP_MAX_RETRIES=0,  # Zero retries for fast test execution
    )


@pytest.fixture
def mock_empty_settings():
    """Return Settings with no API keys configured."""
    return Settings(
        GNEWS_API_KEY="",
        NEWSDATA_API_KEY="",
        HTTP_TIMEOUT_SECONDS=5.0,
        HTTP_MAX_RETRIES=0,
    )


@pytest.fixture
def sample_gnews_response():
    """Sample valid GNews API response."""
    return {
        "totalArticles": 2,
        "articles": [
            {
                "title": "Quantum Leap in Supercomputing",
                "description": "Researchers achieve quantum supremacy benchmark.",
                "content": "Full article content on quantum computing...",
                "url": "https://example.com/quantum-leap",
                "image": "https://example.com/images/quantum.jpg",
                "publishedAt": "2026-09-30T08:30:00Z",
                "source": {
                    "name": "Tech Times",
                    "url": "https://example.com",
                },
            },
            {
                "title": "Next-Gen Battery Tech Revealed",
                "description": "Solid-state batteries reach mass market prototype stage.",
                "content": "Solid state batteries will transform EVs...",
                "url": "https://example.com/battery-tech",
                "image": None,
                "publishedAt": "2026-09-30T07:15:00Z",
                "source": {
                    "name": "Science Daily",
                    "url": "https://example.com/science",
                },
            },
        ],
    }


@pytest.fixture
def sample_newsdata_response():
    """Sample valid NewsData.io API response."""
    return {
        "status": "success",
        "totalResults": 2,
        "results": [
            {
                "article_id": "newsdata_101",
                "title": "Breakthrough in Fusion Energy",
                "link": "https://example.com/fusion-energy",
                "keywords": ["energy", "fusion", "science"],
                "creator": ["Dr. Jane Doe", "Dr. Alan Smith"],
                "video_url": None,
                "description": "Net energy gain sustained for record duration.",
                "content": "Detailed report on tokamak fusion experiments...",
                "pubDate": "2026-09-30 06:45:00",
                "pubDateTZ": "UTC",
                "image_url": "https://example.com/images/fusion.png",
                "source_id": "nature_journal",
                "source_name": "Nature Journal",
                "source_url": "https://nature.com",
                "source_icon": "https://nature.com/favicon.ico",
                "language": "english",
                "country": ["united states"],
                "category": ["science"],
            },
            {
                "article_id": "newsdata_102",
                "title": "Autonomous Rovers Map Deep Oceanic Trenches",
                "link": "https://example.com/ocean-rovers",
                "keywords": ["ocean", "robotics"],
                "creator": None,
                "video_url": None,
                "description": "Unmanned submersibles discover new hydrothermal vents.",
                "content": "Exploration details...",
                "pubDate": "2026-09-29 22:10:00",
                "pubDateTZ": "UTC",
                "image_url": None,
                "source_id": "deepsea_news",
                "source_name": None,  # source_name missing, will fallback to source_id
                "source_url": "https://deepsea.org",
                "source_icon": None,
                "language": "english",
                "country": ["united kingdom"],
                "category": ["science"],
            },
        ],
        "nextPage": "1696000000",
    }


@pytest.fixture
def sample_rss_source():
    """Sample RSSSource object for tests."""
    from backend.step1_source_collection.rss.sources.models import RSSSource
    return RSSSource(
        source_id="test_tech_feed",
        source_name="Test Tech News",
        publisher="Test Media Corp",
        feed_url="https://example.com/feed.xml",
        category="Technology",
        enabled=True,
    )


@pytest.fixture
def sample_rss_xml():
    """Sample RSS 2.0 XML with multiple entries, author, media content, pubDate."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Test Tech News</title>
    <link>https://example.com</link>
    <description>Latest technology news</description>
    <item>
      <title>Autonomous Drones Deliver Medical Supplies</title>
      <link>https://example.com/articles/autonomous-drones</link>
      <description>Next-generation cargo drones complete clinical logistics test flight.</description>
      <dc:creator>Dr. Elena Rostova</dc:creator>
      <pubDate>Wed, 30 Sep 2026 09:00:00 GMT</pubDate>
      <media:content url="https://example.com/images/drone.jpg" medium="image" />
    </item>
    <item>
      <title>Neuromorphic Chip Emulates Synaptic Plasticity</title>
      <link>https://example.com/articles/neuromorphic-chip</link>
      <description>Researchers manufacture silicon device operating on nanowatt power budget.</description>
      <author>sarah.chen@example.com (Sarah Chen)</author>
      <pubDate>Tue, 29 Sep 2026 18:30:00 GMT</pubDate>
      <enclosure url="https://example.com/images/chip.png" type="image/png" length="12345" />
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def sample_atom_xml():
    """Sample Atom feed XML with entry links, updated timestamp, and author."""
    return """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Science Atom Feed</title>
  <link href="https://example.com/science-feed"/>
  <updated>2026-09-30T10:00:00Z</updated>
  <entry>
    <title>Gravitational Wave Observatory Detects Intermediate Black Hole Merger</title>
    <link rel="alternate" href="https://example.com/articles/gravitational-wave"/>
    <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
    <updated>2026-09-30T07:45:00Z</updated>
    <summary>Signal GW260930 reveals binary coalescence of 150 solar-mass black holes.</summary>
    <author>
      <name>Astrophysics Collaboration</name>
    </author>
  </entry>
</feed>
"""


@pytest.fixture
def sample_rss_duplicate_xml():
    """Sample RSS feed with duplicate URLs to test deduplication."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Duplicate Test Feed</title>
    <item>
      <title>Article Alpha First Copy</title>
      <link>https://example.com/article-alpha</link>
      <description>First copy of article alpha.</description>
      <pubDate>Wed, 30 Sep 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Article Alpha Duplicate Copy</title>
      <link>https://example.com/article-alpha</link>
      <description>Second copy with exact duplicate URL.</description>
      <pubDate>Wed, 30 Sep 2026 08:05:00 GMT</pubDate>
    </item>
    <item>
      <title>Article Beta Distinct</title>
      <link>https://example.com/article-beta</link>
      <description>Distinct article beta.</description>
      <pubDate>Wed, 30 Sep 2026 08:10:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

