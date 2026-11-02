"""Unit tests for Step 2 URL Validator and ArticleFetcher."""
import pytest
import httpx

from backend.step2_article_extraction.config import ExtractionConfig
from backend.step2_article_extraction.exceptions import (
    ArticleFetchConnectionError,
    ArticleFetchError,
    ArticleFetchHTTPError,
    ArticleFetchTimeoutError,
    EmptyWebpageError,
    InvalidURLError,
    SSRFSecurityError,
)
from backend.step2_article_extraction.fetchers.article_fetcher import ArticleFetcher
from backend.step2_article_extraction.fetchers.url_validator import URLValidator


# ============================================================================
# URL Validator & SSRF Security Tests
# ============================================================================

def test_url_validator_valid_urls():
    """Legitimate HTTP and HTTPS URLs pass validation."""
    validator = URLValidator()
    assert validator.validate_url("https://example.com/article/123") == "https://example.com/article/123"
    assert validator.validate_url("http://technews.org/story?id=45") == "http://technews.org/story?id=45"


@pytest.mark.parametrize(
    "invalid_url",
    [
        "",
        "   ",
        "ftp://example.com/file.txt",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "mailto:editor@news.com",
        "not-a-valid-url",
        "://missing-scheme.com",
    ],
)
def test_url_validator_invalid_schemes_and_formats(invalid_url):
    """Unsupported schemes and malformed URLs raise InvalidURLError."""
    validator = URLValidator()
    with pytest.raises(InvalidURLError):
        validator.validate_url(invalid_url)


@pytest.mark.parametrize(
    "forbidden_url",
    [
        "http://localhost/admin",
        "http://127.0.0.1/secrets",
        "http://127.0.0.1:8000/api",
        "http://10.0.0.5/internal",
        "http://192.168.1.1/router",
        "http://172.16.0.10/private",
        "http://169.254.169.254/latest/meta-data",
        "http://0.0.0.0:8080/",
        "http://[::1]/internal",
    ],
)
def test_url_validator_ssrf_rejections(forbidden_url):
    """Private and loopback IP addresses and hostnames raise SSRFSecurityError."""
    validator = URLValidator(allow_private_ips=False)
    with pytest.raises(SSRFSecurityError):
        validator.validate_url(forbidden_url)


# ============================================================================
# ArticleFetcher Network & HTTP Tests
# ============================================================================

@pytest.mark.asyncio
async def test_fetcher_success(monkeypatch, valid_article_html):
    """Successful GET request returns webpage HTML."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            text=valid_article_html,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(client=client)
        html = await fetcher.fetch_html("https://technews.example.com/articles/deepmind")
        assert "<article>" in html
        assert "DeepMind Unveils Next-Gen AI System" in html


@pytest.mark.asyncio
async def test_fetcher_timeout(monkeypatch):
    """Request timeout raises ArticleFetchTimeoutError."""
    async def mock_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout reading from socket")

    transport = httpx.MockTransport(mock_timeout)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(client=client)
        with pytest.raises(ArticleFetchTimeoutError) as exc_info:
            await fetcher.fetch_html("https://slow.example.com/article")
        assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_fetcher_connection_error():
    """Connection failure raises ArticleFetchConnectionError."""
    async def mock_conn_err(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused by peer")

    transport = httpx.MockTransport(mock_conn_err)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(client=client)
        with pytest.raises(ArticleFetchConnectionError) as exc_info:
            await fetcher.fetch_html("https://down.example.com/article")
        assert exc_info.value.status_code == 502


@pytest.mark.parametrize("status_code", [403, 404, 429, 500, 503])
@pytest.mark.asyncio
async def test_fetcher_http_status_errors(status_code):
    """HTTP 4xx and 5xx errors raise ArticleFetchHTTPError with appropriate status code."""
    async def mock_http_err(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status_code, text="Error page")

    transport = httpx.MockTransport(mock_http_err)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(client=client)
        with pytest.raises(ArticleFetchHTTPError) as exc_info:
            await fetcher.fetch_html("https://example.com/article")
        assert exc_info.value.status_code == status_code


@pytest.mark.asyncio
async def test_fetcher_empty_response():
    """Empty response body raises EmptyWebpageError."""
    async def mock_empty(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text="   ")

    transport = httpx.MockTransport(mock_empty)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(client=client)
        with pytest.raises(EmptyWebpageError):
            await fetcher.fetch_html("https://example.com/empty")


@pytest.mark.asyncio
async def test_fetcher_unsupported_content_type():
    """Binary or unsupported content types (e.g., PDF) raise ArticleFetchError."""
    async def mock_pdf(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"%PDF-1.4...",
            headers={"Content-Type": "application/pdf"},
        )

    transport = httpx.MockTransport(mock_pdf)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(client=client)
        with pytest.raises(ArticleFetchError) as exc_info:
            await fetcher.fetch_html("https://example.com/paper.pdf")
        assert "Unsupported content type" in exc_info.value.message


@pytest.mark.asyncio
async def test_fetcher_payload_exceeds_max_bytes():
    """Responses exceeding max_response_bytes raise ArticleFetchError."""
    custom_cfg = ExtractionConfig(EXTRACTION_MAX_RESPONSE_BYTES=100)
    async def mock_large(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text="A" * 500)

    transport = httpx.MockTransport(mock_large)
    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = ArticleFetcher(config=custom_cfg, client=client)
        with pytest.raises(ArticleFetchError) as exc_info:
            await fetcher.fetch_html("https://example.com/large")
        assert "exceeds limit" in exc_info.value.message
